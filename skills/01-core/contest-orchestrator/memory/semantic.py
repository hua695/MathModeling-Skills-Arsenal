#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
memory/semantic.py — Semantic Retrieval Layer（语义检索层）

纯标准库、零第三方依赖：字符 n-gram TF-IDF + 余弦相似度（中文免分词、免 jieba），
并提供可选的 embedding 升级通道（本地 sentence-transformers 或 OpenAI 兼容 API）。

三层检索（Tier 结构，retrieval.py 集成）：
  tier0  字符指纹匹配    retrieval.py 现有 fingerprint_match_score —— 始终可用
  tier1  字符 n-gram TF-IDF（本模块） —— 始终可用，离线确定性，零依赖
  tier2  embedding 向量（可选）      —— 检测到模型/API 才启用，向量缓存到 memory/.cache/

为什么用字符 n-gram TF-IDF（而不是分词）：
  - 中文免分词：n=2,3 字符片段对同义改写/换序天然鲁棒（"预测"↔"时序外推"共享大量片段）
  - 纯标准库：与 ranking.py 的"纯 Python 无第三方依赖"哲学一致，任何机器都能跑
  - IDF 压制高频通用词（模型/问题/分析），突出题型判别词

用法：
    from memory.semantic import SemanticIndex
    idx = SemanticIndex(entries)      # entries: [dict]，字段即文本；自动提取 _id
    idx.build()                        # 构建 TF-IDF 索引（可选 build(embedding=True) 启用 tier2）
    hits = idx.query("预测 时序 小样本")  # [(sim, entry_index), ...] 降序
"""
import math
import os
import re
import time

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(SKILL, 'memory', '.cache')

# ---- 字段权重：题型/场景类字段对相似度贡献更高（problem_type 是判别主键）----
FIELD_WEIGHT = {
    'problem_type': 3.0,
    'scenario': 2.5,
    'context': 2.5,
    'context_type': 2.0,
    'section': 2.0,
    'situation': 1.5,
    'method': 1.5,
    'attempt': 1.2,
    'strategy': 1.2,
    'reason': 1.0,
    'lesson': 1.0,
    'signal': 1.0,
    'source': 1.0,
}

# 不参与相似度的键（id 与内部标签）
_SKIP_KEYS = {'_kind', '_text', '_id', '_sim'}
_ID_KEYS = {'failure_id', 'success_id', 'strategy_id', 'decision_id', 'wr_id', 'id'}

# ASCII 停用词（极小集合，只滤掉无信息量虚词）
_STOP_WORDS = {
    'the', 'and', 'for', 'with', 'from', 'this', 'that', 'are', 'was',
    'were', 'have', 'has', 'had', 'not', 'but', 'its', 'their', 'them',
    'will', 'can', 'could', 'should', 'would', 'into', 'about', 'than',
}

_ASCII_RE = re.compile(r'[A-Za-z][A-Za-z0-9_+\-]*')
_CJK_RE = re.compile(r'[\u4e00-\u9fff]+')


def _tokens(text, weight=1.0):
    """把一段文本打成 {token: 加权计数}。
    ASCII 词（≥2 字符、转小写）+ CJK 连续串的 bigram/trigram。"""
    out = {}

    def add(tok, w):
        out[tok] = out.get(tok, 0.0) + w

    for m in _ASCII_RE.findall(text):
        t = m.lower()
        if len(t) >= 2 and t not in _STOP_WORDS:
            add(t, weight)
    for run in _CJK_RE.findall(text):
        if len(run) < 2:
            continue
        for n in (2, 3):
            for i in range(len(run) - n + 1):
                add(run[i:i + n], weight)
    return out


def entry_id(e):
    """条目 id：优先 *_id 字段，其次 _id，最后 '?'。"""
    for k in ('failure_id', 'success_id', 'strategy_id', 'decision_id', 'wr_id', 'id'):
        v = e.get(k)
        if v:
            return str(v)
    return e.get('_id') or '?'


def entry_text(e):
    """把条目字段拼成加权文本对列表 [(text, weight), ...]。id/内部标签不入文本。"""
    parts = []
    for k, v in e.items():
        if k in _SKIP_KEYS or k in _ID_KEYS:
            continue
        if v is None:
            continue
        s = str(v).strip()
        if not s or s == 'None':
            continue
        parts.append((s, FIELD_WEIGHT.get(k, 1.0)))
    return parts


def entry_plain(e):
    """条目的纯文本（embedding 通道用）：所有字段拼接。"""
    return ' '.join(t for t, _ in entry_text(e))


class SemanticIndex:
    """字符 n-gram TF-IDF 索引（tier1）。docs 与输入 entries 严格同序。"""

    def __init__(self, entries):
        self.entries = list(entries)
        self.docs = []          # [{id, vec:{token: 归一化 tfidf}}]
        self.idf = {}
        self.embeddings = None  # tier2：list[vec]（启用时）
        self.built = False
        self.build_ms = 0

    def build(self, embedding=False):
        t0 = time.time()
        raw = []
        for e in self.entries:
            vec = {}
            for text, w in entry_text(e):
                for tok, c in _tokens(text, w).items():
                    vec[tok] = vec.get(tok, 0.0) + c
            raw.append(vec)
        n = len(raw)
        df = {}
        for vec in raw:
            for tok in vec:
                df[tok] = df.get(tok, 0) + 1
        # 平滑 IDF：ln((N+1)/(df+1)) + 1，避免低频词爆炸
        self.idf = {t: math.log((n + 1) / (d + 1)) + 1.0 for t, d in df.items()}
        self.docs = []
        for e, vec in zip(self.entries, raw):
            v = {t: c * self.idf.get(t, 1.0) for t, c in vec.items()}
            norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
            self.docs.append({'id': entry_id(e), 'vec': {t: x / norm for t, x in v.items()}})
        if embedding:
            self._maybe_embed()
        self.build_ms = int((time.time() - t0) * 1000)
        self.built = True
        return self

    def query(self, text, top_k=20, min_sim=0.0):
        """查询文本 → [(sim, entry_index), ...] 降序。
        top_k=0 返回全部（召回扩展用）；min_sim 过滤低分。"""
        q = _tokens(text, 1.0)
        if not q:
            return []
        qvec = {t: c * self.idf.get(t, 0.0) for t, c in q.items()}
        qn = math.sqrt(sum(x * x for x in qvec.values())) or 1.0
        out = []
        for i, d in enumerate(self.docs):
            small, big = (qvec, d['vec']) if len(qvec) <= len(d['vec']) else (d['vec'], qvec)
            dot = 0.0
            for t, x in small.items():
                y = big.get(t)
                if y:
                    dot += x * y
            sim = dot / qn
            if sim >= min_sim:
                out.append((sim, i))
        out.sort(key=lambda x: x[0], reverse=True)
        return out[:top_k] if top_k else out

    # ---- tier2：可选 embedding 通道（不装模型/不配 API 时静默降级）----

    def _maybe_embed(self):
        provider = _embedding_provider()
        if provider is None:
            return
        cache = os.path.join(CACHE_DIR, 'embeddings.json')
        texts = [entry_plain(e) for e in self.entries]
        vecs = _load_emb_cache(cache, len(texts))
        if vecs is None:
            vecs = provider(texts)
            _save_emb_cache(cache, vecs)
        self.embeddings = vecs

    def query_embedding(self, text, top_k=20, min_sim=0.0):
        """tier2：embedding 余弦（未启用时返回空）。"""
        if self.embeddings is None:
            return []
        provider = _embedding_provider()
        if provider is None:
            return []
        qv = provider([text])[0]
        out = []
        for i, v in enumerate(self.embeddings):
            dot = sum(a * b for a, b in zip(qv, v))
            sim = max(0.0, min(1.0, dot))  # 归一化向量内积即余弦
            if sim >= min_sim:
                out.append((sim, i))
        out.sort(key=lambda x: x[0], reverse=True)
        return out[:top_k] if top_k else out


def _embedding_provider():
    """返回 encode(texts)->list[vec] 的可调用对象；不可用返回 None。
    优先级：本地 sentence-transformers（小多语言模型）→ OpenAI 兼容 API（env 配置）。"""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        return lambda texts: [v.tolist() for v in model.encode(texts, normalize_embeddings=True)]
    except Exception:
        pass
    url = os.environ.get('EMBEDDING_API_URL')
    key = os.environ.get('EMBEDDING_API_KEY')
    if url and key:
        import json
        import urllib.request
        model = os.environ.get('EMBEDDING_MODEL', 'text-embedding-3-small')

        def api(texts):
            body = json.dumps({'model': model, 'input': texts}).encode('utf-8')
            req = urllib.request.Request(url, data=body, headers={
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + key,
            })
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read().decode('utf-8'))
            return [d['embedding'] for d in data['data']]
        return api
    return None


def _load_emb_cache(path, n):
    if not os.path.exists(path):
        return None
    try:
        import json
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        if data.get('n') == n and isinstance(data.get('vecs'), list):
            return data['vecs']
    except Exception:
        pass
    return None


def _save_emb_cache(path, vecs):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        import json
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'n': len(vecs), 'vecs': vecs}, f)
    except Exception:
        pass


if __name__ == '__main__':
    # 自测：语义检索能命中"同义改写"条目（bigram 字符匹配会漏的场景）
    demo = [
        {'_id': 'FD-T1', 'problem_type': '预测', 'method': 'LSTM', 'signal': '时序数据 非平稳'},
        {'_id': 'SD-T2', 'problem_type': '预测', 'method': 'ARIMA', 'signal': '小样本 时间序列'},
        {'_id': 'ST-T3', 'problem_type': '组合优化', 'scenario': '几何布图 装箱', 'strategy': '确定性构造'},
        {'_id': 'DM-T4', 'problem_type': '评价分类', 'context': '层次分析法 AHP 权重'},
    ]
    idx = SemanticIndex(demo).build()
    print('build_ms:', idx.build_ms, '| vocab:', len(idx.idf))
    for q in ['时序外推 样本少', '装箱 排布 优化', '权重 打分 评价']:
        hits = idx.query(q, top_k=2)
        print(f'查询[{q}] →', [(demo[i]['_id'], round(s, 3)) for s, i in hits])
