#!/bin/bash
# JarvisVLA Installation Script - Optimized for vLLM Serving
# This script installs all dependencies needed to serve JarvisVLA via vLLM
# with proper dependency resolution to avoid conflicts

set -e  # Exit on any error

echo "🚀 Starting JarvisVLA installation (optimized for vLLM serving)..."

# Install system dependencies
echo "📦 Installing system dependencies..."
apt-get update
apt-get install -y openjdk-8-jdk xvfb git curl wget

# Set up Java environment
echo "🔧 Setting up Java environment..."
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

# Make Java environment persistent
if ! grep -q "JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64" ~/.bashrc; then
    echo 'export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64' >> ~/.bashrc
    echo 'export PATH=$JAVA_HOME/bin:$PATH' >> ~/.bashrc
fi

# Step 1: Install vLLM first (critical for serving) - let pip resolve all dependencies
echo ""
echo "📦 Step 1/5: Installing vLLM and its dependencies..."
echo "   (This may take several minutes as it installs PyTorch and other large packages)"
pip install vllm==0.10.2

# Step 2: Install core ML libraries needed for inference
echo ""
echo "📦 Step 2/5: Installing core inference dependencies..."
# Use compatible versions that work with vllm's PyTorch
pip install transformers>=4.50.0 accelerate>=1.2.0 peft datasets trl
pip install qwen-vl-utils sentencepiece pillow numpy

# Step 3: Clone JarvisVLA and install it WITHOUT strict dependencies
echo ""
echo "📦 Step 3/5: Installing JarvisVLA..."
if [ ! -d "JarvisVLA" ]; then
    git clone https://github.com/CraftJarvis/JarvisVLA.git
fi
cd JarvisVLA

# Install JarvisVLA without enforcing its outdated requirements
# This allows the already-installed compatible versions to be used
pip install --no-deps -e .

# Step 4: Install minestudio for evaluation/simulation (optional for serving)
echo ""
echo "📦 Step 4/5: Installing minestudio (for evaluation)..."
# Install minestudio's dependencies carefully to avoid conflicts
pip install minestudio || {
    echo "⚠️  Warning: minestudio installation had issues, attempting manual install..."
    pip install --no-deps minestudio
    # Install only the critical minestudio dependencies
    pip install hydra-core omegaconf scipy lxml gymnasium
    pip install coloredlogs diskcache einops absl-py dm-tree wrapt
}

# Step 5: Install tunneling tools for public access
echo ""
echo "📦 Step 5/5: Installing tunneling tools (ngrok)..."
# Install ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null 2>&1
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | tee /etc/apt/sources.list.d/ngrok.list
apt-get update && apt-get install -y ngrok

# Go back to parent directory
cd ..

# Verification
echo ""
echo "✅ Verifying installation..."
echo "   Checking Java..."
java -version 2>&1 | head -n 1

echo "   Checking vLLM..."
python -c "import vllm; print(f'✓ vLLM {vllm.__version__} imported successfully')" 2>&1

echo "   Checking transformers..."
python -c "import transformers; print(f'✓ transformers {transformers.__version__} imported successfully')" 2>&1

echo "   Checking JarvisVLA..."
python -c "import jarvisvla; print('✓ JarvisVLA imported successfully')" 2>&1 || {
    echo "⚠️  Warning: JarvisVLA import failed, but vLLM can still serve the model"
}

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 QUICK START - Serve JarvisVLA:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1️⃣  Start the vLLM server:"
echo "   ./start_vllm_server.sh"
echo ""
echo "   Or manually:"
echo "   CUDA_VISIBLE_DEVICES=0 vllm serve CraftJarvis/JarvisVLA-Qwen2-VL-7B \\"
echo "       --port 8000 \\"
echo "       --max-model-len 8192 \\"
echo "       --trust-remote-code"
echo ""
echo "2️⃣  Expose to public internet via ngrok:"
echo "   # In a new terminal:"
echo "   ngrok http 8000"
echo ""
echo "   Or use the helper script:"
echo "   ./start_ngrok_tunnel.sh"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📚 Additional Info:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "• Model will auto-download from Hugging Face on first use"
echo "• API docs available at: http://localhost:8000/docs"
echo "• Compatible with OpenAI API format"
echo ""
echo "✨ Ready to serve JarvisVLA!"