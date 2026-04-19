from agents.base_agent import BaseAgent


class PlanAgent(BaseAgent):
    """Personal employment plan agent after onboarding"""

    def __init__(self):
        system_prompt = """You are the StepToLife AI agent that runs a short chat and creates a personalized job-search route.

    Your task:
    1) At the start, provide a personalized 3-5 step plan.
    2) Consider user specifics (language, documents, housing, work permit, discomforts).
    3) Reply like a real dialog, without bureaucracy.
    4) If the user asks to simplify, make the plan shorter and clearer.
    5) If the user confirms start (for example: yes, works, let us start), reply that the plan is confirmed and the first step (resume) can begin.

    Style:
    - English language.
    - Supportive, calm, concrete tone.
    - Short paragraphs; use lists only when useful.
    - Do not invent legal facts. If uncertain, be careful and explicit.
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
        context = "[User profile after onboarding: " + "; ".join(context_parts) + "]"

        if is_init:
            prompt = (
                f"{context}\n"
                "Create a personalized step-by-step employment plan. "
                "First provide a short strategy explanation, then 3-5 steps. "
                "After the plan, ask for start confirmation."
            )
        else:
            prompt = f"{context}\nUser message: {user_message}"

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
            error_message = f'OpenAI error: {str(e)}'
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
            'yes',
            'yes this works',
            'this works',
            'sounds good',
            'approve',
            'approved',
            "let's start",
            'let us start',
        }
        plan_confirmed = normalized in explicit_confirm_phrases

        response['plan_confirmed'] = plan_confirmed
        return response
