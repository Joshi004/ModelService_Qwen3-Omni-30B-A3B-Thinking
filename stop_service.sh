#!/bin/bash

# Qwen3-Omni Service Stop Script
# This script stops the vLLM server

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}Stopping Qwen3-Omni Service...${NC}"

# Stop video HTTP server
if [ -f /tmp/video_server.pid ]; then
    VIDEO_PID=$(cat /tmp/video_server.pid)
    if ps -p $VIDEO_PID > /dev/null 2>&1; then
        echo "Stopping video server (PID: $VIDEO_PID)..."
        kill -15 $VIDEO_PID 2>/dev/null || true
        rm -f /tmp/video_server.pid
    fi
fi

# Also kill any Python HTTP servers on port 8080
lsof -ti:8080 | xargs kill -9 2>/dev/null || true

# Find and kill vllm processes
VLLM_PIDS=$(pgrep -f "vllm serve")

if [ -z "$VLLM_PIDS" ]; then
    echo -e "${RED}No vLLM service found running.${NC}"
    exit 0
fi

echo "Found vLLM processes: $VLLM_PIDS"

for PID in $VLLM_PIDS; do
    echo "Stopping process $PID..."
    kill -15 "$PID"
done

echo -e "${GREEN}Waiting for graceful shutdown...${NC}"
sleep 5

# Force kill if still running
REMAINING_PIDS=$(pgrep -f "vllm serve")
if [ -n "$REMAINING_PIDS" ]; then
    echo -e "${RED}Force killing remaining processes...${NC}"
    for PID in $REMAINING_PIDS; do
        kill -9 "$PID"
    done
fi

echo -e "${GREEN}Service stopped successfully.${NC}"

