from openai import OpenAI


from .chat_memory import ChatMemory


class Model:
    def __init__(
        self: "Model", key: str, model_name: str = "chatgpt-4o-latest",
        max_attempts: int = 6
    ) -> None:
        self.first_time = True
        self.model_name = model_name
        self.memory = ChatMemory()
        self.client = OpenAI(api_key=key)
        self.max_attempts = max_attempts

    def init_conv(
        self: "Model", city: str, place: str, description: str, user_id: int
    ) -> str:
        system_content = (
            "Ты играешь в игру 'Городской Акинатор'. Пользователь должен угадать загаданное место в городе, задавая тебе вопросы. "
            "Ты должен отвечать 'да', 'нет' или давать подсказки, если пользователь не может угадать долго. "
            "Не раскрывай сразу загаданное место, жди пока пользователь его угадает или спросит напрямую. "
            f"Загаданное место: {place}, находится оно в городе {city}. Вот его описание: {description} "
            "Нужно чтобы пользователь полностью отгадал название и местоположение достопремичательности"
        )
        if self.first_time:
            system_content += "Поздоровайся с пользователем, объясни ему правила игры."

        messages = [
            {"role": "system", "content": [{"type": "text", "text": system_content}]}
        ]
        self.memory.append(user_id, "system", messages[0]["content"][0]["text"])

        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.7,
            max_tokens=300,
        )

        answer = completion.choices[0].message.content.strip()
        self.memory.append(user_id, "assistant", answer)
        return answer

    def bid_farewell(self: "Model", user_id: int) -> str:
        farewell_prompt = (
            "Поблагодари пользователя за хорошую игру"
            "Расскажи пользователю о месте, которое было загадано"
            "Постарайся не быть слишком длинным и подробным, но и чтобы основные сведения были рассказаны"
            "Не прощайся с пользователем"
        )
        self.memory.append(user_id, "system", farewell_prompt)
        messages = self.memory.get(user_id)

        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.7,
            max_tokens=300,
        )

        reply = completion.choices[0].message.content.strip()
        self.memory.append(user_id, "assistant", reply)
        return reply

    def get_hint_from_description(self, description: str, user_id: str) -> str:
        prompt = (
            "Ты ведущий текстовой игры по городским достопримечательностям. "
            "На основе описания места, придумай короткую, немного загадочную, но полезную подсказку, "
            "которая поможет игроку догадаться, что это за место.\n\n"
            f"Описание: {description}\n\n"
            "Подсказка:"
        )
        return self.ask(user_id, prompt)

    def ask(self: "Model", user_id: int, user_input: str) -> str:
        self.memory.append(user_id, "user", user_input)
        messages = self.memory.get(user_id)

        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.7,
            max_tokens=300,
        )

        reply = completion.choices[0].message.content.strip()
        self.memory.append(user_id, "assistant", reply)
        self.memory.attempts_count += 1
        return reply

    def reset(self: "Model", user_id: int) -> None:
        self.first_time = False
        reply = self.bid_farewell(user_id)
        self.memory.clear(user_id)
        return reply
