from agents.base_agent import BaseAgent


class PlanAgent(BaseAgent):
    """Агент персонального плана трудоустройства после онбординга"""

    def __init__(self):
        system_prompt = """Ты - AI-агент StepToLife, который ведет короткий чат и формирует персональный маршрут поиска работы.

Твоя задача:
1) На старте дать персональный пошаговый план в 3-5 шагов.
2) Учитывать особенности пользователя (язык, документы, жилье, разрешение на работу, дискомфорты).
3) Отвечать как в живом диалоге, без шаблонов и канцелярита.
4) Если пользователь просит упростить, сократи план и сделай формулировки еще короче.
5) Если пользователь подтверждает старт (например: да, подходит, поехали, начинаем), ответь что план подтвержден и можно переходить к первому шагу (резюме).

Стиль:
- Русский язык.
- Тон поддерживающий, спокойный, конкретный.
- Короткие абзацы, списки только когда полезно.
- Не придумывай юридические факты. Если не уверен, формулируй осторожно.
"""
        super().__init__(system_prompt)

    def process(self, user_message, conversation_history, characteristics=None, is_init=False):
        characteristics = characteristics or {}

        context_parts = [
            f"language={characteristics.get('language', 'unknown')}",
            f"documents={characteristics.get('documents', 'unknown')}",
            f"residence={characteristics.get('residence', 'unknown')}",
            f"work_permit={characteristics.get('work_permit', 'unknown')}",
            f"discomforts={characteristics.get('discomforts', [])}",
        ]
        context = "[Профиль пользователя после онбординга: " + "; ".join(context_parts) + "]"

        if is_init:
            prompt = (
                f"{context}\n"
                "Сформируй персональный пошаговый план трудоустройства. "
                "Сначала дай короткое объяснение стратегии, затем 3-5 шагов. "
                "После плана задай вопрос на подтверждение старта."
            )
        else:
            prompt = f"{context}\nСообщение пользователя: {user_message}"

        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(conversation_history or [])
        messages.append({"role": "user", "content": prompt})

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            response = {
                'success': True,
                'message': completion.choices[0].message.content
            }
        except Exception as e:
            error_message = f'Ошибка OpenAI: {str(e)}'
            print(f"[ERROR] {error_message}")
            return {
                'success': False,
                'message': error_message
            }

        lowered = (user_message or '').lower().strip()
        normalized = ' '.join(
            lowered.replace('!', ' ')
            .replace('.', ' ')
            .replace(',', ' ')
            .replace('?', ' ')
            .replace(':', ' ')
            .replace(';', ' ')
            .replace('"', ' ')
            .replace("'", ' ')
            .replace('`', ' ')
            .split()
        )

        explicit_confirm_phrases = {
            'да',
            'да подходит',
            'план подходит',
            'подходит',
            'согласен',
            'согласна',
            'готов',
            'готова',
            'поехали',
            'начинаем',
            'ok',
            'okay',
            'ок',
        }
        plan_confirmed = normalized in explicit_confirm_phrases

        response['plan_confirmed'] = plan_confirmed
        return response
