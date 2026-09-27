"""影片 → 逐字稿 → Dify 知识库文件。

用法：
  python transcribe.py <网址或本地文件> [...]          # 下载 + 转写 + 整理成知识库
  python transcribe.py urls.txt                         # 文本文件里每行一个网址
  python transcribe.py <频道/播放列表网址> --limit 20   # 批量处理最新 20 个
  python transcribe.py <抖音网址> --cookies-from-browser chrome
  python transcribe.py ... --no-kb                      # 只要逐字稿，不整理

输出（在 output/ 下）：
  audio/        压缩后的音频片段
  transcripts/  原始逐字稿（.txt）
  kb/           整理好的知识库文件（.md），直接上传到 Dify
已处理过的视频会自动跳过，中断后重新执行即可接着跑。
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import yt_dlp
from openai import OpenAI

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent
OUT = ROOT / "output"
AUDIO_DIR, TEXT_DIR, KB_DIR = OUT / "audio", OUT / "transcripts", OUT / "kb"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

SEGMENT_SECONDS = 600  # 每段 10 分钟，远低于 OpenAI 转写接口 25MB 的上限
MEDIA_EXTS = {".mp4", ".mkv", ".mov", ".avi", ".flv", ".webm", ".mp3", ".m4a", ".wav", ".aac", ".ogg"}

TRANSCRIBE_PROMPT = "以下是一位家庭教育老师讲解亲子关系、孩子教育、夫妻关系和情绪管理的内容，使用简体中文，带标点符号。"

KB_PROMPT = """你是知识库整理员。下面是一位家庭教育老师的视频逐字稿（语音识别结果，可能有错字）。
请把其中有价值的教育观点、方法和案例整理成知识库条目，规则：
1. 每条格式固定为两行：第一行“【主题】标题”，第二行是内容（一个自然段，150~400字）。条目之间空一行，条目内部不要空行。
   主题从这些里选：核心理念、亲子沟通、有效陪伴、学习动力、青春期、手机问题、情绪管理、原生家庭、婚姻关系、家庭关系、规则、自立、自我成长。
2. 保留老师的口吻、口头禅、比喻和标志性说法，让读者能感受到她说话的味道；修正明显的识别错字，删掉语气词、重复和口误。
3. 案例去除可识别信息（真实姓名、学校、城市），用“有一位妈妈”“一个初二的男孩”等代替。
4. 删除广告、卖课、引导关注/点赞/进直播间等内容，以及寒暄闲聊。
5. 不要添加逐字稿里没有的观点。如果整段都没有有价值的内容，只输出：无
只输出条目本身，不要任何说明。

视频标题：{title}

逐字稿：
{text}"""


def safe_name(name: str) -> str:
    name = re.sub(r'[\\/:*?"<>|\r\n\t]', "_", name).strip(" .")
    return name[:80] or "untitled"


def is_done(title: str, args) -> bool:
    name = safe_name(title)
    if args.no_kb:
        return (TEXT_DIR / f"{name}.txt").exists()
    return (KB_DIR / f"{name}.md").exists()


# ---------- 1. 取得音频 ----------

def download(url: str, args) -> list[tuple[str, Path]]:
    """下载网址中的所有视频音频，返回 [(标题, 音频文件)]。"""
    opts = {
        "format": "bestaudio/best",
        "outtmpl": str(AUDIO_DIR / "raw" / "%(id)s.%(ext)s"),
        "ffmpeg_location": FFMPEG,
        "ignoreerrors": True,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "extract_flat": "in_playlist",  # 先只列出频道里的视频，逐个再下载
    }
    if args.limit:
        opts["playlistend"] = args.limit
    if args.cookies_from_browser:
        opts["cookiesfrombrowser"] = (args.cookies_from_browser,)

    results = []
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if info is None:
            print(f"  ✗ 无法解析：{url}")
            return results
        entries = [e for e in (info.get("entries") or [info]) if e]
        for entry in entries:
            page = entry.get("webpage_url") or entry.get("url") or url
            if entry.get("ie_key") == "YoutubeTab" or entry.get("_type") == "playlist":
                results += download(page, args)  # 频道首页会先列出“视频/Shorts”等分页
                continue
            title = entry.get("title") or entry.get("id")
            if is_done(title, args):
                print(f"  - 已处理过，跳过：{title}")
                continue
            print(f"  ↓ 下载：{title}")
            got = ydl.extract_info(page, download=True)
            if got is None:
                print(f"  ✗ 下载失败：{title}")
                continue
            got = (got.get("entries") or [got])[0]
            results.append((got.get("title") or title, Path(ydl.prepare_filename(got))))
    return results


def split_audio(src: Path, name: str) -> list[Path]:
    """转为 16kHz 单声道 mp3，并切成 10 分钟一段。"""
    seg_dir = AUDIO_DIR / name
    seg_dir.mkdir(parents=True, exist_ok=True)
    for old in seg_dir.glob("*.mp3"):
        old.unlink()
    subprocess.run(
        [FFMPEG, "-loglevel", "error", "-y", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000",
         "-b:a", "48k", "-f", "segment", "-segment_time", str(SEGMENT_SECONDS),
         str(seg_dir / "part%03d.mp3")],
        check=True,
    )
    return sorted(seg_dir.glob("part*.mp3"))


# ---------- 2. 转写 ----------

def transcribe(client: OpenAI, parts: list[Path], model: str) -> str:
    texts = []
    for i, part in enumerate(parts, 1):
        print(f"  ✎ 转写 {i}/{len(parts)}")
        with part.open("rb") as f:
            r = client.audio.transcriptions.create(
                model=model, file=f, language="zh", prompt=TRANSCRIBE_PROMPT,
            )
        texts.append(r.text.strip())
    return "\n".join(texts)


# ---------- 3. 整理成知识库 ----------

def to_kb(client: OpenAI, title: str, text: str, model: str) -> str:
    size = 6000
    chunks = [text[i : i + size] for i in range(0, len(text), size)]
    entries = []
    for i, chunk in enumerate(chunks, 1):
        print(f"  ✦ 整理 {i}/{len(chunks)}")
        r = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": KB_PROMPT.format(title=title, text=chunk)}],
        )
        out = (r.choices[0].message.content or "").strip()
        if out and out != "无":
            entries.append(out)
    return "\n\n".join(entries)


# ---------- 主流程 ----------

def collect_inputs(items: list[str]) -> list[str]:
    inputs = []
    for item in items:
        p = Path(item)
        if p.suffix.lower() == ".txt" and p.exists():
            inputs += [l.strip() for l in p.read_text(encoding="utf-8").splitlines()
                       if l.strip() and not l.lstrip().startswith("#")]
        elif p.is_dir():
            inputs += [str(f) for f in sorted(p.iterdir()) if f.suffix.lower() in MEDIA_EXTS]
        else:
            inputs.append(item)
    return inputs


def process(client: OpenAI, title: str, audio: Path, args):
    name = safe_name(title)
    txt_path = TEXT_DIR / f"{name}.txt"
    if txt_path.exists():
        text = txt_path.read_text(encoding="utf-8")
    else:
        parts = split_audio(audio, name)
        text = transcribe(client, parts, args.asr_model)
        txt_path.write_text(text, encoding="utf-8")
        print(f"  ✓ 逐字稿：transcripts/{name}.txt（{len(text)} 字）")
    if args.no_kb:
        return
    kb = to_kb(client, title, text, args.chat_model)
    if kb:
        (KB_DIR / f"{name}.md").write_text(kb + "\n", encoding="utf-8")
        print(f"  ✓ 知识库：kb/{name}.md（{kb.count('【')} 条）")
    else:
        print("  - 没有可整理的内容")


def main():
    ap = argparse.ArgumentParser(description="影片转逐字稿，并整理成 Dify 知识库")
    ap.add_argument("inputs", nargs="+", help="网址、本地音视频文件、文件夹，或每行一个网址的 .txt")
    ap.add_argument("--limit", type=int, help="频道/播放列表最多处理几个视频")
    ap.add_argument("--cookies-from-browser", help="从浏览器读取登录 cookies（抖音常需要），如 chrome、edge")
    ap.add_argument("--no-kb", action="store_true", help="只产生逐字稿，不整理成知识库")
    ap.add_argument("--asr-model", default=os.getenv("ASR_MODEL", "gpt-4o-transcribe"),
                    help="OpenAI 转写模型（也可用 whisper-1）")
    ap.add_argument("--chat-model", default=os.getenv("CHAT_MODEL", "gpt-4o-mini"),
                    help="用于整理知识库的 OpenAI 模型")
    ap.add_argument("--download-only", action="store_true", help="只下载并切分音频（测试用，不需要 API Key）")
    args = ap.parse_args()

    for d in (AUDIO_DIR, TEXT_DIR, KB_DIR):
        d.mkdir(parents=True, exist_ok=True)
    if not args.download_only and not os.getenv("OPENAI_API_KEY"):
        sys.exit("请先设置环境变量 OPENAI_API_KEY")
    client = None if args.download_only else OpenAI()

    for item in collect_inputs(args.inputs):
        print(f"\n▶ {item}")
        try:
            if Path(item).exists():
                jobs = [(Path(item).stem, Path(item))]
            else:
                jobs = download(item, args)
            for title, audio in jobs:
                print(f"  ● {title}")
                if args.download_only:
                    parts = split_audio(audio, safe_name(title))
                    print(f"  ✓ 切成 {len(parts)} 段：audio/{safe_name(title)}/")
                    continue
                process(client, title, audio, args)
        except Exception as e:  # 单个失败不影响其他
            print(f"  ✗ 出错：{e}")

    print(f"\n完成。知识库文件在：{KB_DIR}")


if __name__ == "__main__":
    main()
