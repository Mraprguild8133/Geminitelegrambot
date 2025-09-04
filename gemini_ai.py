import google.generativeai as genai
from config import config
import logging

class GeminiAI:
    def __init__(self):
        """Initialize Gemini AI with API key"""
        if config.GEMINI_API_KEY:
            genai.configure(api_key=config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.logger = logging.getLogger(__name__)

    async def generate_response(self, prompt: str, context: str = None) -> str:
        """Generate AI response using Gemini"""
        try:
            if context:
                full_prompt = f"Context: {context}\n\nUser: {prompt}\n\nPlease provide a helpful response:"
            else:
                full_prompt = prompt

            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            self.logger.error(f"Gemini AI error: {e}")
            return "I'm sorry, I encountered an error while processing your request. Please try again."

    async def moderate_content(self, text: str) -> dict:
        """Use Gemini to analyze content for moderation"""
        try:
            moderation_prompt = f"""
            Analyze this content for:
            1. Adult/explicit content
            2. Hate speech or harassment
            3. Copyright violations (obvious copied content)
            4. Spam or promotional content
            5. Harmful or dangerous content

            Content: "{text}"

            Respond in JSON format:
            {{
                "is_safe": true/false,
                "violations": ["list of violations found"],
                "confidence": 0.0-1.0,
                "reason": "explanation"
            }}
            """
            
            response = self.model.generate_content(moderation_prompt)
            # Parse JSON response (simplified for now)
            if "false" in response.text.lower():
                return {"is_safe": False, "reason": "Content flagged by AI"}
            return {"is_safe": True, "reason": "Content approved by AI"}
        except Exception as e:
            self.logger.error(f"Content moderation error: {e}")
            return {"is_safe": True, "reason": "Moderation unavailable"}