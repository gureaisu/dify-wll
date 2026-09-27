# 王立宁老师风格 AI 关怀助手（MVP）

## 结构
- `persona/wang_lining.md` — 角色设定（老师理念、说话风格、界线）。**【待补充】部分需用授权资料填写并请老师审阅**
- `data/` — 老师的授权资料（文章、课程逐字稿、问答），自动检索
- `safety.py` — 危机关键词检测与求助热线
- `retrieval.py` — 简易中文检索
- `bot.py` — 命令行聊天程序（Claude Opus 5）

## 运行
    pip install -r requirements.txt
    set ANTHROPIC_API_KEY=你的密钥        (PowerShell: $env:ANTHROPIC_API_KEY="...")
    python bot.py

## 上线前清单
- [ ] 取得王立宁老师书面授权（肖像、姓名、内容使用范围）
- [ ] 补全 persona，放入足量授权资料
- [ ] 准备 30–50 个测试情境，请老师评分“像不像我会说的话”
- [ ] 请心理专业人士审核危机处理流程与热线
- [ ] 隐私：用户同意书、对话加密、数据保存期限
- [ ] 若在中国大陆面向公众上线：生成式 AI 服务需按规定办理备案/算法备案
