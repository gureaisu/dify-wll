# dify-wll — 暖心家庭教育助手

參考家庭教育導師王立寧老師的理念，用 Dify + OpenAI 建立的 AI 關懷對話助手。

| 目錄 | 內容 |
|---|---|
| `dify/` | Dify 匯入設定檔（`暖心家庭教育助手.yml`）、提示詞、設定步驟 |
| `transcriber/` | 影片 → 逐字稿 → 知識庫條目的工具（yt-dlp + OpenAI） |
| `web/` | 對外聊天網頁（nginx + 單頁 HTML，`http://<IP>:8080`），代理 Dify API 並限流 |
| `care_bot/` | 早期用 Claude API 寫的命令行版本，僅供參考 |
| `aiwll/` | Obsidian 筆記庫：`知识库/`（上傳到 Dify 的 9 個知識庫檔案）、`部署记录/`（Dify 建置、部署、移除紀錄） |

## 快速開始
1. 依 `dify/Dify設定步驟.md` 接上 OpenAI、上傳 `aiwll/知识库/` 建知識庫
2. 工作室 → 匯入 DSL → `dify/暖心家庭教育助手.yml`
3. 在應用的「上下文」加入知識庫，確認模型，發佈

修改提示詞後執行 `python dify/build_dsl.py` 重新產生設定檔。
