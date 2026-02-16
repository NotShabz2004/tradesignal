"""
AI Analyzer using Google Gemini API (Updated for 2026 SDK)
Makes intelligent decisions about when to alert users
"""
import json
import logging
import time
from typing import Dict, Optional, List
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_MAX_RETRIES

logger = logging.getLogger(__name__)

class AIAnalyzer:
    def __init__(self):
        """Initialize Gemini API client"""
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in configuration")
        
        # NEW: Initialize the Client instead of configuring a global object
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        logger.info(f"AI Analyzer initialized with model: {GEMINI_MODEL}")
    
    def _create_prompt(self, prices: Dict[str, float], changes_10min: Dict[str, float],
                      changes_24h: Dict[str, float], feedback_history: List[Dict]) -> str:
        """Create prompt for Gemini AI"""
        
        # Format feedback history
        feedback_text = "No previous feedback available."
        if feedback_history:
            helpful_count = sum(1 for f in feedback_history if f.get("user_feedback") == "helpful")
            not_helpful_count = sum(1 for f in feedback_history if f.get("user_feedback") == "not_helpful")
            feedback_text = f"User feedback history:\n- Helpful alerts: {helpful_count}\n- Not helpful alerts: {not_helpful_count}"
        
        # Format price data
        price_data = []
        for coin in ["bitcoin", "ethereum", "solana"]:
            coin_name = coin.capitalize()
            price = prices.get(coin, 0)
            change_10min = changes_10min.get(coin, 0)
            change_24h = changes_24h.get(coin, 0)
            price_data.append(
                f"{coin_name}: ${price:,.2f} ({change_10min:+.2f}% in 10 mins, {change_24h:+.2f}% in 24h)"
            )
        
        prompt = f"""You are a crypto trading assistant. Analyze this data:

{chr(10).join(price_data)}

{feedback_text}

Should I alert the user? Consider:
- Magnitude of price change (we only check if >3% change occurred)
- Multiple coins moving together (correlation)
- User's past preferences (from feedback)
- Whether the change is significant enough to warrant attention

Respond ONLY with valid JSON (no markdown, no code blocks):
{{
  "should_alert": true or false,
  "coin": "bitcoin" or "ethereum" or "solana" (the most significant change),
  "reason": "brief explanation of why",
  "confidence": 0-100,
  "message": "alert text for user (max 200 chars)"
}}"""
        
        return prompt
    
    def analyze_price_change(self, prices: Dict[str, float], 
                           changes_10min: Dict[str, float],
                           changes_24h: Dict[str, float],
                           feedback_history: List[Dict]) -> Optional[Dict]:
        """
        Ask Gemini AI if we should alert the user
        """
        prompt = self._create_prompt(prices, changes_10min, changes_24h, feedback_history)
        
        for attempt in range(GEMINI_MAX_RETRIES):
            try:
                logger.debug(f"Calling Gemini API (attempt {attempt + 1}/{GEMINI_MAX_RETRIES})")
                
                # NEW: Updated call syntax for google-genai SDK
                response = self.client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                        max_output_tokens=500,
                        response_mime_type="application/json" # Enforces JSON output!
                    )
                )
                
                # Extract text
                response_text = response.text.strip()
                
                # Clean up any potential markdown (though response_mime_type helps prevent this)
                if response_text.startswith("```"):
                    response_text = response_text.split("```")[1]
                    if response_text.startswith("json"):
                        response_text = response_text[4:]
                    response_text = response_text.strip()
                
                # Parse JSON
                result = json.loads(response_text)
                
                # Validate response structure
                required_keys = ["should_alert", "coin", "reason", "confidence", "message"]
                if not all(key in result for key in required_keys):
                    logger.warning(f"Invalid response structure: {result}")
                    return None
                
                # Ensure coin is valid
                if result["coin"] not in ["bitcoin", "ethereum", "solana"]:
                    logger.warning(f"Invalid coin in response: {result['coin']}")
                    return None
                
                # Ensure confidence is in valid range
                result["confidence"] = max(0, min(100, int(result.get("confidence", 50))))
                
                logger.info(f"Gemini decision: alert={result['should_alert']}, coin={result['coin']}, confidence={result['confidence']}")
                return result
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON response (attempt {attempt + 1}): {e}")
                if attempt < GEMINI_MAX_RETRIES - 1:
                    time.sleep(1)
                    continue
                return None
                
            except Exception as e:
                logger.error(f"Error calling Gemini API (attempt {attempt + 1}): {e}")
                if attempt < GEMINI_MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                    continue
                return None
        
        logger.error("Failed to get response from Gemini after all retries")
        return None