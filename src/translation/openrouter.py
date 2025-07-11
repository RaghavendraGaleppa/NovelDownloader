import requests
import os
import json
import copy
from rich.console import Console

# --- Configuration ---

CONSOLE = Console()
SECRETS_FILE = "secrets.json"

# This dictionary still defines the technical details for each provider.
api_providers = {
    "chutes": {
        "url": "https://llm.chutes.ai/v1/chat/completions",
        "model_names": ["deepseek-ai/DeepSeek-V3-0324"]
    },
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model_names": [
            "deepseek/deepseek-chat-v3-0324:free",
            "google/gemini-2.0-flash-exp:free",
            "meta-llama/llama-4-maverick:free",
            "qwen/qwq-32b:free"
        ]
    }
}

# --- API Key Loading ---

def _load_api_keys() -> list[dict]:
    """Loads API keys from the secrets.json file."""
    if not os.path.exists(SECRETS_FILE):
        return []
    try:
        with open(SECRETS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        keys = data.get("api_keys", [])
        if not isinstance(keys, list):
            CONSOLE.print(f"⚠️  Warning: 'api_keys' in {SECRETS_FILE} is not a list. No keys loaded.", style="yellow")
            return []
        return keys
    except (json.JSONDecodeError, IOError) as e:
        CONSOLE.print(f"❌ Error reading {SECRETS_FILE}: {e}", style="red")
        return []

# Load keys at module start
LOADED_API_KEYS = _load_api_keys()

# --- Core Translation Logic ---

def translate_chinese_to_english(text_to_translate: str, key_override: dict | None = None) -> tuple[str, str | None]:
    """
    Translates Chinese text to English using a fallback-enabled system based on keys in secrets.json.
    It will try each key and its associated models until one succeeds.

    Args:
        text_to_translate (str): The Chinese text to be translated.
        key_override (dict | None): If provided, uses only this key info instead of the full list. For testing.

    Returns:
        tuple[str, str | None]: A tuple containing:
            - The translated English text, or an error message if all keys and models fail.
            - The name of the key/provider that succeeded, or None on failure.
    """
    keys_to_use = [key_override] if key_override else LOADED_API_KEYS

    if not keys_to_use:
        return f"Error: No API keys found in {SECRETS_FILE} or the file is missing/invalid.", None

    for i, key_info in enumerate(keys_to_use):
        provider_name = key_info.get("provider")
        api_key = key_info.get("key")
        key_name = key_info.get("name", f"Provider: {provider_name}")

        if not provider_name or not api_key:
            CONSOLE.print(f"⏩ Skipping invalid key entry at index {i} in {SECRETS_FILE} (missing 'provider' or 'key').", style="yellow")
            continue

        if provider_name not in api_providers:
            CONSOLE.print(f"⏩ Skipping key for unknown provider '{provider_name}' at index {i}.", style="yellow")
            continue

        provider_config = copy.deepcopy(api_providers[provider_name])
        api_url = provider_config["url"]
        available_models = provider_config["model_names"]

        CONSOLE.print(f"🔄 Attempting translation with: [bold cyan]{key_name}[/bold cyan] (Key #{i + 1})", style="dim")

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        
        for model_name in available_models:
            messages = [
                {"role": "system", "content": "You are a professional Chinese to English translator and editor for Xianxia novels. The provided text may be merged from multiple pages, causing repeated chapter titles and promotional text. Please translate it into a clean, continuous chapter. You MUST: 1. Remove all advertisements and non-story metadata. 2. Keep the chapter title only once at the beginning and remove any duplicates. 3. Merge all content into a seamless narrative. Output only the final, clean, and consolidated English translation."},
                {"role": "user", "content": f"Translate, clean, and consolidate the following text into a single continuous chapter: '{text_to_translate}'"}
            ]
            payload = {
                "model": model_name, "messages": messages, "temperature": 0.3, "max_tokens": 50000
            }

            try:
                # I am setting the timeout to 5 minutes
                response = requests.post(api_url, headers=headers, json=payload, timeout=5*60)
                response.raise_for_status()
                response_data = response.json()
                
                if response_data and response_data.get("choices"):
                    translated_text = response_data["choices"][0]["message"]["content"].strip()
                    CONSOLE.print(f"✅ Success with [bold cyan]{key_name}[/bold cyan] using model [green]{model_name}[/green].", style="dim")
                    return translated_text, key_name
                else:
                    CONSOLE.print(f"⚠️  Warning: No translation found in API response for model {model_name}. Response: {response_data}", style="yellow")
                    continue

            except requests.exceptions.HTTPError as http_err:
                if http_err.response is not None and http_err.response.status_code == 429:
                    CONSOLE.print(f"Rate limit for model {model_name}. Trying next model...", style="yellow")
                    continue
                else:
                    error_body = http_err.response.text if http_err.response else "No response body"
                    CONSOLE.print(f"❌ HTTP Error with {provider_name}/{model_name}: {http_err} - {error_body}", style="red")
                    break  # Break from model loop, move to next key
            except requests.exceptions.RequestException as req_err:
                CONSOLE.print(f"❌ Request Error with {provider_name}/{model_name}: {req_err}", style="red")
                break # Break from model loop, move to next key
            except Exception as e:
                CONSOLE.print(f"❌ Unforeseen Error with {provider_name}/{model_name}: {e}", style="red")
                break # Break from model loop, move to next key

    return "Error: All specified API keys and models failed to provide a translation.", None

if __name__ == "__main__":
    # --- IMPORTANT ---
    # Ensure your API key is set as an environment variable named API_KEY.
    # The value of API_KEY should be the API key for the provider you intend to use.
    # For Chutes (default): export API_KEY="your_chutes_api_key"
    # For OpenRouter: export API_KEY="your_openrouter_api_key"
    # If a provider in api_providers has a different api_key_env_var specified, that will be used for it.

    # Example 1: Using the default provider (Chutes)
    # Make sure API_KEY is set to your Chutes API key before running this.
    print("\n--- Example 1: Using default provider (Chutes) ---")
    chinese_text_1 = "你好，世界！这是一个测试翻译。"
    print(f"Original Chinese text: {chinese_text_1}\n")
    print("Translating...")
    english_translation_1, provider_1 = translate_chinese_to_english(chinese_text_1)
    print(f"Translated English text: {english_translation_1} (Provider: {provider_1})")

    # Example 2: Specifying OpenRouter as the provider
    # Make sure API_KEY is set to your OpenRouter API key before running this.
    print("\n\n--- Example 2: Using OpenRouter provider ---")
    chinese_text_2 = "今天天气真好，适合出去走走。"
    print(f"Original Chinese text: {chinese_text_2}\n")
    print("Translating...")
    # Ensure OPENROUTER_API_KEY is set in your environment for this to work
    # Update: Ensure API_KEY is set to your OpenRouter key for this to work
    english_translation_2, provider_2 = translate_chinese_to_english(chinese_text_2)
    print(f"Translated English text: {english_translation_2} (Provider: {provider_2})")

    # Example 3: Testing with a non-configured provider
    print("\n\n--- Example 3: Testing non-configured provider ---")
    chinese_text_3 = "这是第三个测试。"
    print(f"Original Chinese text: {chinese_text_3}\n")
    print("Translating...")
    english_translation_3, provider_3 = translate_chinese_to_english(chinese_text_3)
    print(f"Translated English text: {english_translation_3} (Provider: {provider_3})")

