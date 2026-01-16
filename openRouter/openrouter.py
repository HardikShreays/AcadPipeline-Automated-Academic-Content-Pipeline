import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def call_openrouter(
    message: str,
    model: str = "tngtech/deepseek-r1t2-chimera:free",
    api_key: str = None,
    system_prompt: str = None,
    **kwargs
) -> str:
    """
    Call OpenRouter API to get a chat completion response.
    
    Args:
        message: The user message to send
        model: The model to use (default: "tngtech/deepseek-r1t2-chimera:free")
        api_key: OpenRouter API key (defaults to OPENROUTER_KEY env var)
        system_prompt: Optional system prompt
        **kwargs: Additional parameters to pass to the API (temperature, max_tokens, etc.)
    
    Returns:
        str: The response content from the model
    
    Raises:
        ValueError: If API key is not found
        requests.RequestException: If the API request fails
    """
    # Get API key from parameter or environment
    if api_key is None:
        api_key = os.getenv('OPENROUTER_KEY')
    
    if not api_key:
        raise ValueError("OPENROUTER_KEY not found in environment variables. Please check your .env file.")
    
    # Build messages array
    messages = []
    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })
    messages.append({
        "role": "user",
        "content": message
    })
    
    # Prepare request payload
    payload = {
        "model": model,
        "messages": messages,
        **kwargs  # Allow additional parameters like temperature, max_tokens, etc.
    }
    
    # Make the API request
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            # Optional. Site title for rankings on openrouter.ai.
            # "HTTP-Referer": "https://your-site.com",
            # "X-Title": "Your Site Name",
        },
        json=payload
    )
    
    # Check if request was successful
    response.raise_for_status()
    
    # Parse and extract the response
    result = response.json()
    
    if 'choices' in result and len(result['choices']) > 0:
        return result['choices'][0]['message']['content']
    else:
        raise ValueError("No response content found in API response")


# Example usage (for testing)
if __name__ == "__main__":
    response = call_openrouter("What is the meaning of life?")
    print(response)