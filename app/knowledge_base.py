"""Base de conocimiento con RAG vectorial local.

Usa embeddings locales por hashing y similitud coseno. Esto deja evidencia
concreta de recuperación por vectores, superando la búsqueda por palabras exactas.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List
from .semantic_index import embed, cosine

from .config import DATA_DIR, settings

STOPWORDS = {
    'de', 'la', 'el', 'en', 'y', 'a', 'los', 'las', 'un', 'una', 'que',
    'con', 'del', 'por', 'para', 'se', 'al', 'es', 'su', 'son', 'como',
    'más', 'pero', 'sus', 'le', 'ya', 'o', 'fue', 'este', 'ha', 'lo',
    'si', 'sobre', 'ser', 'tiene', 'nos', 'uno', 'puede', 'todo',
}

@dataclass
class DocumentChunk:
    source: str
    title: str
    content: str
    score: float = 0.0


def _tokenize(text: str) -> List[str]:
    text = text.lower()
    text = re.sub(r'[^a-záéíóúñü0-9\s]', ' ', text)
    return [w for w in text.split() if len(w) > 2 and w not in STOPWORDS]


def load_documents() -> List[DocumentChunk]:
    chunks: List[DocumentChunk] = []
    for path in sorted(DATA_DIR.glob('*.md')) + sorted(DATA_DIR.glob('*.txt')):
        raw = path.read_text(encoding='utf-8')
        sections = re.split(r'\n(?=## )', raw)
        for index, section in enumerate(sections):
            title_match = re.search(r'^#+\s*(.+)$', section.strip(), flags=re.MULTILINE)
            title = title_match.group(1).strip() if title_match else f'Sección {index + 1}'
            body = section.strip()
            if len(body) > 40:
                chunks.append(DocumentChunk(source=path.name, title=title, content=body))
    return chunks


def retrieve(query: str, top_k: int | None = None) -> List[DocumentChunk]:
    """
    Recuperación semántica usando TF-IDF + similitud coseno.
    Retorna los top_k chunks más relevantes para la consulta.
    """
    top_k = top_k or settings.top_k
    query_vec = embed(query)

    docs = load_documents()
    ranked: List[DocumentChunk] = []

    for doc in docs:
        doc_vec = embed(doc.title + " " + doc.content)
        score = round(cosine(query_vec, doc_vec), 4)
        if score > 0:
            ranked.append(DocumentChunk(doc.source, doc.title, doc.content, score))

    ranked.sort(key=lambda c: c.score, reverse=True)
    return ranked[:top_k]
