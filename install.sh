#!/bin/bash
# Complete JarvisVLA Installation Script (No Conda Required!)
# This script installs OpenJDK 8, JarvisVLA, minestudio, vllm, and all dependencies
# for both Xvfb (headless) and VirtualGL rendering

set -e  # Exit on any error

echo "🚀 Starting JarvisVLA installation..."

# Install OpenJDK 8 via apt (no conda needed!)
echo "📦 Installing OpenJDK 8..."
apt update
apt install openjdk-8-jdk -y

# Install Xvfb for headless display support
echo "📦 Installing Xvfb for headless display..."
apt install -y xvfb

# Set environment variables
echo "🔧 Setting up environment variables..."
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

# Make JAVA_HOME persistent
echo 'export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64' >> ~/.bashrc
echo 'export PATH=$JAVA_HOME/bin:$PATH' >> ~/.bashrc

# Clone and install JarvisVLA
echo "📥 Cloning and installing JarvisVLA..."
git clone https://github.com/CraftJarvis/JarvisVLA.git
cd JarvisVLA
pip install --no-deps -e .

# Install compatible core dependencies
echo "📦 Installing core ML dependencies..."
pip install accelerate==1.4.0 peft==0.14.0 trl==0.18.2
pip install av==14.1.0 rich wandb openai opencv-python opencv-python-headless

# Install minestudio dependencies
echo "📦 Installing minestudio and dependencies..."
pip install minestudio --no-deps
pip install hydra-core omegaconf scipy lxml gym gymnasium
pip install absl-py dm-tree einops coloredlogs diskcache
pip install gym3 minecraft_data==3.20.0 pyglet pyopengl daemoniker
pip install Pyro4 xmltodict typing lmdb

# Install vllm and inference dependencies
echo "📦 Installing vllm for inference..."
pip install vllm --no-deps
pip install ray sentencepiece==0.2.0 qwen-vl-utils

# Install all missing VLLM dependencies
echo "📦 Installing VLLM dependencies..."
pip install cachetools blake3 cbor2 compressed-tensors==0.11.0 depyf==0.19.0 
pip install "fastapi[standard]>=0.115.0" gguf>=0.13.0 lark==1.2.2 llguidance==0.7.30
pip install lm-format-enforcer==0.11.3 mistral_common msgspec ninja numba==0.61.2
pip install openai-harmony>=0.0.3 outlines_core==0.2.11 partial-json-parser
pip install prometheus-fastapi-instrumentator>=7.0.0 py-cpuinfo pybase64 setproctitle
pip install tiktoken>=0.6.0 watchfiles xformers==0.0.32.post1 xgrammar==0.1.23

# Install correct PyTorch versions for VLLM compatibility
echo "📦 Installing compatible PyTorch versions..."
pip install torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu128

# Install tunneling tools (ngrok and localtunnel)
echo "📦 Installing tunneling tools..."
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | tee /etc/apt/sources.list.d/ngrok.list
apt update && apt install ngrok -y
curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && apt-get install -y nodejs
npm install -g localtunnel

# Download the JarvisVLA model
echo "📥 Downloading JarvisVLA model..."
python download_model.py

# Verify installation
echo "✅ Verifying installation..."
java -version
python -c "import jarvisvla; print('JarvisVLA imported successfully!')"
python -c "import vllm; print('VLLM imported successfully!')"
python -c "import minestudio; print('Minestudio imported successfully!')"

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "📋 Available commands:"
echo "  # Test minestudio simulator with Xvfb (headless):"
echo "  python -m minestudio.simulator.entry"
echo ""
echo "  # Test minestudio simulator with VirtualGL (GPU rendering):"
echo "  MINESTUDIO_GPU_RENDER=1 python -m minestudio.simulator.entry"
echo ""
echo "  # Download the model first:"
echo "  python download_model.py"
echo ""
echo "  # Serve model with vllm for inference (local path):"
echo "  CUDA_VISIBLE_DEVICES=0 vllm serve ./models/JarvisVLA-Qwen2-VL-7B --port 8000 --max-model-len 8192"
echo ""
echo "  # Or serve directly from Hugging Face (will auto-download):"
echo "  CUDA_VISIBLE_DEVICES=0 vllm serve CraftJarvis/JarvisVLA-Qwen2-VL-7B --port 8000 --max-model-len 8192"
echo ""
echo "  # Create public HTTPS tunnel (choose one):"
echo "  ./start_ngrok_tunnel.sh     # ngrok (requires domain setup)"
echo "  ./start_localtunnel.sh      # LocalTunnel (easier setup)"
echo ""
echo "  # Or start everything with public access:"
echo "  ./start_jarvis_public.sh"
echo ""
echo "✨ JarvisVLA is ready for inference!"