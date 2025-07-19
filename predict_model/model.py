from openai import OpenAI

ACTIONS = [
    "GUESS",     
    "GIVE_UP",   
    "ASK_HINT",  
    "RESET",     
    "OTHER",     
]

SYSTEM_PROMPT = (
    "Ты классификатор намерений для текстовой игры «Городской Акинатор». "
    f"Ответь ОДНИМ словом, выбери из: {', '.join(ACTIONS)}. "
    "Никаких других слов, знаков препинания или форматирования."
)


class Predictor:
    """Возвращает строку‑код действия без JSON."""

    def __init__(self, key: str, model_name: str = "gpt-4o-mini"):
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
