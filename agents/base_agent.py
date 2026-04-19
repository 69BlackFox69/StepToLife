import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class BaseAgent:
    """Base class for all agents"""
    
    def __init__(self, system_prompt):
        self.system_prompt = system_prompt
        self.model = "gpt-4o-mini"
        
        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file")
        
        self.client = OpenAI(api_key=api_key)
    
    def process(self, user_message, conversation_history=None):
        """
        Process user message.

        Args:
            user_message: Message from user
            conversation_history: Conversation history

        Returns:
            Agent response
        """
        if conversation_history is None:
            conversation_history = []
        
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Add conversation history
        messages.extend(conversation_history)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            
            message = response.choices[0].message.content
            
            return {
                'success': True,
                'message': message
            }
        except Exception as e:
            error_message = f'OpenAI error: {str(e)}'
            print(f"[ERROR] {error_message}")
            return {
                'success': False,
                'message': error_message
            }
