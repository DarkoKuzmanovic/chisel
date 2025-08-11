#!/usr/bin/env python3
"""
Test script for OpenRouter integration in Chisel.

This script tests the OpenRouter client functionality without requiring
a full GUI setup.
"""

import asyncio
import os
from src.chisel.ai_client import OpenRouterClient
from src.chisel.settings import ChiselSettings, APIProvider

async def test_openrouter_models():
    """Test fetching models from OpenRouter."""
    print("Testing OpenRouter model fetching...")
    
    # Use a dummy API key for testing model fetching structure
    # (This will fail but should show the API structure)
    client = OpenRouterClient("dummy-key", timeout=10)
    
    try:
        models = await client.fetch_available_models()
        print(f"Fetched {len(models)} fallback models (API call expected to fail with dummy key):")
        for model in models[:5]:  # Show first 5 models
            print(f"  - {model.name}: {model.display_name}")
            if model.description:
                print(f"    Description: {model.description[:100]}...")
    except Exception as e:
        print(f"Expected error with dummy key: {e}")
    
    print("\nFallback models available:")
    fallback_models = client._get_fallback_models()
    for model in fallback_models:
        print(f"  - {model.name}: {model.display_name}")
        if model.description:
            print(f"    {model.description}")

def test_settings_provider_switching():
    """Test settings model provider switching."""
    print("\nTesting settings provider switching...")
    
    # Create settings with Google provider
    settings = ChiselSettings(api_provider=APIProvider.GOOGLE)
    settings.google_api_key = "google-test-key"
    settings.google_model = "gemini-2.5-pro"
    settings.openrouter_api_key = "openrouter-test-key"
    settings.openrouter_model = "openai/gpt-oss-20b:free"
    
    print(f"Google provider - API key: {settings.current_api_key}, Model: {settings.current_model}")
    
    # Switch to OpenRouter
    settings.api_provider = APIProvider.OPENROUTER
    print(f"OpenRouter provider - API key: {settings.current_api_key}, Model: {settings.current_model}")
    
    # Test setting current values
    settings.set_current_api_key("new-openrouter-key")
    settings.set_current_model("anthropic/claude-3-haiku")
    print(f"After updates - API key: {settings.current_api_key}, Model: {settings.current_model}")

async def test_openrouter_request_format():
    """Test OpenRouter request building."""
    print("\nTesting OpenRouter request format...")
    
    client = OpenRouterClient("test-key", model="openai/gpt-oss-20b:free")
    
    # Test request building
    test_text = "Hello world"
    test_prompt = "Rephrase this professionally"
    
    request = client._build_request(test_text, test_prompt, 0.7, 0.8)
    
    print("Generated request structure:")
    print(f"  Model: {request['model']}")
    print(f"  Messages: {request['messages']}")
    print(f"  Temperature: {request['temperature']}")
    print(f"  Max tokens: {request['max_tokens']}")

async def main():
    """Run all tests."""
    print("=== Chisel OpenRouter Integration Test ===\n")
    
    await test_openrouter_models()
    test_settings_provider_switching()
    await test_openrouter_request_format()
    
    print("\n=== Test completed ===")
    print("\nTo fully test OpenRouter integration:")
    print("1. Get an OpenRouter API key from https://openrouter.ai/")
    print("2. Run Chisel and open Settings")
    print("3. Select 'OpenRouter' as provider")
    print("4. Enter your API key")
    print("5. Select 'openai/gpt-oss-20b:free' model (1000 free requests/day)")
    print("6. Test text rephrasing with Ctrl+Shift+R")

if __name__ == "__main__":
    asyncio.run(main())