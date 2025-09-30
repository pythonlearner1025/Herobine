# MineRL Server Setup Guide

## System Requirements

### Server (Remote Machine)

✅ **Operating System:** Linux (Ubuntu 20.04+)  
✅ **Java:** OpenJDK 8 (REQUIRED - installed and verified)  
✅ **Python:** 3.10+  
✅ **MineStudio:** Installed with MineRL support  
✅ **GPU:** Recommended for rendering (or use Xvfb for CPU rendering)  
✅ **Ports:** 6666 (or custom) for interactive mode  

### Client (Your Local Computer)

- **Python 3.10+**
- **MineStudio** (`pip install minestudio`)
- **OpenJDK 8** (for Minecraft client)
- **Port forwarding** via SSH

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  YOUR LOCAL COMPUTER                                         │
│                                                              │
│  ┌───────────────────────────────────────────────┐          │
│  │  Minecraft Client (Interactor)                │          │
│  │  - Connects via port forwarding               │          │
│  │  - See agent's first-person POV               │          │
│  │  - Spectate or interact in real-time          │          │
│  └───────────────┬───────────────────────────────┘          │
│                  │                                           │
│                  │ SSH Port Forward (6666)                   │
└──────────────────┼───────────────────────────────────────────┘
                   │
                   │
┌──────────────────▼───────────────────────────────────────────┐
│  REMOTE SERVER                                               │
│                                                              │
│  ┌────────────────────────────────────────────────┐         │
│  │  MineRL Agent Server (server_minerl.py)        │         │
│  │  - JarvisVLA agent running                     │         │
│  │  - Proper POV with hands/HUD                   │         │
│  │  - Interactive mode on port 6666               │         │
│  └────────────────────────────────────────────────┘         │
│                                                              │
│  ┌────────────────────────────────────────────────┐         │
│  │  Minecraft 1.16.5 + Malmo                      │         │
│  │  - Rendering with real Minecraft client        │         │
│  │  - World simulation                            │         │
│  └────────────────────────────────────────────────┘         │
│                                                              │
│  ┌────────────────────────────────────────────────┐         │
│  │  VLLM Server (port 8000)                       │         │
│  │  - JarvisVLA inference                         │         │
│  └────────────────────────────────────────────────┘         │
└──────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### 1. Verify System Requirements

```bash
cd /workspace/Herobine/minerl_server

# Check Java (MUST be version 8)
java -version
# Should show: openjdk version "1.8.0_xxx"

# Check MineStudio
python -c "import minestudio; print('✓ MineStudio OK')"

# Check MineRL module
python -c "from minestudio.simulator.minerl import interactor; print('✓ MineRL OK')"
```

### 2. Test Basic Rendering (No Agent)

```bash
# Test that Minecraft can render
xvfb-run python -m minestudio.simulator.entry

# If you have NVIDIA GPU, use VirtualGL (faster):
MINESTUDIO_GPU_RENDER=1 python -m minestudio.simulator.entry
```

### 3. Start VLLM Server (If Not Running)

```bash
# Terminal 1 - Start VLLM
cd /workspace/Herobine
./start_vllm_server.sh

# Wait for: "Uvicorn running on http://0.0.0.0:8000"
```

### 4. Run Agent Server WITHOUT Interactive Mode

```bash
# Terminal 2 - Basic agent test
cd /workspace/Herobine/minerl_server

python server_minerl.py \
  --checkpoint /path/to/jarvis_vla_checkpoint \
  --vllm-url http://localhost:8000/v1 \
  --instruction "Mine stone" \
  --max-steps 100
```

### 5. Run Agent Server WITH Interactive Mode

```bash
# Terminal 2 - Agent with interactive mode
python server_minerl.py \
  --checkpoint /path/to/jarvis_vla_checkpoint \
  --vllm-url http://localhost:8000/v1 \
  --interactive-port 6666 \
  --instruction "Mine stone"

# Server will show:
# "Interactive mode enabled on port 6666"
# "Connect with: python3 -m minestudio.simulator.minerl.interactor 6666"
```

### 6. Connect Your Minecraft Client (Local Computer)

**On your local computer:**

```bash
# Step A: Forward the port via SSH
ssh -L 6666:localhost:6666 user@your-server-ip

# Keep this terminal open!
```

**In a NEW terminal on your local computer:**

```bash
# Step B: Install MineStudio
pip install minestudio

# Step C: Start the interactor
python3 -m minestudio.simulator.minerl.interactor 6666 --ip localhost

# A Minecraft window will open!
# You'll be in the agent's world, watching it play!
```

### 7. Spectator Mode (Invisible to Agent)

Once in the Minecraft world:

```
Press 't' (chat)
Type: /gamemode sp
Press Enter
```

You're now in spectator mode - invisible to the agent!

---

## Usage Examples

### Interactive Console Mode

```bash
python server_minerl.py \
  --checkpoint /path/to/model \
  --interactive-port 6666

# Will prompt for instructions:
# Enter instruction: Mine stone
# Enter instruction: Craft wooden pickaxe
# Enter instruction: quit
```

### Single Task with Human Spectator

```bash
python server_minerl.py \
  --checkpoint /path/to/model \
  --instruction "Build a house" \
  --max-steps 2000 \
  --interactive-port 6666
```

### Fast Mode (No Human Watching)

```bash
# Agent runs at full speed (not real-time)
python server_minerl.py \
  --checkpoint /path/to/model \
  --instruction "Mine diamond" \
  --no-realtime
```

---

## Port Forwarding Setup

### SSH Port Forward (Recommended)

```bash
# On your local computer:
ssh -L 6666:localhost:6666 user@server-ip

# Now localhost:6666 on your computer → server's port 6666
```

### Ngrok (Alternative)

```bash
# On server:
ngrok tcp 6666

# Shows: tcp://0.tcp.ngrok.io:12345
# On local computer:
python3 -m minestudio.simulator.minerl.interactor 12345 --ip 0.tcp.ngrok.io
```

### Direct Connection (If Server Has Public IP)

```bash
# On local computer:
python3 -m minestudio.simulator.minerl.interactor 6666 --ip <server-public-ip>

# Make sure firewall allows port 6666!
```

---

## Troubleshooting

### "Cannot connect to X server"

```bash
# Use Xvfb wrapper
xvfb-run -a python server_minerl.py ...

# Or set display
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 &
python server_minerl.py ...
```

### "Java version mismatch"

```bash
# MUST use Java 8!
conda install --channel=conda-forge openjdk=8 -y

# Verify
java -version  # Should show 1.8.0_xxx
```

### "Interactor connection failed"

```bash
# On server: Make sure agent is running FIRST
# Then on local: Try connecting again

# Check port is forwarded correctly
# On local computer:
netstat -an | grep 6666  # Should show LISTEN
```

### "Agent runs too fast to watch"

```bash
# Use real-time mode (default)
python server_minerl.py --interactive-port 6666 ...

# NOT this:
# python server_minerl.py --no-realtime ...  # Too fast for humans
```

### "GPU not available"

```bash
# Use CPU rendering (slower but works everywhere)
xvfb-run python server_minerl.py ...

# Or install VirtualGL for GPU rendering
sudo apt-get install virtualgl
MINESTUDIO_GPU_RENDER=1 python server_minerl.py ...
```

---

## Performance Expectations

| Mode | FPS | Latency | Notes |
|------|-----|---------|-------|
| Agent Only | 15-20 | ~60ms | Full speed |
| Interactive (CPU) | 10-15 | ~100ms | Xvfb rendering |
| Interactive (GPU) | 15-20 | ~60ms | VirtualGL |
| Fast Mode | 20+ | ~50ms | Not human-watchable |

---

## Differences from Mineflayer Bridge

| Feature | Mineflayer Bridge | MineRL Server |
|---------|-------------------|---------------|
| **POV** | World view only | True first-person with hands |
| **HUD** | Fake overlays | Real Minecraft HUD |
| **Interactive** | Not supported | Full support via interactor |
| **Minecraft Version** | 1.21.8 | 1.16.5 |
| **Rendering** | headless-gl | Real Minecraft client |
| **GUI Screens** | Not visible | Fully visible |

---

## Files

```
/workspace/Herobine/minerl_server/
├── minerl_env.py         # Environment wrapper with interactive support
├── server_minerl.py      # Main server with interactive mode
├── SETUP.md             # This file
├── test_hands.py        # Test script to verify hands are visible
└── logs/                # Screenshots and recordings
```

---

## Next Steps

1. ✅ Verify Java 8 is installed
2. ✅ Test basic rendering: `xvfb-run python -m minestudio.simulator.entry`
3. ✅ Start VLLM server
4. ✅ Run agent server
5. ✅ Test interactive mode locally
6. ✅ Set up port forwarding
7. ✅ Connect your Minecraft client
8. ✅ Watch your agent play in real-time!

---

## Support

- **MineRL Issues:** https://github.com/minerllabs/minerl
- **MineStudio Docs:** https://craftjarvis.github.io/MineStudio/
- **Interactive Mode:** Built-in to MineRL 0.4.4+

---

**Your agent now has proper first-person POV with hands, and you can watch it play in real-time!** 🎮

