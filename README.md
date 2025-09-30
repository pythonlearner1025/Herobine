# 🎮 JarvisVLA Server Setup

**Serve JarvisVLA (Minecraft AI) via vLLM with public ngrok access**

This repository provides a **one-shot installation script** to serve the [JarvisVLA](https://github.com/CraftJarvis/JarvisVLA) vision-language-action model using vLLM, with proper dependency resolution to avoid the common "dependency hell" issues.

## 🚀 Quick Start (3 Commands)

```bash
# 1. Install everything (15-20 minutes)
sudo ./install.sh

# 2. Verify installation
./verify_installation.sh

# 3. Start serving
./start_vllm_server.sh
```

That's it! The model will auto-download on first use and start serving on port 8000.

## 📋 What This Does

✅ Installs vLLM with proper PyTorch dependencies  
✅ Installs JarvisVLA package (without dependency conflicts)  
✅ Installs Minecraft simulation environment (minestudio)  
✅ Configures OpenJDK 8 for Minecraft  
✅ Sets up ngrok for public HTTPS tunneling  
✅ Provides ready-to-use serving scripts  

## 🎯 Use Cases

- **Run inference** on JarvisVLA for Minecraft tasks
- **Expose local GPU** as a cloud API via ngrok
- **Test vision-language models** without complex setup
- **Deploy on VM** without SSL certificate hassles

## 📚 Documentation

- **[INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)** - Comprehensive setup guide, troubleshooting
- **[CHANGES_SUMMARY.md](CHANGES_SUMMARY.md)** - Technical details on how we fixed dependency hell
- **[verify_installation.sh](verify_installation.sh)** - Quick health check script

## 🔧 Key Features

### 1. Proper Dependency Resolution
Unlike naive installation approaches, this script:
- Installs vLLM first (with full dependency resolution)
- Lets modern compatible versions coexist
- Skips training-only dependencies for serving

### 2. Flexible Configuration
```bash
# Custom GPU
CUDA_VISIBLE_DEVICES=1 ./start_vllm_server.sh

# Custom port
PORT=8080 ./start_vllm_server.sh

# Static ngrok domain
export NGROK_DOMAIN=your-domain.ngrok-free.dev
./start_ngrok_tunnel.sh
```

### 3. OpenAI-Compatible API
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy"
)

response = client.chat.completions.create(
    model="JarvisVLA-Qwen2-VL-7B",
    messages=[{"role": "user", "content": "Mine diamond ore"}]
)
```

## 🛠️ System Requirements

- **OS:** Ubuntu 20.04+ / Debian 11+
- **GPU:** NVIDIA GPU with 16GB+ VRAM (for 7B model)
- **RAM:** 32GB+ recommended
- **CUDA:** 11.8 or 12.x
- **Disk:** 20GB+ free space

## 📖 Usage Examples

### Start Server Locally
```bash
./start_vllm_server.sh
# Server at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Expose Publicly via ngrok
```bash
# Terminal 1
./start_vllm_server.sh

# Terminal 2 (after server starts)
./start_ngrok_tunnel.sh
# Copy the public URL (e.g., https://xyz.ngrok-free.dev)
```

### Test API
```bash
curl http://localhost:8000/health
curl http://localhost:8000/v1/models

# Or visit in browser:
# http://localhost:8000/docs
```

## 🐛 Troubleshooting

### Installation fails with dependency conflicts
```bash
# Clean pip cache and retry
pip cache purge
sudo ./install.sh
```

### CUDA out of memory
```bash
# Reduce max sequence length
MAX_MODEL_LEN=4096 ./start_vllm_server.sh
```

### vLLM server won't start
```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Check vLLM
python -c "import vllm; print('OK')"
```

See [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) for detailed troubleshooting.

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         Public Internet                 │
│  https://your-domain.ngrok-free.dev     │
└───────────────┬─────────────────────────┘
                │ ngrok tunnel
┌───────────────▼─────────────────────────┐
│      Your VM / Local Machine            │
│                                          │
│  ┌────────────────────────────────┐     │
│  │   vLLM Server (Port 8000)      │     │
│  │   - OpenAI-compatible API      │     │
│  │   - JarvisVLA-Qwen2-VL-7B      │     │
│  └────────────────────────────────┘     │
│                                          │
│  ┌────────────────────────────────┐     │
│  │   GPU (CUDA)                   │     │
│  │   - Model inference            │     │
│  │   - xformers optimization      │     │
│  └────────────────────────────────┘     │
└──────────────────────────────────────────┘
```

## 📦 What Gets Installed

### Core Components
- **vLLM 0.10.2** - High-performance inference server
- **PyTorch 2.8.0** - With CUDA support
- **transformers** - HuggingFace model loading
- **JarvisVLA** - Vision-language-action model

### Supporting Libraries
- **xformers** - Attention kernel optimizations
- **qwen-vl-utils** - Vision-language processing
- **minestudio** - Minecraft simulation (optional for serving)

### Tools
- **ngrok** - HTTPS tunneling
- **OpenJDK 8** - For Minecraft simulation

## 🔐 Security Notes

- vLLM server has no authentication by default (local use)
- Use ngrok authentication for public endpoints
- Don't expose sensitive data through the API
- Consider firewall rules for production

## 🤝 Contributing

Issues and PRs welcome! Key areas:
- Multi-GPU support scripts
- Docker containerization
- Better error handling
- Cloud deployment guides

## 📄 License

See individual component licenses:
- JarvisVLA: MIT License
- vLLM: Apache 2.0
- This setup: MIT License

## 🙏 Credits

- [JarvisVLA Team](https://github.com/CraftJarvis/JarvisVLA) - Original model
- [vLLM Team](https://github.com/vllm-project/vllm) - Inference engine
- [ngrok](https://ngrok.com/) - Tunneling service

## 📞 Support

- **Installation issues**: Check [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)
- **Dependency conflicts**: See [CHANGES_SUMMARY.md](CHANGES_SUMMARY.md)
- **vLLM issues**: [vLLM Documentation](https://docs.vllm.ai/)
- **JarvisVLA issues**: [JarvisVLA GitHub](https://github.com/CraftJarvis/JarvisVLA)

---

**Ready to serve JarvisVLA in under 20 minutes!** 🚀

Run `./install.sh` to get started.