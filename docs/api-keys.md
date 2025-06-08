# API Key Setup Guide

This document provides detailed instructions on how to obtain API keys for the supported translation providers in the Novel Translation Pipeline.

## Overview

The Novel Translation Pipeline supports two main API providers:
- **OpenRouter** - A unified API for multiple AI models
- **Chutes** - A decentralized AI compute platform

Both providers require API keys for authentication. This guide will walk you through the process of obtaining these keys.

---

## OpenRouter API Key

[OpenRouter](https://openrouter.ai/) provides access to multiple AI models through a unified API, making it easy to switch between different models and providers.

### Step 1: Create an OpenRouter Account

1. Navigate to [OpenRouter.ai](https://openrouter.ai/)
2. Click on "Sign up with email/wallet" or "Login" if you already have an account
3. Complete the registration process with your email address

### Step 2: Access API Keys Section

1. Once logged in, look for "Keys" in the navigation menu or user dashboard
2. Click on "Keys" to access the API key management page

### Step 3: Create a New API Key

1. Click the "Create Key" button
2. In the popup window, provide a descriptive name for your API key (e.g., "Novel Translation")
3. Optionally, you can set a credit limit for the key to control spending
4. Click "Create" to generate the key

### Step 4: Save Your API Key

1. **Important**: Copy the generated API key immediately and store it securely
2. You won't be able to retrieve the full key later for security reasons
3. Keep this key confidential and never commit it to public repositories

### Step 5: Set Environment Variable

Set the API key as an environment variable:

```bash
export API_KEY="sk-or-v1-your-openrouter-api-key-here"
```

To make this permanent, add it to your shell configuration file (e.g., `~/.bashrc`, `~/.zshrc`):

```bash
echo 'export API_KEY="sk-or-v1-your-openrouter-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

---

## Chutes API Key

[Chutes](https://chutes.ai/) is a serverless AI compute platform that provides decentralized access to AI models through a simple web interface.

### Step 1: Create a Chutes Account

1. Navigate to [chutes.ai/app](https://chutes.ai/app)
2. Click on "Create an Account" or "Log In" if you already have an account
3. Complete the registration process

### Step 2: Access API Section

1. Once logged in to the Chutes dashboard, look for "API" in the navigation menu
2. Click on "API" to access the API management section

### Step 3: Get Your API Key

1. In the API section, look for "Get API Key" button or link
2. Click on it to generate or view your API key
3. Your API key will be displayed and can be copied

**Note**: According to the [Chutes documentation](https://chutes.ai/app/docs), you can run AI models through their API without worrying about infrastructure setup.

### Step 4: Save Your API Key

1. **Important**: Copy the generated API key immediately and store it securely
2. Chutes API keys typically start with `cpk_` followed by the key string
3. Keep this key confidential and never commit it to public repositories

### Step 5: Set Environment Variable

Set the Chutes API key as an environment variable:

```bash
export API_KEY="cpk-your-chutes-api-key-here"
```

To make this permanent:

```bash
echo 'export API_KEY="cpk-your-chutes-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

---

## Validation and Testing

Once you have set up your API key, you can validate your configuration using the translation pipeline's built-in validation:

```bash
# Validate OpenRouter configuration
python tool.py validate -p openrouter

# Validate Chutes configuration  
python tool.py validate -p chutes
```

The validation will check:
- ✅ API key environment variable is set and not empty
- ✅ Provider configuration exists and is valid  
- ✅ API connectivity with a simple test call
- ✅ Clear error messages with specific fix guidance

---

## Troubleshooting

### Common Issues

1. **"API key not set" error**
   ```bash
   # Check if the environment variable is set
   echo $API_KEY
   
   # If empty, set it again
   export API_KEY="your-api-key-here"
   ```

2. **"API connectivity test failed"**
   - Verify your internet connection
   - Check if the API key is valid and has sufficient credits
   - Ensure the API service is not experiencing downtime

3. **"Unknown API provider" error**
   - Use valid provider names: `chutes` or `openrouter`
   - Check for typos in the provider name

4. **Permission denied errors**
   - For OpenRouter: Ensure your key has sufficient credits
   - For Chutes: Make sure your account is properly set up on the web platform

### Getting Help

If you encounter issues:

1. **Check the validation output**: Run `python tool.py validate -p <provider>` for detailed error information
2. **Review API provider documentation**: 
   - [OpenRouter Docs](https://openrouter.ai/docs)
   - [Chutes Documentation](https://chutes.ai/app/docs)
3. **Check API status pages** for service outages
4. **Verify your account** has sufficient credits/permissions

---

## Cost Considerations

### OpenRouter
- Pricing varies by model used
- Check [OpenRouter pricing](https://openrouter.ai/models) for specific model costs
- Set credit limits to control spending
- Monitor usage through the dashboard

### Chutes
- Uses a serverless compute model with pay-per-use pricing
- Check current rates on the [Chutes platform](https://chutes.ai/app)
- Monitor usage through the web dashboard
- Offers various AI models including LLMs, image generation, and more

---

## Next Steps

After successfully setting up your API key:

1. **Validate your setup**: `python tool.py validate -p <provider>`
2. **Start with a small test**: Try translating a few chapters first
3. **Monitor your usage**: Keep track of API calls and costs
4. **Scale up gradually**: Increase worker count and batch sizes as needed

For more information on using the translation pipeline, see the main [README.md](../README.md). 