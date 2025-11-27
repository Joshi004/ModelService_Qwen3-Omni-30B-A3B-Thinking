# Qwen3-Omni Service

A production-ready service for running the Qwen3-Omni-30B-A3B-Thinking model using vLLM's built-in API server.

## Overview

This service deploys the Qwen3-Omni-30B-A3B-Thinking model, a state-of-the-art multimodal model capable of understanding text, images, audio, and video, with chain-of-thought reasoning capabilities.

### Model Information
- **Model**: Qwen3-Omni-30B-A3B-Thinking
- **Location**: `/home/naresh/models/qwen3-omni-30b/`
- **Capabilities**: Text, audio, image, and video understanding with text output
- **Features**: Chain-of-thought reasoning, multilingual support

### Hardware Configuration
- **GPUs**: 2x NVIDIA H100 (80GB each)
- **Tensor Parallelism**: Enabled across both GPUs
- **Total GPU Memory**: 160GB

## Quick Start

### 1. Start the Service

```bash
cd /home/naresh/qwen3-omni-service
./start_service.sh
```

The startup script will automatically start two services:

**Video HTTP Server (Port 8080)**
- Serves video files from `/home/naresh/datasets/videos`
- Runs in background mode
- Video URLs: `http://localhost:8080/<filename>.mp4`

**vLLM Model Server (Port 8002)**
- Max model length: 32,768 tokens (~60s videos)
- GPU memory utilization: 95%
- Tensor parallel size: 2 (both GPUs)
- Max concurrent sequences: 8

### 2. Test the Service

#### Using Local Videos

If you have videos in `/home/naresh/datasets/videos/`:

```bash
# Test with a local video file (e.g., 1.mp4)
python test_client.py "http://localhost:8080/1.mp4" "Describe this video in detail."

# Or use curl
curl http://localhost:8002/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{
      "role": "user",
      "content": [
        {"type": "video_url", "video_url": {"url": "http://localhost:8080/1.mp4"}},
        {"type": "text", "text": "Describe this video and analyze the audio."}
      ]
    }],
    "temperature": 0.6,
    "top_p": 0.95,
    "top_k": 20,
    "max_tokens": 16384
  }'
```

#### Using Remote Videos

```bash
# Using the built-in example
python test_client.py

# Or with your own video URL and prompt
python test_client.py "https://example.com/video.mp4" "Describe this video in detail."
```

### 3. Stop the Service

```bash
./stop_service.sh
```

## SSH Tunneling (Local Access)

To access the service from your local machine via SSH tunnel:

### Setup SSH Tunnel

```bash
# From your local machine - tunnel both services
ssh -L 8002:localhost:8002 -L 8080:localhost:8080 user@remote-server

# Keep this terminal open while using the service
```

Now you can access:
- **Model service**: `http://localhost:8002` from your local machine
- **Video files**: `http://localhost:8080/<filename>.mp4` from your local machine

### Test from Local Machine

```bash
# Example curl request
curl http://localhost:8002/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{
      "role": "user",
      "content": [
        {"type": "video_url", "video_url": {"url": "https://example.com/video.mp4"}},
        {"type": "text", "text": "Describe this video and analyze the audio track in detail."}
      ]
    }],
    "temperature": 0.6,
    "top_p": 0.95,
    "top_k": 20,
    "max_tokens": 16384
  }'
```

## API Usage

### Endpoint

```
POST http://localhost:8002/v1/chat/completions
```

### Request Format

The service provides an OpenAI-compatible API. Here's a complete example:

```json
{
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "video_url",
          "video_url": {
            "url": "https://example.com/video.mp4"
          }
        },
        {
          "type": "text",
          "text": "Describe this video in detail, including both visual and audio content."
        }
      ]
    }
  ],
  "temperature": 0.6,
  "top_p": 0.95,
  "top_k": 20,
  "max_tokens": 16384
}
```

### Supported Input Types

1. **Video with Audio** (Recommended for this use case)
   ```json
   {"type": "video_url", "video_url": {"url": "https://..."}}
   ```

2. **Image**
   ```json
   {"type": "image_url", "image_url": {"url": "https://..."}}
   ```

3. **Audio**
   ```json
   {"type": "audio_url", "audio_url": {"url": "https://..."}}
   ```

4. **Text**
   ```json
   {"type": "text", "text": "Your prompt here"}
   ```

### Response Format

```json
{
  "id": "cmpl-...",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "/home/naresh/models/qwen3-omni-30b",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Detailed caption and analysis of the video..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 500,
    "total_tokens": 650
  }
}
```

## Python Client Example

```python
import requests
import json

def analyze_video(video_url, prompt, base_url="http://localhost:8002"):
    """Analyze a video using the Qwen3-Omni service."""
    
    response = requests.post(
        f"{base_url}/v1/chat/completions",
        headers={"Content-Type": "application/json"},
        json={
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "video_url", "video_url": {"url": video_url}},
                    {"type": "text", "text": prompt}
                ]
            }],
            "temperature": 0.6,
            "top_p": 0.95,
            "top_k": 20,
            "max_tokens": 16384
        }
    )
    
    response.raise_for_status()
    result = response.json()
    return result["choices"][0]["message"]["content"]

# Usage
caption = analyze_video(
    "https://example.com/video.mp4",
    "Describe this video in detail, including both visual and audio content."
)
print(caption)
```

## Configuration

### Environment Variables

Located in `config.env`:

```bash
# Required for Qwen3-Omni compatibility
export VLLM_USE_V1=0

# Model settings
MODEL_PATH="/home/naresh/models/qwen3-omni-30b"
PORT=8002
DTYPE="bfloat16"

# Performance
MAX_MODEL_LEN=32768      # 32768 for ~60s videos, 65536 for ~120s videos
TENSOR_PARALLEL_SIZE=2   # Number of GPUs
GPU_MEMORY_UTIL=0.95     # GPU memory utilization
MAX_NUM_SEQS=8          # Concurrent sequences

# Generation
TEMPERATURE=0.6
TOP_P=0.95
TOP_K=20
MAX_TOKENS=16384
```

### Adjusting for Longer Videos

For videos longer than 60 seconds, edit `start_service.sh` and change:

```bash
MAX_MODEL_LEN=65536  # For videos up to 120s
```

## Service Management

### Check Service Status

```bash
# Check if service is running
curl http://localhost:8002/health

# Check vLLM processes
ps aux | grep vllm
```

### View Logs

When starting the service, logs will be displayed in the terminal. For background execution:

```bash
# Start in background and redirect logs
nohup ./start_service.sh > service.log 2>&1 &

# View logs
tail -f service.log
```

### GPU Monitoring

```bash
# Monitor GPU usage
watch -n 1 nvidia-smi

# Or use
nvtop  # If installed
```

## Troubleshooting

### Service Won't Start

1. **Check GPU availability**
   ```bash
   nvidia-smi
   ```

2. **Verify virtual environment**
   ```bash
   source /home/naresh/venvs/qwen3-omni-service/bin/activate
   which vllm
   ```

3. **Check model path**
   ```bash
   ls -la /home/naresh/models/qwen3-omni-30b/
   ```

### Out of Memory Errors

1. Reduce `MAX_MODEL_LEN` for shorter videos
2. Reduce `GPU_MEMORY_UTIL` to 0.90
3. Reduce `MAX_NUM_SEQS` to 4

### Connection Refused

1. Ensure service is running: `ps aux | grep vllm`
2. Check port availability: `netstat -tuln | grep 8002`
3. Verify SSH tunnel is active (if accessing remotely)

## Performance Tips

1. **Optimal Video Length**: Best performance with videos under 60 seconds
2. **Batch Processing**: Process multiple videos sequentially rather than concurrently
3. **GPU Utilization**: Monitor with `nvidia-smi` to ensure both GPUs are utilized
4. **Prompt Engineering**: Clear, specific prompts yield better results

## Model Capabilities

### Thinking Model Features

- **Chain-of-Thought Reasoning**: The model uses internal reasoning before generating answers
- **Multimodal Understanding**: Processes video frames and audio simultaneously
- **Detailed Analysis**: Provides comprehensive captions including:
  - Visual content description
  - Audio track analysis
  - Temporal relationships
  - Context understanding

### Best Practices for Prompts

Good prompt examples:
```
"Describe this video in detail, including both visual and audio content."
"What is happening in this video? Analyze the scene and any sounds you hear."
"Provide a comprehensive caption for this video, covering all important details."
```

## Directory Structure

```
qwen3-omni-service/
├── start_service.sh      # Start the vLLM server
├── stop_service.sh       # Stop the service
├── config.env           # Configuration variables
├── test_client.py       # Test client script
└── README.md           # This file
```

## Dependencies

Installed in virtual environment at `/home/naresh/venvs/qwen3-omni-service/`:

- vLLM (Qwen3-Omni branch)
- PyTorch 2.7.0
- Transformers (from source)
- accelerate
- qwen-omni-utils
- Other dependencies (see requirements)

## Support

For issues related to:
- **Model**: See [Qwen3-Omni GitHub](https://github.com/QwenLM/Qwen3-Omni)
- **vLLM**: See [vLLM Documentation](https://docs.vllm.ai/)
- **Service Configuration**: Check logs and GPU status

## License

The Qwen3-Omni model is licensed under Apache 2.0. See the model repository for details.

---

**Note**: This is a production deployment. Always monitor GPU usage and service logs for optimal performance.

