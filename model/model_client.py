from openai import OpenAI


from .chat_memory import ChatMemory


class Model:
    def __init__(self, key, model_name: str = "chatgpt-4o-latest") -> None:
        self.model_name = model_name
        self.memory = ChatMemory()
        self.client = OpenAI(api_key=key) 

    def ask(self, user_id: str, user_input: str) -> str:
        self.memory.append(user_id, "user", user_input)

        messages = [{"role": "system", "content": (
            "Ты играешь в игру 'Городской Акинатор'. Пользователь должен угадать загаданное место в городе, задавая тебе вопросы. "
            "Ты должен отвечать 'да', 'нет' или давать подсказки, если пользователь не может угадать долго."
            "Не раскрывай сразу загаданное место, жди пока пользователь его угадает или спросит напрямую."
        )}]
        messages += self.memory.get(user_id)

        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.7,
            max_tokens=300,
        )

        reply = completion.choices[0].message.content.strip()
        self.memory.append(user_id, "assistant", reply)
        return reply

    def reset(self, user_id: str) -> None:
        self.memory.clear(user_id)
