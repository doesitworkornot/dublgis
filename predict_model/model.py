from openai import OpenAI
from model.chat_memory import ChatMemory

ACTIONS = [
    "RESET",     
    "CORRECT",
    "OTHER",     
]

SYSTEM_PROMPT = (
    "Ты — строгий классификатор намерений для текстовой игры «Городской Акинатор».\n"
    "Верни ОДНО слово (БЕЗ кавычек и знаков препинания) в ВЕРХНЕМ регистре,\n"
    f"выбрав из: {', '.join(ACTIONS)}.\n"
    "Описание действий:\n"
    "RESET — просит начать заново;\n"
    "CORRECT — пользователь должен отгадать место ПОЛНОСТЬЮ, указав точное название;\n"
    "OTHER — всё, что не подходит выше.\n\n"
)

class Predictor:
    def __init__(self, key: str, model_name: str = "gpt-4.1-mini") -> None:
        self.client = OpenAI(api_key=key)
        self.model_name = model_name
        self.memory = ChatMemory()

    def _ensure_system_prompt(self, user_id: int) -> None:
        if not self.memory.get(user_id): 
            self.memory.append(user_id, "system", SYSTEM_PROMPT)

    def predict(self, user_id: int, text: str) -> str:
        self._ensure_system_prompt(user_id)

        self.memory.append(user_id, "user", text.strip())

        messages = self.memory.get(user_id)
        resp = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0,
            max_tokens=10,
        )

        code = resp.choices[0].message.content.strip().upper()
        code = code if code in ACTIONS else "OTHER"

        self.memory.append(user_id, "assistant", code)
        return code
    

    def remember_assistant(self, user_id: int, text: str) -> None:
        self._ensure_system_prompt(user_id)
        self.memory.append(user_id, "assistant", text)

    def reset(self, user_id: int) -> None:
        self.memory.clear(user_id)
