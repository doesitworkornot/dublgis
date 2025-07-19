from openai import OpenAI
from model.chat_memory import ChatMemory


ACTIONS = [
    "GUESS",  # пользователь предполагает, что за место (но НЕ назвал точно)
    "RESET",  # просит начать заново
    "CORRECT",  # назвал место полностью и точно
    "OTHER",  # всё остальное
]

SYSTEM_PROMPT = (
    "Ты — строгий классификатор намерений для текстовой игры «Городской Акинатор».\n"
    "Всегда смотри только на ПОСЛЕДНЕЕ сообщение пользователя и верни ровно ОДНО слово БЕЗ кавычек, знаков препинания и пробелов — в ВЕРХНЕМ регистре, выбрав из: "
    f"{', '.join(ACTIONS)}.\n\n"
    "Определения: \n"
    "• CORRECT — пользователь НАПИСАЛ полное и точное название загаданного места (например: ‘Эйфелева башня, Париж’). Слова вроде ‘угадал’, ‘я знаю ответ’, ‘я догадался’ НЕ являются CORRECT.\n"
    "• GUESS   — пользователь выдвигает версию или задаёт уточняющий вопрос о месте, НО ещё не назвал его полностью (например: ‘Это башня?’, ‘Это музей науки?’).\n"
    "• RESET   — пользователь явно просит начать игру заново (‘давай по новой’, ‘сброс’).\n"
    "• OTHER   — всё остальное (приветствия, благодарности, эмоции, ‘я угадал!’ и пр.).\n\n"
    "Примеры классификации:\n"
    "П: ‘Это Эйфелева башня, Париж?’ → CORRECT\n"
    "П: ‘Эйфелева башня’           → CORRECT\n"
    "П: ‘Это башня?’               → GUESS\n"
    "П: ‘Я угадал!’                → OTHER\n"
    "П: ‘Сбрось, хочу сначала’     → RESET\n"
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
