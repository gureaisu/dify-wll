# 影片轉逐字稿 → Dify 知識庫

流程：下載影片音訊 → 切成 10 分鐘一段 → OpenAI 語音轉文字 → GPT 整理成知識庫條目

## 安裝（只需一次）
    pip install -r requirements.txt

ffmpeg 已由 `imageio-ffmpeg` 內建，不需要另外安裝。

## 使用（PowerShell）
    $env:OPENAI_API_KEY="sk-..."

    # 單支影片
    python transcribe.py "https://www.youtube.com/watch?v=xxxx"

    # 整個頻道，先試最新 5 支
    python transcribe.py "https://www.youtube.com/channel/UCMI7XQkssNpl_KgKjgIZTiA/videos" --limit 5

    # 多個網址：寫進 urls.txt，每行一個
    python transcribe.py urls.txt

    # 抖音（通常需要登入的 cookies；先關掉 Chrome 再執行）
    python transcribe.py "https://www.douyin.com/video/xxxx" --cookies-from-browser chrome

    # 自己已下載的影片／錄音（檔案或整個資料夾）
    python transcribe.py D:\videos\

    # 只要逐字稿，不整理
    python transcribe.py urls.txt --no-kb

## 輸出
- `output/transcripts/*.txt`：原始逐字稿
- `output/kb/*.md`：整理好的知識庫，**上傳到 Dify 的同一個知識庫**（分段標識符 `\n\n`）

已處理過的影片會自動跳過；中途中斷，重新執行同一個指令即可接著跑。

## 模型與費用
- 轉寫：預設 `gpt-4o-transcribe`，可改 `--asr-model whisper-1`
- 整理：預設 `gpt-4o-mini`，可改 `--chat-model <模型名稱>`
- 也可以用環境變數 `ASR_MODEL`、`CHAT_MODEL` 設定
- 語音轉寫按音訊分鐘數計費，建議先用 `--limit 5` 試跑，確認品質和費用

## 建議
- 整理後的條目請人工抽查，特別是錯字和案例去識別化
- 優先處理長影片、直播回放（內容最豐富），短影片多半是片段
- 下載的內容只作為內部知識庫使用
