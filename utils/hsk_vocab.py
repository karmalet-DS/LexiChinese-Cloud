"""
HSK 급수별 어휘 로더 — drkameleon/complete-hsk-vocabulary 기반
"""
import json
import os
import random

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_cache: dict[int, list[dict]] = {}


def load_vocab(level: int) -> list[dict]:
    """HSK 급수(3~6)에 해당하는 누적 어휘 목록 반환. 캐시됨."""
    if level in _cache:
        return _cache[level]
    path = os.path.join(_DATA_DIR, f"hsk{level}_vocab.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    _cache[level] = data
    return data


def sample_vocab_text(level: int, n: int = 40) -> str:
    """HSK 급수에서 랜덤 어휘 n개를 '단어(pinyin)' 형태의 텍스트로 반환."""
    vocab = load_vocab(level)
    samples = random.sample(vocab, min(n, len(vocab)))
    return ", ".join(
        f"{w['word']}({w['pinyin']})" if w.get("pinyin") else w["word"]
        for w in samples
    )


def vocab_count(level: int) -> int:
    """해당 급수의 총 어휘 수."""
    return len(load_vocab(level))
