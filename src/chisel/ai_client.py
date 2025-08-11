"""
AI client interfaces and implementations for multiple providers.

Handles API communication, error handling, and response processing.
"""

import httpx
import json
import asyncio
from typing import Optional, Dict, Any, List, Protocol
from dataclasses import dataclass
from abc import ABC, abstractmethod
from loguru import logger


@dataclass
class AIResponse:
    """Response from AI API."""
    success: bool
    text: Optional[str] = None
    error: Optional[str] = None


@dataclass
class ModelInfo:
    """Information about a Gemini model."""
    name: str
    display_name: str
    description: Optional[str] = None
    version: Optional[str] = None
    input_token_limit: Optional[int] = None
    output_token_limit: Optional[int] = None
    supported_generation_methods: Optional[List[str]] = None


class AIClient(ABC):
    """Abstract base class for AI API clients."""
    
    @abstractmethod
    async def process_text(self, text: str, prompt: str, temperature: float = 0.7, top_p: float = 0.8) -> Optional[str]:
        """Process text with AI and return the result."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test the API connection."""
        pass
    
    @abstractmethod
    async def fetch_available_models(self) -> List[ModelInfo]:
        """Fetch available models from the API."""
        pass


class GeminiClient(AIClient):
    """Google Gemini API client for text processing."""
    
    def __init__(self, api_key: str, timeout: int = 30, model: str = "gemini-1.5-pro-latest"):
        self.api_key = api_key
        self.timeout = timeout
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.model = model
        
        logger.info(f"Gemini AI client initialized with model: {model}")
    
    async def process_text(self, text: str, prompt: str, temperature: float = 0.7, top_p: float = 0.8) -> Optional[str]:
        """
        Send text to Gemini API for processing.
        
        Args:
            text: Text to process
            prompt: Processing prompt/instruction
            
        Returns:
            Optional[str]: Processed text, or None if processing failed
        """
        if not text.strip():
            logger.warning("Empty text provided for processing")
            return None
        
        try:
            # Prepare the request
            request_data = self._build_request(text, prompt, temperature, top_p)
            
            # Make the API call
            response = await self._make_api_call(request_data)
            
            if response.success:
                return response.text
            else:
                logger.error(f"AI processing failed: {response.error}")
                return None
                
        except Exception as e:
            logger.error(f"Unexpected error during AI processing: {e}")
            return None
    
    def _build_request(self, text: str, prompt: str, temperature: float = 0.7, top_p: float = 0.8) -> Dict[str, Any]:
        """
        Build the API request payload.
        
        Args:
            text: Text to process
            prompt: Processing prompt
            
        Returns:
            Dict[str, Any]: Request payload
        """
        # For thinking models like Gemini 2.5, add system instruction to be concise
        system_instruction = None
        if "2.5" in self.model or "2.0" in self.model:
            system_instruction = {
                "parts": [{
                    "text": "You are a text rephrasing assistant. Respond ONLY with the rephrased text, no thinking, no explanation, no additional commentary. Be direct and concise."
                }]
            }
        
        request = {
            "contents": [{
                "parts": [{
                    "text": f"{prompt}\\n\\nText to process: {text}"
                }]
            }],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 8192,  # Increased for thinking models
                "topP": top_p,
                "topK": 40
            },
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH", 
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
        }
        
        # Add system instruction if available
        if system_instruction:
            request["systemInstruction"] = system_instruction
            
        return request
    
    async def _make_api_call(self, request_data: Dict[str, Any]) -> AIResponse:
        """
        Make the actual API call to Gemini.
        
        Args:
            request_data: Request payload
            
        Returns:
            AIResponse: API response
        """
        url = f"{self.base_url}/models/{self.model}:generateContent"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                logger.debug("Making API call to Gemini")
                
                response = await client.post(
                    url,
                    params={"key": self.api_key},
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Log the full response for debugging
                logger.debug(f"Full API response: {json.dumps(data, indent=2)}")
                
                # Extract response text
                processed_text = self._extract_response_text(data)
                
                if processed_text:
                    logger.info("AI processing completed successfully")
                    return AIResponse(success=True, text=processed_text)
                else:
                    return AIResponse(success=False, error="No valid response from AI")
                
            except httpx.TimeoutException:
                error_msg = f"API request timed out after {self.timeout} seconds"
                logger.error(error_msg)
                return AIResponse(success=False, error=error_msg)
                
            except httpx.HTTPStatusError as e:
                error_msg = f"API error: {e.response.status_code} - {e.response.text}"
                logger.error(error_msg)
                return AIResponse(success=False, error=error_msg)
                
            except json.JSONDecodeError:
                error_msg = "Invalid JSON response from API"
                logger.error(error_msg)
                return AIResponse(success=False, error=error_msg)
                
            except Exception as e:
                error_msg = f"Unexpected API error: {str(e)}"
                logger.error(error_msg)
                return AIResponse(success=False, error=error_msg)
    
    def _extract_response_text(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Extract text from API response with improved error handling.
        
        Args:
            data: API response JSON
            
        Returns:
            Optional[str]: Extracted text or None
        """
        try:
            # Log the structure we're working with
            logger.debug(f"Extracting text from response structure: {list(data.keys())}")
            
            candidates = data.get("candidates", [])
            if not candidates:
                logger.warning("No candidates in API response")
                logger.debug(f"Available top-level keys: {list(data.keys())}")
                return None
            
            candidate = candidates[0]
            logger.debug(f"First candidate keys: {list(candidate.keys())}")
            
            # Check finish reason for issues
            finish_reason = candidate.get("finishReason")
            if finish_reason:
                logger.debug(f"Finish reason: {finish_reason}")
                if finish_reason == "MAX_TOKENS":
                    logger.warning("Response was truncated due to token limit")
                elif finish_reason in ["SAFETY", "RECITATION"]:
                    logger.warning(f"Response blocked due to: {finish_reason}")
                    return None
            
            # Check for different response formats
            content = candidate.get("content", {})
            if not content:
                logger.warning("No content in candidate")
                logger.debug(f"Candidate structure: {candidate}")
                return None
            
            logger.debug(f"Content keys: {list(content.keys())}")
            parts = content.get("parts", [])
            
            if not parts:
                logger.warning("No parts in API response content")
                logger.debug(f"Content structure: {content}")
                
                # Try alternative structure for thinking models
                if "role" in content and "parts" not in content:
                    # Some models might have text directly in content
                    if "text" in content:
                        text = content.get("text", "").strip()
                        if text:
                            logger.info("Found text directly in content")
                            return text
                
                return None
            
            # Extract text from parts
            for i, part in enumerate(parts):
                logger.debug(f"Part {i} keys: {list(part.keys())}")
                text = part.get("text", "").strip()
                if text:
                    logger.info(f"Found text in part {i}")
                    return text
            
            logger.warning("No text found in any parts")
            return None
            
        except (KeyError, IndexError, AttributeError) as e:
            logger.error(f"Error extracting response text: {e}")
            logger.debug(f"Full error context - data keys: {list(data.keys()) if isinstance(data, dict) else 'not dict'}")
            return None
    
    async def test_connection(self) -> bool:
        """
        Test the API connection with a simple request.
        
        Returns:
            bool: True if connection is working
        """
        test_text = "Hello"
        test_prompt = "Simply return the word 'Success' if you can process this."
        
        try:
            result = await self.process_text(test_text, test_prompt)
            success = result is not None and "success" in result.lower()
            
            if success:
                logger.info("AI client connection test successful")
            else:
                logger.warning("AI client connection test failed")
                
            return success
            
        except Exception as e:
            logger.error(f"AI client connection test error: {e}")
            return False
    
    async def fetch_available_models(self) -> List[ModelInfo]:
        """
        Fetch available models from Google AI API.
        
        Returns:
            List[ModelInfo]: List of available models
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    params={"key": self.api_key}
                )
                
                response.raise_for_status()
                data = response.json()
                
                models = []
                for model_data in data.get("models", []):
                    # Only include models that support generateContent
                    supported_methods = model_data.get("supportedGenerationMethods", [])
                    if "generateContent" in supported_methods:
                        model_info = ModelInfo(
                            name=model_data.get("name", "").replace("models/", ""),
                            display_name=model_data.get("displayName", ""),
                            description=model_data.get("description", ""),
                            version=model_data.get("version", ""),
                            input_token_limit=model_data.get("inputTokenLimit"),
                            output_token_limit=model_data.get("outputTokenLimit"),
                            supported_generation_methods=supported_methods
                        )
                        models.append(model_info)
                
                logger.info(f"Fetched {len(models)} available models")
                return models
                
        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return self._get_fallback_models()
    
    def _get_fallback_models(self) -> List[ModelInfo]:
        """
        Get fallback model list when API call fails.
        
        Returns:
            List[ModelInfo]: Fallback models list
        """
        fallback_models = self._get_fallback_models_static()
        
        logger.info("Using fallback model list")
        return fallback_models
    
    @staticmethod
    async def fetch_models_static(api_key: str, timeout: int = 10) -> List[ModelInfo]:
        """
        Static method to fetch models without creating a client instance.
        
        Args:
            api_key: Google AI API key
            timeout: Request timeout in seconds
            
        Returns:
            List[ModelInfo]: Available models
        """
        if not api_key:
            return GeminiClient._get_fallback_models_static()
            
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(
                    "https://generativelanguage.googleapis.com/v1beta/models",
                    params={"key": api_key}
                )
                
                response.raise_for_status()
                data = response.json()
                
                models = []
                for model_data in data.get("models", []):
                    supported_methods = model_data.get("supportedGenerationMethods", [])
                    if "generateContent" in supported_methods:
                        model_info = ModelInfo(
                            name=model_data.get("name", "").replace("models/", ""),
                            display_name=model_data.get("displayName", ""),
                            description=model_data.get("description", ""),
                            version=model_data.get("version", ""),
                            input_token_limit=model_data.get("inputTokenLimit"),
                            output_token_limit=model_data.get("outputTokenLimit"),
                            supported_generation_methods=supported_methods
                        )
                        models.append(model_info)
                
                return models
                
        except Exception as e:
            logger.error(f"Error fetching models (static): {e}")
            return GeminiClient._get_fallback_models_static()
    
    @staticmethod
    def _get_fallback_models_static() -> List[ModelInfo]:
        """Static fallback models - updated with latest 2.5 models."""
        return [
            ModelInfo(
                name="gemini-2.5-pro",
                display_name="Gemini 2.5 Pro",
                description="Latest Gemini 2.5 Pro with advanced reasoning"
            ),
            ModelInfo(
                name="gemini-2.5-flash",
                display_name="Gemini 2.5 Flash",
                description="Fast and efficient Gemini 2.5 model"
            ),
            ModelInfo(
                name="gemini-2.0-flash-exp",
                display_name="Gemini 2.0 Flash (Experimental)",
                description="Latest experimental Gemini 2.0 model"
            ),
            ModelInfo(
                name="gemini-1.5-pro-latest", 
                display_name="Gemini 1.5 Pro (Latest)",
                description="Latest Gemini 1.5 Pro model"
            ),
            ModelInfo(
                name="gemini-1.5-pro",
                display_name="Gemini 1.5 Pro",
                description="Stable Gemini 1.5 Pro model"
            ),
            ModelInfo(
                name="gemini-1.5-flash-latest",
                display_name="Gemini 1.5 Flash (Latest)",
                description="Latest fast Gemini 1.5 model"
            ),
            ModelInfo(
                name="gemini-1.5-flash",
                display_name="Gemini 1.5 Flash",
                description="Fast and efficient Gemini model"
            ),
            ModelInfo(
                name="gemini-pro",
                display_name="Gemini Pro",
                description="Standard Gemini Pro model"
            )
        ]


class OpenRouterClient(AIClient):
    """OpenRouter API client for text processing using OpenAI-compatible format."""
    
    def __init__(self, api_key: str, timeout: int = 30, model: str = "openai/gpt-oss-20b:free"):
        self.api_key = api_key
        self.timeout = timeout
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"
        
        logger.info(f"OpenRouter AI client initialized with model: {model}")
    
    async def process_text(self, text: str, prompt: str, temperature: float = 0.7, top_p: float = 0.8) -> Optional[str]:
        """
        Send text to OpenRouter API for processing.
        
        Args:
            text: Text to process
            prompt: Processing prompt/instruction
            temperature: Temperature for generation
            top_p: Top-p for generation
            
        Returns:
            Optional[str]: Processed text, or None if processing failed
        """
        if not text.strip():
            logger.warning("Empty text provided for processing")
            return None
        
        try:
            # Prepare the request
            request_data = self._build_request(text, prompt, temperature, top_p)
            
            # Make the API call
            response = await self._make_api_call(request_data)
            
            if response.success:
                return response.text
            else:
                logger.error(f"AI processing failed: {response.error}")
                return None
                
        except Exception as e:
            logger.error(f"Unexpected error during AI processing: {e}")
            return None
    
    def _build_request(self, text: str, prompt: str, temperature: float = 0.7, top_p: float = 0.8) -> Dict[str, Any]:
        """
        Build the API request payload for OpenRouter (OpenAI format).
        
        Args:
            text: Text to process
            prompt: Processing prompt
            temperature: Temperature for generation
            top_p: Top-p for generation
            
        Returns:
            Dict[str, Any]: Request payload
        """
        # Combine prompt and text for OpenRouter
        full_prompt = f"{prompt}\n\nText to process: {text}"
        
        return {
            "model": self.model,
            "messages": [
                {
                    "role": "user", 
                    "content": full_prompt
                }
            ],
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": 1000,
            "stream": False
        }
    
    async def _make_api_call(self, request_data: Dict[str, Any]) -> AIResponse:
        """
        Make the actual API call to OpenRouter.
        
        Args:
            request_data: Request payload
            
        Returns:
            AIResponse: API response
        """
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/chisel/chisel",  # Optional: for OpenRouter analytics
            "X-Title": "Chisel Text Rephrasing Tool"  # Optional: for OpenRouter analytics
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                logger.debug("Making API call to OpenRouter")
                
                response = await client.post(
                    url,
                    json=request_data,
                    headers=headers
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Log the full response for debugging
                logger.debug(f"Full API response: {json.dumps(data, indent=2)}")
                
                # Extract response text
                processed_text = self._extract_response_text(data)
                
                if processed_text:
                    logger.info("AI processing completed successfully")
                    return AIResponse(success=True, text=processed_text)
                else:
                    return AIResponse(success=False, error="No valid response from AI")
                
            except httpx.TimeoutException:
                error_msg = f"API request timed out after {self.timeout} seconds"
                logger.error(error_msg)
                return AIResponse(success=False, error=error_msg)
                
            except httpx.HTTPStatusError as e:
                error_msg = f"API error: {e.response.status_code} - {e.response.text}"
                logger.error(error_msg)
                return AIResponse(success=False, error=error_msg)
                
            except json.JSONDecodeError:
                error_msg = "Invalid JSON response from API"
                logger.error(error_msg)
                return AIResponse(success=False, error=error_msg)
                
            except Exception as e:
                error_msg = f"Unexpected API error: {str(e)}"
                logger.error(error_msg)
                return AIResponse(success=False, error=error_msg)
    
    def _extract_response_text(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Extract text from OpenRouter API response (OpenAI format).
        
        Args:
            data: API response JSON
            
        Returns:
            Optional[str]: Extracted text or None
        """
        try:
            # Log the structure we're working with
            logger.debug(f"Extracting text from OpenRouter response structure: {list(data.keys())}")
            
            choices = data.get("choices", [])
            if not choices:
                logger.warning("No choices in OpenRouter API response")
                logger.debug(f"Available top-level keys: {list(data.keys())}")
                return None
            
            choice = choices[0]
            logger.debug(f"First choice keys: {list(choice.keys())}")
            
            message = choice.get("message", {})
            if not message:
                logger.warning("No message in choice")
                logger.debug(f"Choice structure: {choice}")
                return None
            
            logger.debug(f"Message keys: {list(message.keys())}")
            content = message.get("content", "").strip()
            
            if not content:
                logger.warning("Empty content in API response")
                return None
            
            logger.info("Found content in OpenRouter response")
            return content
            
        except (KeyError, IndexError, AttributeError) as e:
            logger.error(f"Error extracting response text: {e}")
            logger.debug(f"Full error context - data keys: {list(data.keys()) if isinstance(data, dict) else 'not dict'}")
            return None
    
    async def test_connection(self) -> bool:
        """
        Test the API connection with a simple request.
        
        Returns:
            bool: True if connection is working
        """
        test_text = "Hello"
        test_prompt = "Simply return the word 'Success' if you can process this."
        
        try:
            result = await self.process_text(test_text, test_prompt)
            success = result is not None and "success" in result.lower()
            
            if success:
                logger.info("OpenRouter client connection test successful")
            else:
                logger.warning("OpenRouter client connection test failed")
                
            return success
            
        except Exception as e:
            logger.error(f"OpenRouter client connection test error: {e}")
            return False
    
    async def fetch_available_models(self) -> List[ModelInfo]:
        """
        Fetch available models from OpenRouter API.
        
        Returns:
            List[ModelInfo]: List of available models
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                
                response.raise_for_status()
                data = response.json()
                
                models = []
                for model_data in data.get("data", []):
                    model_info = ModelInfo(
                        name=model_data.get("id", ""),
                        display_name=model_data.get("name", model_data.get("id", "")),
                        description=model_data.get("description", ""),
                        input_token_limit=model_data.get("context_length"),
                        output_token_limit=model_data.get("top_provider", {}).get("max_completion_tokens"),
                    )
                    models.append(model_info)
                
                logger.info(f"Fetched {len(models)} OpenRouter models")
                return models
                
        except Exception as e:
            logger.error(f"Error fetching OpenRouter models: {e}")
            return self._get_fallback_models()
    
    def _get_fallback_models(self) -> List[ModelInfo]:
        """
        Get fallback model list when API call fails.
        
        Returns:
            List[ModelInfo]: Fallback models list
        """
        fallback_models = [
            ModelInfo(
                name="openai/gpt-oss-20b:free",
                display_name="GPT OSS 20B (Free)",
                description="Free OpenRouter model with 1000 requests/day"
            ),
            ModelInfo(
                name="openai/gpt-4o-mini",
                display_name="GPT-4o Mini",
                description="Faster and cheaper GPT-4 variant"
            ),
            ModelInfo(
                name="anthropic/claude-3-haiku",
                display_name="Claude 3 Haiku",
                description="Fast and efficient Claude model"
            ),
            ModelInfo(
                name="meta-llama/llama-3.1-8b-instruct:free",
                display_name="Llama 3.1 8B (Free)",
                description="Free Llama model"
            ),
            ModelInfo(
                name="google/gemini-flash-1.5",
                display_name="Gemini Flash 1.5",
                description="Fast Google model via OpenRouter"
            )
        ]
        
        logger.info("Using OpenRouter fallback model list")
        return fallback_models


def create_ai_client(api_provider: str, api_key: str, model: str, timeout: int = 30) -> Optional[AIClient]:
    """
    Factory function to create appropriate AI client based on provider.
    
    Args:
        api_provider: Provider name ("google" or "openrouter")
        api_key: API key for the provider
        model: Model to use
        timeout: Request timeout
        
    Returns:
        AIClient instance or None if provider not supported
    """
    if api_provider == "google":
        return GeminiClient(api_key, timeout, model)
    elif api_provider == "openrouter":
        return OpenRouterClient(api_key, timeout, model)
    else:
        logger.error(f"Unsupported API provider: {api_provider}")
        return None