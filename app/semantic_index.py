"""Índice vectorial simple para RAG con embeddings locales por hashing.

No reemplaza un modelo de embeddings comercial, pero sí transforma textos y consultas
en vectores numéricos y calcula similitud coseno, evitando la búsqueda textual plana.
"""
from __future__ import annotations
import hashlib
import math
import re
from typing import Dict, Iterable, List

DIM = 384

STOP = {"de","la","el","en","y","a","los","las","un","una","que","con","del","por","para","se","al","es","su","son","como"}


def tokenize(text: str) -> List[str]:
    text = re.sub(r"[^a-záéíóúñü0-9 ]", " ", text.lower())
    return [t for t in text.split() if len(t) > 2 and t not in STOP]


def embed(text: str, dim: int = DIM) -> List[float]:
    vec = [0.0] * dim
    for tok in tokenize(text):
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if (h >> 1) % 2 == 0 else -1.0
        vec[idx] += sign
    norm = math.sqrt(sum(v*v for v in vec)) or 1.0
    return [v / norm for v in vec]


def cosine(a: Iterable[float], b: Iterable[float]) -> float:
    return sum(x*y for x, y in zip(a, b))
