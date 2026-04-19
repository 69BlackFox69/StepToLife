from agents.base_agent import BaseAgent

class LanguageAgent(BaseAgent):
    """Second agent: Slovak language learning via micro-lessons"""
    
    def __init__(self):
        system_prompt = """You are an enthusiastic and patient Slovak language teacher on the StepToLife platform.

Your goal is to help the user learn practical Slovak for employment through micro-lessons.

Approach:
- Adapt difficulty to the user level (beginner, intermediate, advanced)
- Structure each lesson like this:
    1. Introduce the topic in 1-2 sentences
    2. Provide the core content (5-7 useful phrases)
    3. Include practice (2-3 interactive questions)
    4. Show workplace usage (real-life job situations)
- Use practical examples from work and hiring contexts
- Stay supportive: anyone can learn a language

Recommended topics:
- Beginner: greetings, self-introduction, numbers, weekdays, professions, essential phrases
- Intermediate: business communication, interview conversation, writing short messages
- Advanced: negotiation, specialized vocabulary, cultural nuances

Many users are from vulnerable groups, so:
- Be especially positive and encouraging
- Never criticize mistakes; celebrate progress
- Show that language learning is achievable for adults
- Give motivating success examples

Language: English with Slovak examples."""
        super().__init__(system_prompt)
    
    def process(self, user_message, conversation_history, lesson_level='beginner'):
        """Process message and provide the first micro-lesson"""

        normalized = ' '.join((user_message or '').lower().replace('!', ' ').replace('.', ' ').replace(',', ' ').replace('?', ' ').replace(':', ' ').replace(';', ' ').replace('"', ' ').replace("'", ' ').replace('`', ' ').split())
        start_phrases = {
            'да',
            'готов',
            'готова',
            'начать',
            'поехали',
            'да, помоги мне начать говорить по словацки',
            'помоги мне начать говорить по словацки',
            'помоги мне выучить словацкий',
            'хочу учить словацкий',
            'yes',
            'ok',
            'okay',
            'start',
            'let us start',
            "let's start",
            'ready',
        }

        if normalized in start_phrases or normalized.startswith('да') or normalized.startswith('yes') or 'помоги мне' in normalized or 'help me' in normalized:
            lesson = (
                "Great. Let us start with the basics.\n\n"
                "Micro-lesson 1: greetings.\n"
                "Remember these 3 short phrases:\n"
                "- Dobrý deň - Good day\n"
                "- Ahoj - Hi\n"
                "- Ďakujem - Thank you\n\n"
                "How to use them at work: say 'Dobrý deň' when entering and 'Ďakujem' at the end of a conversation.\n\n"
                "Now try writing: Dobrý deň."
            )
            return {
                'success': True,
                'message': lesson,
                'lesson_level': lesson_level,
                'lesson_step': 1
            }

        if not normalized or normalized in {'нет', 'не', 'no'}:
            return {
                'success': True,
                'message': 'Write "yes" if you want to start a short Slovak lesson.',
                'lesson_level': lesson_level,
                'lesson_step': 0
            }

        enhanced_history = conversation_history.copy() if conversation_history else []
        level_info = f"\n[Lesson level: {lesson_level}]"
        response = super().process(user_message + level_info, enhanced_history)

        if not response['success']:
            return response

        return {
            'success': True,
            'message': response['message'],
            'lesson_level': lesson_level,
            'lesson_step': 1
        }
