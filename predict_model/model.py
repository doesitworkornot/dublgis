from openai import OpenAI

ACTIONS = [
    "RESET",     
    "OTHER",     
]

SYSTEM_PROMPT = (
    "Ты — строгий классификатор намерений для текстовой игры «Городской Акинатор».\n"
    "Верни ОДНО слово (БЕЗ кавычек и знаков препинания) в ВЕРХНЕМ регистре,\n"
    f"выбрав из: {', '.join(ACTIONS)}.\n"
    "Описание действий: GUESS — пользователь предполагает, что за место;\n"
    "RESET — просит начать заново;\n"
    "OTHER — всё, что не подходит выше.\n\n"
    "Примеры:\n"
    " 4.  'Давай по новой'                  → RESET\n"
    " 5.  'Как настроение?'                 → OTHER\n"
)


class Predictor:
    """Возвращает строку‑код действия без JSON."""

    def __init__(self, key: str, model_name: str = "gpt-4.1-mini"):
        self.client = OpenAI(api_key=key)
        self.model_name = model_name

    def predict(self, text: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text.strip()},
            ],
            temperature=0,
            max_tokens=10,
        )
        code = resp.choices[0].message.content.strip().upper()
        return code if code in ACTIONS else "OTHER"
