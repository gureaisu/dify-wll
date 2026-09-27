"""王立宁老师风格 AI 关怀助手 —— 命令行版。

运行：python bot.py
"""

import sys
from pathlib import Path

import anthropic

from retrieval import Retriever
from safety import HOTLINE_MESSAGE, detect_crisis

# Windows 繁体中文终端默认 cp950，无法显示简体字
sys.stdout.reconfigure(encoding="utf-8")
sys.stdin.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent
MODEL = "claude-opus-5"

PERSONA = (ROOT / "persona" / "wang_lining.md").read_text(encoding="utf-8")
CRISIS_NOTE = (
    "【系统提示】用户本条消息可能包含危机信号。请把用户的安全放在第一位："
    "温和地确认对方现在是否安全，鼓励拨打 12356 或 400-161-9995，紧急时拨打 110/120，"
    "并联系身边信任的人。不要说教，不要讲大道理，保持陪伴的语气。"
)

client = anthropic.Anthropic()
retriever = Retriever(ROOT / "data")


def build_system() -> str:
    # 系统提示保持不变，便于提示缓存；检索到的资料放在用户消息里
    return PERSONA


def build_user_content(user_msg: str, crisis: bool) -> str:
    parts = []
    refs = retriever.search(user_msg)
    if refs:
        parts.append(
            "<参考资料>\n以下是王立宁老师授权资料中与问题相关的内容，可以借鉴其理念和表达，"
            "但不要逐字照搬，也不要编造资料里没有的“老师原话”。\n\n"
            + "\n\n".join(f"[{src}]\n{para}" for src, para in refs)
            + "\n</参考资料>"
        )
    if crisis:
        parts.append(CRISIS_NOTE)
    parts.append(f"<用户消息>\n{user_msg}\n</用户消息>")
    return "\n\n".join(parts)


def reply(history: list[dict], user_msg: str) -> str:
    crisis = detect_crisis(user_msg)
    if crisis:
        print("\n" + HOTLINE_MESSAGE)

    messages = history + [
        {"role": "user", "content": build_user_content(user_msg, crisis)}
    ]
    print("\n老师助手：", end="", flush=True)
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=16000,
        system=build_system(),
        messages=messages,
        output_config={"effort": "medium"},
        # 被安全分类器拒答时，由服务器自动改用推荐的备用模型
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
        final = stream.get_final_message()
    print()

    if final.stop_reason == "refusal":
        answer = "抱歉，这个问题我暂时没办法回答。如果你正经历困难，可以拨打全国心理援助热线 12356。"
        print(answer)
    else:
        answer = "".join(b.text for b in final.content if b.type == "text")

    # 历史里只保存原始用户消息和回复文本，不保存检索资料，避免上下文膨胀
    history.append({"role": "user", "content": user_msg})
    history.append({"role": "assistant", "content": answer})
    return answer


def main():
    print("=" * 50)
    print("您好，我是参考王立宁老师教育理念设计的 AI 关怀助手（不是老师本人）。")
    print("亲子、夫妻、情绪压力……想聊什么都可以。输入 q 退出。")
    print("=" * 50)
    history: list[dict] = []
    while True:
        try:
            user_msg = input("\n你：").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if user_msg.lower() in ("q", "quit", "exit"):
            break
        if not user_msg:
            continue
        try:
            reply(history, user_msg)
        except anthropic.RateLimitError:
            print("\n（请求太频繁了，请稍等一会儿再试）")
        except anthropic.APIConnectionError:
            print("\n（网络连接失败，请检查网络）")
        except anthropic.APIStatusError as e:
            print(f"\n（服务出错：{e.status_code}）")
    print("\n照顾好自己，随时欢迎回来聊聊。")


if __name__ == "__main__":
    main()
