# JarvisVLA Setup Guide (No Conda Required!)

This guide helps you install and run JarvisVLA with public HTTPS access using either ngrok or LocalTunnel.

## 🚀 Quick Start

### 1. Complete Installation
```bash
# Run the complete installation script
bash install.sh
```

### 2. Start JarvisVLA Server
```bash
# Start the vLLM server locally
./start_vllm_server.sh
```

## 📋 What's Installed

### Core Components
- ✅ **OpenJDK 8** (via apt, no conda!)
- ✅ **JarvisVLA** (CraftJarvis/JarvisVLA-Qwen2-VL-7B model)
- ✅ **vLLM** (for model serving)
- ✅ **Minestudio** (for Minecraft simulation)
- ✅ **Xvfb** (headless display support)

### Tunneling Tools
- ✅ **ngrok** (authenticated with your token)
- ✅ **LocalTunnel** (Node.js based alternative)

### Model Details
- **Model**: [CraftJarvis/JarvisVLA-Qwen2-VL-7B](https://huggingface.co/CraftJarvis/JarvisVLA-Qwen2-VL-7B)
- **Size**: ~16.6 GB
- **Architecture**: Qwen2VLForConditionalGeneration
- **Location**: `./models/JarvisVLA-Qwen2-VL-7B/`

## 🧪 Testing Commands

### Test Minestudio Simulator
```bash
# Test with Xvfb (headless)
python -m minestudio.simulator.entry

# Test with VirtualGL (GPU rendering)
MINESTUDIO_GPU_RENDER=1 python -m minestudio.simulator.entry
```

### Test vLLM Server
```bash
# Test the API server
python test_vllm_serve.py
```

### Test Model Imports
```bash
python -c "import jarvisvla, vllm, minestudio; print('✅ All packages working!')"
```

## 🔧 Configuration

### Environment Variables
- `PORT`: Server port (default: 8000)
- `MAX_MODEL_LEN`: Maximum model length (default: 8192)
- `CUDA_VISIBLE_DEVICES`: GPU selection (default: 0)

### Example with Custom Settings
```bash
# Start with custom settings
PORT=9000 MAX_MODEL_LEN=4096 CUDA_VISIBLE_DEVICES=1 ./start_vllm_server.sh
```

## 🌐 API Access

Once the tunnel is running, you'll get a public HTTPS URL like:
- **LocalTunnel**: `https://random-words.loca.lt`
- **ngrok**: `https://your-domain.ngrok-free.app`

### API Endpoints
- **Chat Completions**: `POST /v1/chat/completions`
- **Models**: `GET /v1/models`
- **Health**: `GET /health`
- **API Docs**: `GET /docs`

### Example API Request
```bash
curl -X POST "https://unexaggerative-dilan-alphanumerically.ngrok-free.dev/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "JarvisVLA-Qwen2-VL-7B",
    "messages": [
      {"role": "user", "content": "Describe what you see in this Minecraft world."}
    ],
    "max_tokens": 100
  }'
```
