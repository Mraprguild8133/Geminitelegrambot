import re
from better_profanity import profanity
from gemini_ai import GeminiAI
import logging

class ContentModerator:
    def __init__(self):
        """Initialize content moderator"""
        self.gemini_ai = GeminiAI()
        self.logger = logging.getLogger(__name__)
        
        # Initialize profanity filter
        profanity.load_censor_words()
        
        # Common adult content keywords
        self.adult_keywords = [
            'xxx', 'porn', 'sex', 'nude', 'naked', 'adult', 'nsfw',
            'erotic', 'sexual', 'explicit', 'mature'
        ]
        
        # Copyright-related keywords
        self.copyright_keywords = [
            'pirated', 'cracked', 'leaked', 'bootleg', 'unauthorized',
            'copyright', '©', 'all rights reserved', 'proprietary'
        ]

    async def check_text_content(self, text: str) -> dict:
        """Check text for inappropriate content"""
        violations = []
        
        # Check for profanity
        if profanity.contains_profanity(text):
            violations.append("profanity")
        
        # Check for adult content
        text_lower = text.lower()
        if any(keyword in text_lower for keyword in self.adult_keywords):
            violations.append("adult_content")
        
        # Check for potential copyright violations
        if any(keyword in text_lower for keyword in self.copyright_keywords):
            violations.append("copyright")
        
        # Use Gemini AI for advanced moderation
        ai_result = await self.gemini_ai.moderate_content(text)
        if not ai_result["is_safe"]:
            violations.append("ai_flagged")
        
        return {
            "is_safe": len(violations) == 0,
            "violations": violations,
            "cleaned_text": profanity.censor(text) if violations else text
        }

    async def check_image_content(self, image_path: str) -> dict:
        """Basic image content checking"""
        try:
            # Load image
            img = cv2.imread(image_path)
            if img is None:
                return {"is_safe": True, "reason": "Could not process image"}
            
            # Basic checks (simplified)
            # In a real implementation, you'd use more sophisticated AI models
            height, width = img.shape[:2]
            
            # Check for suspicious aspect ratios or sizes
            if height < 100 or width < 100:
                return {"is_safe": False, "reason": "Suspicious image dimensions"}
            
            return {"is_safe": True, "reason": "Image passed basic checks"}
            
        except Exception as e:
            self.logger.error(f"Image moderation error: {e}")
            return {"is_safe": True, "reason": "Could not analyze image"}

    def clean_bad_words(self, text: str) -> str:
        """Clean bad words from text"""
        return profanity.censor(text)

    def is_spam_content(self, text: str) -> bool:
        """Check if content appears to be spam"""
        spam_indicators = [
            r'(https?://\S+){3,}',  # Multiple URLs
            r'[A-Z]{5,}',  # Excessive caps
            r'(.)\1{4,}',  # Repeated characters
            r'(buy now|click here|limited time|act now)',  # Spam phrases
        ]
        
        text_lower = text.lower()
        return any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in spam_indicators)