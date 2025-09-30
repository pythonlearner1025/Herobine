# Quick Setup Instructions

## Deliverables Summary

Created for your Minecraft AI server with Mineflayer + JarvisVLA:

### Core System Files
1. **`mineflayer_bridge.js`** - Node.js HTTP server that controls Mineflayer bot
2. **`mineflayer_env.py`** - Python gym environment mimicking MinecraftSim API  
3. **`vllm_agent_adapter.py`** - Adapter connecting JarvisVLA's VLLM_AGENT to Mineflayer
4. **`server_mineflayer.py`** - Main server script (replaces your server.py)

### Supporting Files
5. **`package.json`** - Node.js dependencies
6. **`README_MINEFLAYER.md`** - Complete documentation
7. **`SETUP_INSTRUCTIONS.md`** - This file

## What This Achieves

✅ **AI agent** (VLLM) controls a bot in real Minecraft  
✅ **Human players** can join the same server normally (port 25565)  
✅ **JarvisVLA compatibility** - Uses your existing VLLM_AGENT  
✅ **MineStudio-like API** - Compatible with your evaluate.py patterns  
✅ **make_interactive** - Not needed! Real server handles multiplayer  

## Quick Start

### Step 1: Install Dependencies

```bash
cd /workspace

# Node.js packages
npm install

# Python packages (if needed)
pip install requests numpy
```

### Step 2: Start Minecraft Server

You need a running Minecraft server. Easiest option:

```bash
# Using Docker
docker run -d -p 25565:25565 \
    -e EULA=TRUE \
    -e ONLINE_MODE=FALSE \
    itzg/minecraft-server
```

Or use an existing server - just note the IP:port.

### Step 3: Start VLLM Server (On GPU Machine)

```bash
# On your GPU machine
python -m vllm.entrypoints.openai.api_server \
    --model /path/to/your/checkpoint \
    --port 8000 \
    --trust-remote-code
```

### Step 4: Run the AI Server

```bash
python server_mineflayer.py \
    --mc-host localhost \
    --mc-port 25565 \
    --bot-username JarvisAI \
    --vllm-url http://your-gpu-machine:8000/v1 \
    --checkpoint /path/to/checkpoint \
    --instruction "Explore and survive" \
    --verbos
```

### Step 5: Join as Human Player

1. Open Minecraft client
2. Multiplayer → Direct Connect
3. Enter: `localhost:25565` (or your server IP)
4. See JarvisAI bot in the world!

## Key Differences from Original server.py

| Old (MineStudio) | New (Mineflayer) |
|------------------|------------------|
| `sim.env.make_interactive()` - Broken | Not needed - real server |
| Headless, no multiplayer | Full multiplayer support |
| Port 3145 never opens | Port 25565 works normally |
| Only AI can play | AI + humans together |

## Architecture Overview

```
[Minecraft Server:25565] ← TCP → [Mineflayer Bot] ← HTTP:3333 → [Python] ← HTTPS → [VLLM]
         ↑
    [Human Players]
```

## Next Steps

1. **Test without AI first**:
   ```bash
   python server_mineflayer.py --max-steps 100
   ```

2. **Add AI agent**:
   ```bash
   python server_mineflayer.py \
       --vllm-url http://localhost:8000/v1 \
       --checkpoint /models/qwen2-vl \
       --instruction "craft wooden tools"
   ```

3. **Improve action mapping**: 
   - Edit `ActionMapper` in `mineflayer_env.py`
   - Map JarvisVLA's action space to Mineflayer actions

4. **Add POV rendering**:
   - Integrate `prismarine-viewer` or similar
   - Currently returns black images (placeholder)

## Troubleshooting

**"Connection refused" when starting bot**:
- Check Minecraft server is running: `docker ps` or `telnet localhost 25565`

**"Node.js not found"**:
- Install Node.js 18+: `curl -fsSL https://deb.nodesource.com/setup_18.x | bash -`
- Then: `apt-get install -y nodejs`

**Agent gives errors**:
- Verify VLLM is running: `curl http://localhost:8000/v1/models`
- Check checkpoint path is correct

**Want to use original MineStudio**:
- Keep your original `server.py`  
- This system is a parallel alternative that actually works for multiplayer

## Files Structure

```
/workspace/
├── mineflayer_bridge.js      # Node.js bot controller
├── mineflayer_env.py          # Gym-like environment
├── vllm_agent_adapter.py      # JarvisVLA adapter
├── server_mineflayer.py       # Main server (NEW)
├── server.py                  # Original (keep for reference)
├── package.json               # Node dependencies
├── README_MINEFLAYER.md       # Full documentation
└── SETUP_INSTRUCTIONS.md      # This file
```

## What's Left to Implement

The core architecture is complete. For full JarvisVLA integration:

1. ✅ **POV Images**: Real screenshot support via prismarine-viewer (see CHAT_INTERACTION_GUIDE.md)
2. ✅ **Action Mapping**: Basic VPT → Mineflayer mapping implemented
3. ✅ **Chat Interaction**: Type in Minecraft to control JarvisAI (see QUICKSTART.md)
4. 🚧 **Advanced Action Mapping**: Inventory management, crafting GUI interactions
5. 🚧 **Reward Signals**: Task-specific success detection
6. 🚧 **Callbacks**: FastReset, InitInventory, etc.

See `README_MINEFLAYER.md` for detailed TODO list.

## Questions?

- Architecture questions: See `README_MINEFLAYER.md`
- API docs: Check docstrings in Python files
- Mineflayer docs: `/workspace/mineflayer/docs/`
- JarvisVLA reference: Your existing `evaluate.py` and `agent_wrapper.py`

