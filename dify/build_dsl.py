"""把 system_prompt.md / opening.md / moderation_keywords.txt 打包成 Dify 可匯入的 DSL（YAML）。
執行：python build_dsl.py  → 產生 暖心家庭教育助手.yml
"""
import re
import sys
from pathlib import Path

import yaml

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).parent

# 提示詞：聊天助手（simple 模式）會自動把知識庫內容附在後面，所以拿掉 {{#context#}} 佔位符
prompt = (ROOT / "system_prompt.md").read_text(encoding="utf-8")
prompt = prompt.replace("{{#context#}}\n", "").replace("下面是知识库中检索到的相关内容。", "系统会在下方附上知识库中检索到的相关内容。")

opening_md = (ROOT / "opening.md").read_text(encoding="utf-8")
sections = re.split(r"^# .*$", opening_md, flags=re.M)
opening = sections[1].strip()
questions = [l[2:].strip() for l in sections[2].splitlines() if l.startswith("- ")]

keywords = "\n".join(
    l.strip() for l in (ROOT / "moderation_keywords.txt").read_text(encoding="utf-8").splitlines() if l.strip()
)
crisis_reply = (
    "听到你这样说，我很担心你。你现在安全吗？\n"
    "如果你有伤害自己的念头，请马上拨打全国心理援助热线 12356，或希望24热线 400-161-9995；"
    "紧急情况请拨打 110 或 120。\n"
    "也请告诉身边一位你信任的人，你不需要一个人扛着。"
)

dsl = {
    "version": "0.7.0",
    "kind": "app",
    "app": {
        "name": "暖心家庭教育助手",
        "mode": "chat",
        "icon_type": "emoji",
        "icon": "🌱",
        "icon_background": "#E4FBCC",
        "description": "参考资深家庭教育导师理念设计的 AI 陪伴助手：亲子沟通、学习动力、青春期、情绪与婚姻家庭关系。",
        "use_icon_as_answer_icon": False,
    },
    "model_config": {
        "prompt_type": "simple",
        "pre_prompt": prompt,
        "chat_prompt_config": {},
        "completion_prompt_config": {},
        "model": {
            "provider": "langgenius/openai/openai",
            "name": "gpt-4o",
            "mode": "chat",
            "completion_params": {
                "temperature": 0.7,
                "top_p": 1,
                "presence_penalty": 0,
                "frequency_penalty": 0,
                "max_tokens": 1024,
            },
        },
        "opening_statement": opening,
        "suggested_questions": questions,
        "suggested_questions_after_answer": {"enabled": True},
        "speech_to_text": {"enabled": False},
        "text_to_speech": {"enabled": False, "language": "", "voice": ""},
        "retriever_resource": {"enabled": True},
        "annotation_reply": {"enabled": False},
        "more_like_this": {"enabled": False},
        "sensitive_word_avoidance": {
            "enabled": True,
            "type": "keywords",
            "config": {
                "keywords": keywords,
                "inputs_config": {"enabled": True, "preset_response": crisis_reply},
                "outputs_config": {"enabled": False, "preset_response": ""},
            },
        },
        "external_data_tools": [],
        "user_input_form": [],
        "dataset_query_variable": "",
        "dataset_configs": {
            "retrieval_model": "multiple",
            "top_k": 4,
            "reranking_enable": False,
            "datasets": {"datasets": []},  # 匯入後請在「上下文」手動加入知識庫
        },
        "agent_mode": {"enabled": False, "max_iteration": 5, "strategy": "function_call", "tools": []},
        "file_upload": {
            "enabled": False,
            "image": {
                "enabled": False,
                "detail": "high",
                "number_limits": 3,
                "transfer_methods": ["remote_url", "local_file"],
            },
            "allowed_file_types": [],
            "allowed_file_extensions": [],
            "allowed_file_upload_methods": ["remote_url", "local_file"],
            "number_limits": 3,
        },
    },
}

out = ROOT / "暖心家庭教育助手.yml"
out.write_text(yaml.safe_dump(dsl, allow_unicode=True, sort_keys=False, width=1000), encoding="utf-8")
back = yaml.safe_load(out.read_text(encoding="utf-8"))
assert back["model_config"]["pre_prompt"] == prompt and back["model_config"]["suggested_questions"] == questions
print(f"OK → {out.name}  提示词 {len(prompt)} 字，开场问题 {len(questions)} 个，关键词 {keywords.count(chr(10))+1} 个")
