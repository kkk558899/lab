from pathlib import Path
from typing import Any
try:
    import chromadb
    from chromadb.api.models.Collection import Collection
    from chromadb.utils import embedding_functions
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False
    Collection = Any

import os
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from app.config import BASE_DIR

_local_hf_cache = BASE_DIR / "data" / "hf_cache"
if _local_hf_cache.exists():
    os.environ["HF_HOME"] = str(_local_hf_cache)
    os.environ["HF_HUB_OFFLINE"] = "1"

KB_DIR = BASE_DIR / "data" / "kb"
CHROMA_DIR = BASE_DIR / "data" / "chroma"

_collection = None
_embedding_fn = None

def get_embedding_fn():
    global _embedding_fn
    if _embedding_fn is None:
        _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="BAAI/bge-small-zh-v1.5"
        )
    return _embedding_fn

def get_collcetion():
    """向量库的初始化"""
    if not HAS_CHROMADB:
        return None
    global _collection
    if _collection is not None:
        return _collection

    KB_DIR.mkdir(parents=True, exist_ok=True)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    col = client.get_or_create_collection(
        name="lab_kb", embedding_function=get_embedding_fn()
    )

    if col.count() == 0:
        ids = []
        docs = []
        metas = []
        for path in sorted(KB_DIR.glob("*.md")):
            text = path.read_text(encoding="UTF-8").strip()
            if not text:
                continue
            docs.append(text)
            ids.append(path.stem)
            metas.append({"source": path.name})

        if docs:
            col.add(ids=ids, documents=docs, metadatas=metas)

    _collection = col
    return col

def _keyword_search(query: str) -> str:
    """无向量库时的轻量级本地文档关键词检索（不依赖 PyTorch/ChromaDB）"""
    if not KB_DIR.exists():
        return ""
    q = query.lower()
    results = []
    for path in sorted(KB_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            continue
        score = 0
        stem = path.stem.lower()
        for ch in q:
            if ch.strip() and (ch in text.lower() or ch in stem):
                score += 1
        for kw in ["安全", "规范", "时间", "开放", "预约", "规则", "设备", "借用"]:
            if kw in q and (kw in text or kw in stem):
                score += 10
        if score > 0:
            results.append((score, f"[{path.name}]\n{text}"))
    results.sort(key=lambda x: x[0], reverse=True)
    if not results:
        # 兜底返回前两份规范摘要
        for path in sorted(KB_DIR.glob("*.md"))[:2]:
            text = path.read_text(encoding="utf-8").strip()
            if text:
                results.append((1, f"[{path.name}]\n{text}"))
    return "\n\n".join([r[1] for r in results[:2]])

def warmup():
    """启动时预热：如果启用了向量库则预热，否则跳过"""
    if not HAS_CHROMADB:
        return
    try:
        col = get_collcetion()
        if col is not None and col.count() > 0:
            col.query(query_texts=["预热"], n_results=1)
    except Exception as e:
        print(f"向量库预热跳过或失败: {e}")

def search(query: str) -> str:
    """根据关键字去检索知识库（优先向量库，无向量库时自动回退至轻量检索）"""
    if not HAS_CHROMADB:
        return _keyword_search(query)
    try:
        col = get_collcetion()
        if col is None or col.count() == 0:
            return _keyword_search(query)

        limit = min(5, col.count())
        res = col.query(query_texts=[query], n_results=limit)
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        distances = (res.get("distances") or [[]])[0]

        score_parts = []
        for doc, meta, dist in zip(docs, metas, distances):
            score = 1 / (1 + dist)
            if score < 0.5:
                continue
            name = meta.get("source") or ""
            score_parts.append({"score": score, "content": f"[{name}]\n{doc}"})

        score_parts.sort(key=lambda x: x["score"], reverse=True)
        final_parts = [item["content"] for item in score_parts[:2]]
        return "\n\n".join(final_parts) or _keyword_search(query)
    except Exception:
        return _keyword_search(query)
