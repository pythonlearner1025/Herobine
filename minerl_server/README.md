# MineRL Server for JarvisVLA

**Proper first-person POV with hands, HUD, and interactive spectator support**

This directory contains the MineRL-based implementation that replaces the prismarine-viewer approach. It provides:

✅ **True first-person POV** with hands visible  
✅ **Real Minecraft HUD** (health, food, hotbar)  
✅ **GUI support** (inventory, chests, crafting)  
✅ **Interactive mode** - connect your Minecraft client to watch the agent  
✅ **Proper distribution match** for VLA models trained on MineRL data  

---

## Quick Start

### 1. Test Hands Visibility

```bash
cd /workspace/Herobine/minerl_server
python test_hands.py
```

This will:
- Create a MineRL environment
- Capture a screenshot
- Analyze if hands are visible
- Save `test_minerl_screenshot.png`

**Expected output:** `✓✓✓ HANDS LIKELY VISIBLE! ✓✓✓`

### 2. Run Agent (Basic)

```bash
# Make sure VLLM server is running first!
# cd /workspace/Herobine && ./start_vllm_server.sh

python server_minerl.py \
  --checkpoint /path/to/jarvis_vla_qwen2_vl_7b_sft \
  --vllm-url http://localhost:8000/v1 \
  --instruction "Mine stone"
```

### 3. Run Agent with Interactive Mode

```bash
python server_minerl.py \
  --checkpoint /path/to/model \
  --interactive-port 6666 \
  --instruction "Build a house"
```

**Then on your LOCAL computer:**

```bash
# Forward the port
ssh -L 6666:localhost:6666 user@server

# In another terminal:
pip install minestudio
python3 -m minestudio.simulator.minerl.interactor 6666 --ip localhost
```

A Minecraft window will open showing the agent's world in real-time!

---

## Files

| File | Description |
|------|-------------|
| `minerl_env.py` | Environment wrapper with interactive mode support |
| `server_minerl.py` | Main agent server |
| `test_hands.py` | Quick test for hands visibility |
| `SETUP.md` | Comprehensive setup guide |
| `README.md` | This file |

---

## System Requirements

**Server:**
- ✅ Java 8 (verified installed)
- ✅ MineStudio with MineRL (verified installed)
- ✅ Python 3.10+
- ✅ GPU recommended (or Xvfb for CPU rendering)

**Client (for interactive mode):**
- Python 3.10+
- MineStudio (`pip install minestudio`)
- OpenJDK 8
- SSH port forwarding

---

## Key Differences from Mineflayer Bridge

| Feature | Mineflayer (Old) | MineRL (New) |
|---------|------------------|--------------|
| **Hands visible** | ❌ No | ✅ Yes |
| **HUD** | Fake overlays | Real Minecraft HUD |
| **Interactive** | Not supported | Full support |
| **GUI screens** | Not visible | Visible |
| **Minecraft version** | 1.21.8 | 1.16.5 |
| **Distribution match** | ⚠ Shift | ✅ Match |

---

## Usage Examples

### Interactive Console

```bash
python server_minerl.py --checkpoint /path/to/model --interactive-port 6666

# Prompts for instructions:
> Enter instruction: Mine stone
> Enter instruction: Craft wooden pickaxe
> Enter instruction: quit
```

### Batch Processing

```bash
for task in "Mine stone" "Craft pickaxe" "Build house"; do
  python server_minerl.py \
    --checkpoint /path/to/model \
    --instruction "$task" \
    --max-steps 500
done
```

### With Spectator (Real-time Observation)

```bash
# Terminal 1 (server):
python server_minerl.py \
  --checkpoint /path/to/model \
  --interactive-port 6666 \
  --instruction "Explore world"

# Terminal 2 (local computer):
ssh -L 6666:localhost:6666 user@server

# Terminal 3 (local computer):
python3 -m minestudio.simulator.minerl.interactor 6666 --ip localhost

# In Minecraft: Press 't', type '/gamemode sp' to become invisible
```

---

## Troubleshooting

### Q: "Cannot connect to X server"

**A:** Use Xvfb wrapper:

```bash
xvfb-run -a python server_minerl.py ...
```

### Q: "Interactor connection refused"

**A:** Make sure:
1. Agent server is running FIRST
2. Port forwarding is active (`ssh -L 6666:localhost:6666 ...`)
3. Port number matches on both sides

### Q: "Hands not visible in screenshot"

**A:** This shouldn't happen with MineRL. If it does:
1. Check if MineRL version is 0.4.4+
2. Verify Java 8 is active
3. Try running test again: `python test_hands.py`

### Q: "Agent runs too fast to watch"

**A:** Use real-time mode (default):

```bash
python server_minerl.py --interactive-port 6666 ...
# NOT --no-realtime
```

---

## Performance

| Mode | FPS | Notes |
|------|-----|-------|
| Agent only (CPU) | 10-15 | Xvfb rendering |
| Agent only (GPU) | 15-20 | VirtualGL |
| Interactive (realtime) | 10-15 | Human-watchable |
| Fast mode | 20+ | Not for humans |

---

## Documentation

- **[SETUP.md](./SETUP.md)** - Full setup guide with port forwarding
- **[/workspace/Herobine/bridge/CONTEXT_SUMMARY.md](../bridge/CONTEXT_SUMMARY.md)** - Why we migrated from prismarine-viewer

---

## Migration from Mineflayer Bridge

The old mineflayer-based system is preserved in `/workspace/Herobine/bridge/`.

**Key changes:**
1. Environment: `MineflayerEnv` → `MineRLEnv`
2. Server: `server_mineflayer.py` → `server_minerl.py`
3. Minecraft version: 1.21.8 → 1.16.5
4. POV: No hands → **With hands** ✓

**Migration time:** 4-6 hours (mostly waiting for testing)

---

## Credits

- **JarvisVLA:** https://github.com/CraftJarvis/JarvisVLA
- **MineStudio:** https://github.com/CraftJarvis/MineStudio
- **MineRL:** https://github.com/minerllabs/minerl

---

**You can now watch your AI agent play Minecraft in real-time with your own Minecraft client!** 🎮

