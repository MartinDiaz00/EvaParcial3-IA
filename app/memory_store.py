from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from .config import MEMORY_FILE

class MemoryStore:
    '''Memoria simple de corto y largo plazo para demostrar continuidad conversacional.'''

    def __init__(self, file_path: Path = MEMORY_FILE):
        self.file_path = file_path
        self.file_path.parent.mkdir(exist_ok=True)
        if not self.file_path.exists():
            self._save({'short_term': [], 'long_term': {}})

    def _load(self) -> Dict:
        return json.loads(self.file_path.read_text(encoding='utf-8'))

    def _save(self, data: Dict) -> None:
        self.file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    def add_interaction(self, role: str, content: str) -> None:
        data = self._load()
        data['short_term'].append({
            'timestamp': datetime.now().isoformat(timespec='seconds'),
            'role': role,
            'content': content
        })
        data['short_term'] = data['short_term'][-12:]
        self._save(data)

    def remember_fact(self, key: str, value: str) -> None:
        data = self._load()
        data['long_term'][key] = {
            'value': value,
            'updated_at': datetime.now().isoformat(timespec='seconds')
        }
        self._save(data)

    def short_context(self) -> str:
        data = self._load()
        if not data['short_term']:
            return 'Sin historial conversacional previo.'
        return '\n'.join([f"{item['role']}: {item['content']}" for item in data['short_term'][-6:]])

    def long_context(self) -> str:
        data = self._load()
        if not data['long_term']:
            return 'Sin datos persistentes registrados.'
        return '\n'.join([f'{key}: {value["value"]}' for key, value in data['long_term'].items()])

    def clear(self) -> None:
        self._save({'short_term': [], 'long_term': {}})
