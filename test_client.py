#!/usr/bin/env python3
"""
Qwen3-Omni Service Test Client

This script tests the vLLM service with video URLs and prompts.
It demonstrates how to interact with the Qwen3-Omni model via the OpenAI-compatible API.
"""

import json
import re
import requests
import sys
from typing import Optional


def remove_thinking_tags(text: str) -> str:
    """
    Remove thinking/reasoning tags from the model output.
    
    This function strips out common thinking patterns like:
    - <think>...</think>
    - <reasoning>...</reasoning>
    - Content before "Answer:" or similar markers
    
    Args:
        text: Raw output from the model
        
    Returns:
        str: Cleaned text with only the final answer
    """
    # Pattern 1: Remove <think>...</think> tags
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Pattern 2: Remove <reasoning>...</reasoning> tags
    text = re.sub(r'<reasoning>.*?</reasoning>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Pattern 3: Extract content after "Answer:" or "Final Answer:" markers
    answer_match = re.search(r'(?:Final\s+)?Answer\s*:\s*(.*)', text, flags=re.DOTALL | re.IGNORECASE)
    if answer_match:
        text = answer_match.group(1)
    
    # Pattern 4: Remove markdown code blocks with "thinking" label
    text = re.sub(r'```thinking.*?```', '', text, flags=re.DOTALL)
    
    # Clean up extra whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = text.strip()
    
    return text


def test_service(
    video_url: str,
    prompt: str,
    base_url: str = "http://localhost:8002",
    temperature: float = 0.6,
    top_p: float = 0.95,
    top_k: int = 20,
    max_tokens: int = 16384,
    strip_thinking: bool = True,
):
    """
    Test the Qwen3-Omni service with a video URL and prompt.
    
    Args:
        video_url: URL to the video file
        prompt: Text prompt for the model
        base_url: Base URL of the vLLM service
        temperature: Sampling temperature
        top_p: Top-p sampling parameter
        top_k: Top-k sampling parameter
        max_tokens: Maximum tokens to generate
        strip_thinking: Whether to remove thinking/reasoning tags from output
    
    Returns:
        dict: Response from the service
    """
    
    # Construct the API endpoint
    api_url = f"{base_url}/v1/chat/completions"
    
    # Prepare the request payload
    payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "video_url", "video_url": {"url": video_url}},
                    {"type": "text", "text": prompt}
                ]
            }
        ],
        "temperature": temperature,
        "top_p": top_p,
        "top_k": top_k,
        "max_tokens": max_tokens,
    }
    
    print(f"🔄 Sending request to {api_url}")
    print(f"📹 Video URL: {video_url}")
    print(f"💬 Prompt: {prompt}")
    print("-" * 80)
    
    try:
        # Send POST request
        response = requests.post(
            api_url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=300  # 5 minute timeout for longer videos
        )
        
        response.raise_for_status()
        
        # Parse response
        result = response.json()
        
        # Extract generated text
        if "choices" in result and len(result["choices"]) > 0:
            generated_text = result["choices"][0]["message"]["content"]
            
            # Store raw output
            raw_output = generated_text
            
            # Optionally strip thinking tags
            if strip_thinking:
                generated_text = remove_thinking_tags(generated_text)
                print("✅ Response received! (Thinking tags removed)")
            else:
                print("✅ Response received! (Raw output with thinking)")
            
            print("-" * 80)
            print("📝 Generated Caption:")
            print(generated_text)
            print("-" * 80)
            
            # Print usage stats if available
            if "usage" in result:
                print(f"📊 Usage Stats:")
                print(f"   Prompt tokens: {result['usage'].get('prompt_tokens', 'N/A')}")
                print(f"   Completion tokens: {result['usage'].get('completion_tokens', 'N/A')}")
                print(f"   Total tokens: {result['usage'].get('total_tokens', 'N/A')}")
                
                # Show token savings if thinking was stripped
                if strip_thinking and raw_output != generated_text:
                    raw_tokens = len(raw_output.split())  # Rough estimate
                    clean_tokens = len(generated_text.split())
                    saved_tokens = raw_tokens - clean_tokens
                    print(f"   💡 Estimated tokens saved: ~{saved_tokens} (by removing thinking)")
            
            return {
                "success": True,
                "response": generated_text,
                "raw_response": raw_output,
                "full_response": result
            }
        else:
            print("❌ Unexpected response format")
            print(json.dumps(result, indent=2))
            return {"success": False, "error": "Unexpected response format"}
            
    except requests.exceptions.Timeout:
        error_msg = "Request timed out after 5 minutes"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}
    
    except requests.exceptions.ConnectionError:
        error_msg = f"Failed to connect to {base_url}. Is the service running?"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}
    
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP error: {e.response.status_code} - {e.response.text}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}
    
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}


def main():
    """Main function to run example tests"""
    
    print("=" * 80)
    print("Qwen3-Omni Service Test Client")
    print("=" * 80)
    print()
    
    # Example 1: Test with a sample video URL
    # Replace with your actual video URL
    example_video_url = "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen3-Omni/demo/draw.mp4"
    example_prompt = "Describe this video in detail, including the visual content and any audio you can hear."
    
    print("📝 Example Test:")
    print(f"   Video: {example_video_url}")
    print(f"   Prompt: {example_prompt}")
    print()
    
    # Check if custom arguments provided
    if len(sys.argv) >= 3:
        video_url = sys.argv[1]
        prompt = sys.argv[2]
        print("Using custom input from command line arguments")
    else:
        video_url = example_video_url
        prompt = example_prompt
        print("Using example video and prompt (no command line args provided)")
        print("Usage: python test_client.py <video_url> <prompt>")
    
    print()
    
    # Run the test
    result = test_service(video_url, prompt)
    
    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()








