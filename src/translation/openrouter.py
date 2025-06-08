import requests
import os

model_names = [
    "deepseek/deepseek-chat-v3-0324:free",
    "google/gemini-2.0-flash-exp:free",
]

api_providers = {
    "chutes": {
        "url": "https://llm.chutes.ai/v1/chat/completions",
        "model_names": [
            "deepseek-ai/DeepSeek-V3-0324"
        ],
        "api_key_env_var": "API_KEY"
    },
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model_names": [
            "deepseek/deepseek-chat-v3-0324:free",
            "google/gemini-2.0-flash-exp:free",
        ],
        "api_key_env_var": "API_KEY"
    }
}

def translate_chinese_to_english(text_to_translate: str, api_provider_name: str = "chutes") -> str:
    """
    Translates Chinese text to English using the specified API provider, trying multiple models if rate limits are hit.

    Args:
        text_to_translate (str): The Chinese text to be translated.
        api_provider_name (str): The name of the API provider to use (e.g., "chutes", "openrouter"). Defaults to "chutes".

    Returns:
        str: The translated English text, or an error message if translation fails for all models.
    """
    if api_provider_name not in api_providers:
        return f"Error: API provider '{api_provider_name}' not configured."

    provider_config = api_providers[api_provider_name]
    api_url = provider_config["url"]
    available_models = provider_config["model_names"]
    api_key_env_variable = provider_config.get("api_key_env_var", "API_KEY") # Get specific or default to API_KEY
    
    api_key = os.getenv(api_key_env_variable)

    if not api_key:
        return f"Error: API key environment variable '{api_key_env_variable}' not set."

    # Print provider name in a box
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        # Optional: Set a referrer if you're using it in a web application
        # "HTTP-Referer": "YOUR_APP_URL",
        # Optional: Set X-Title for analytics
        # "X-Title": "YOUR_APP_NAME",
    }

    for model_name in available_models:
        # The prompt instructs the model to act as a translator.
        # It's crucial to be clear about the source and target languages.
        messages = [
            {"role": "system", "content": "You are a professional Chinese to English translator specializing in Xianxia novel style. Translate the following Chinese text, which is from a Xianxia novel, accurately and naturally into English, maintaining the specific tone, terminology, and cultural nuances characteristic of the genre."},
            {"role": "user", "content": f"Translate this Chinese text, which is from a Xianxia novel, into English: '{text_to_translate}'"}
        ]

        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.3, # Lower temperature for more deterministic and accurate translation
            "max_tokens": 50000,  # Adjust as needed for the length of expected translation
        }

        try:
            response = requests.post(api_url, headers=headers, json=payload)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)

            response_data = response.json()

            # Check if the response contains choices and message content
            if response_data and response_data.get("choices"):
                translated_text = response_data["choices"][0]["message"]["content"].strip()
                return translated_text
            else:
                # This case might occur if the response is 200 OK but doesn't contain the expected data.
                print(f"Warning: No translation found in API response for model {model_name}. Response: {response_data}")
                # Continue to the next model as this one didn't provide a translation.
                continue

        except requests.exceptions.HTTPError as http_err:
            if http_err.response is not None and http_err.response.status_code == 429:
                print(f"Rate limit exceeded for model {model_name}. Trying next model if available. Error: {http_err} - Response: {http_err.response.text}")
                continue  # Try the next model
            else:
                # For other HTTP errors, return the error and stop.
                error_response_text = http_err.response.text if http_err.response is not None else "No response body"
                return f"HTTP error occurred with model {model_name}: {http_err} - Response: {error_response_text}"
        except requests.exceptions.ConnectionError as conn_err:
            # This error is not model-specific in the same way, but retrying with another model might not help if it's a general network issue.
            # However, to stick to the "try all models" logic, we can report and continue, or decide to bail out.
            # For now, let's assume it might be a transient issue with a specific model endpoint or routing.
            print(f"Connection error occurred while trying model {model_name}: {conn_err}. Trying next model if available.")
            continue
        except requests.exceptions.Timeout as timeout_err:
            print(f"Timeout error occurred with model {model_name}: {timeout_err}. Trying next model if available.")
            continue
        except requests.exceptions.RequestException as req_err:
            # For other request-related errors, stop and report.
            return f"An unexpected request error occurred with model {model_name}: {req_err}"
        except Exception as e:
            # Catch any other unforeseen error during the attempt with this model.
            return f"An unforeseen error occurred with model {model_name}: {e}"

    return "Error: All specified models failed to provide a translation due to errors or rate limits."

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
    english_translation_1 = translate_chinese_to_english(chinese_text_1)
    print(f"Translated English text: {english_translation_1}")

    # Example 2: Specifying OpenRouter as the provider
    # Make sure API_KEY is set to your OpenRouter API key before running this.
    print("\n\n--- Example 2: Using OpenRouter provider ---")
    chinese_text_2 = "今天天气真好，适合出去走走。"
    print(f"Original Chinese text: {chinese_text_2}\n")
    print("Translating...")
    # Ensure OPENROUTER_API_KEY is set in your environment for this to work
    # Update: Ensure API_KEY is set to your OpenRouter key for this to work
    english_translation_2 = translate_chinese_to_english(chinese_text_2, api_provider_name="openrouter")
    print(f"Translated English text: {english_translation_2}")

    # Example 3: Testing with a non-configured provider
    print("\n\n--- Example 3: Testing non-configured provider ---")
    chinese_text_3 = "这是第三个测试。"
    print(f"Original Chinese text: {chinese_text_3}\n")
    print("Translating...")
    english_translation_3 = translate_chinese_to_english(chinese_text_3, api_provider_name="nonexistent_provider")
    print(f"Translated English text: {english_translation_3}")

