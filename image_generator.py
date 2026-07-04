"""
Image generation module using Hugging Face API
"""

import os
import logging
import requests
import time
from io import BytesIO
from typing import Optional, Dict, Any
from config import Config

logger = logging.getLogger(__name__)

class ImageGenerator:
    """Handles AI image generation using Hugging Face API"""
    
    def __init__(self):
        self.api_key = Config.HUGGINGFACE_API_KEY
        self.model = Config.HUGGINGFACE_MODEL
        self.api_url = f"https://api-inference.huggingface.co/models/{self.model}"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.last_request_time = 0
        self.min_interval = 2  # Minimum 2 seconds between requests
        
    async def generate(self, prompt: str) -> Optional[bytes]:
        """
        Generate an image from text prompt
        
        Args:
            prompt: Text description of the image
            
        Returns:
            Image data as bytes, or None if generation failed
        """
        if not self.api_key:
            logger.error("HUGGINGFACE_API_KEY not configured")
            return None
            
        if len(prompt) > Config.MAX_PROMPT_LENGTH:
            logger.warning(f"Prompt too long: {len(prompt)} characters")
            prompt = prompt[:Config.MAX_PROMPT_LENGTH]
            
        # Rate limiting
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
            
        self.last_request_time = time.time()
        
        try:
            logger.info(f"Generating image for prompt: {prompt[:50]}...")
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "negative_prompt": (
                        "blurry, bad quality, distorted, deformed, "
                        "low resolution, pixelated, ugly, nsfw"
                    ),
                    "num_inference_steps": 25,
                    "guidance_scale": 7.5,
                    "scheduler": "DPMSolverMultistepScheduler"
                }
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                logger.info("Image generated successfully")
                return response.content
            elif response.status_code == 503:
                # Model is loading
                await self.handle_model_loading(response)
                # Retry once
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=60
                )
                if response.status_code == 200:
                    logger.info("Image generated after model loading")
                    return response.content
            else:
                logger.error(f"API Error: {response.status_code} - {response.text}")
                return None
                
        except requests.Timeout:
            logger.error("Request timeout")
            return None
        except Exception as e:
            logger.error(f"Generation error: {e}")
            return None
            
    async def handle_model_loading(self, response: requests.Response):
        """Handle the case when the model is loading"""
        try:
            data = response.json()
            if "estimated_time" in data:
                wait_time = data["estimated_time"] + 5
                logger.info(f"Model loading, waiting {wait_time} seconds...")
                time.sleep(wait_time)
        except:
            logger.info("Model loading, waiting 30 seconds...")
            time.sleep(30)
            
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        try:
            response = requests.get(
                f"https://api-inference.huggingface.co/models/{self.model}",
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return {"model": self.model, "status": "unknown"}

# Alternative generators (you can swap these in)

class SDXLGenerator(ImageGenerator):
    """Stable Diffusion XL generator"""
    def __init__(self):
        super().__init__()
        self.model = "stabilityai/stable-diffusion-xl-base-1.0"

class DreamshaperGenerator(ImageGenerator):
    """Dreamshaper model for artistic images"""
    def __init__(self):
        super().__init__()
        self.model = "Lykon/dreamshaper-xl-1-0"

class OpenJourneyGenerator(ImageGenerator):
    """OpenJourney - Midjourney style"""
    def __init__(self):
        super().__init__()
        self.model = "prompthero/openjourney-v4"
