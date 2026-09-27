"""极简检索：用中文双字切分 + 词频打分，从 data/ 中找出最相关的段落。

资料量大了以后，可换成向量数据库（Chroma、pgvector 等）。
"""

import math
from collections import Counter
from pathlib import Path


def _bigrams(text: str) -> list[str]:
    chars = [c for c in text if not c.isspace()]
    return ["".join(chars[i : i + 2]) for i in range(len(chars) - 1)]


class Retriever:
    def __init__(self, data_dir: Path):
        self.chunks: list[tuple[str, str]] = []  # (来源文件, 段落)
        for path in sorted(data_dir.glob("*")):
            if path.suffix not in (".md", ".txt") or path.name == "README.md":
                continue
            text = path.read_text(encoding="utf-8")
            for para in text.split("\n\n"):
                para = para.strip()
                if len(para) >= 20:
                    self.chunks.append((path.stem, para))
        self.grams = [Counter(_bigrams(p)) for _, p in self.chunks]
        df = Counter(g for grams in self.grams for g in grams)
        n = len(self.chunks) or 1
        self.idf = {g: math.log(1 + n / c) for g, c in df.items()}

    def search(self, query: str, k: int = 4) -> list[tuple[str, str]]:
        q = set(_bigrams(query))
        scored = []
        for (src, para), grams in zip(self.chunks, self.grams):
            score = sum(self.idf.get(g, 0) for g in q if g in grams)
            if score > 0:
                scored.append((score, src, para))
        scored.sort(reverse=True)
        return [(src, para) for _, src, para in scored[:k]]
