from typing import List, Dict


class ChatMemory:
    def __init__(self):
        self.history: Dict[str, List[Dict[str, str]]] = {}
        self.attempts_count = 0

    def get(self, user_id: str) -> List[Dict[str, str]]:
        return self.history.get(user_id, [])

    def append(self, user_id: str, role: str, content: str):
        if user_id not in self.history:
            self.history[user_id] = []
        self.history[user_id].append({"role": role, "content": content})

    def clear(self, user_id: str):
        self.history[user_id] = []
        self.attempts_count = 0
