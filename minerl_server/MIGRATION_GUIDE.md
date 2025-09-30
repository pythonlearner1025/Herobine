# Migration Guide: Prismarine-Viewer → MineRL/MineStudio

## Why Migrate?

**Prismarine-Viewer Limitations:**
- ❌ No player hands visible
- ❌ No held items in first-person view
- ❌ Fake HUD overlays (not real Minecraft UI)
- ❌ No GUI screens (inventory, chests, etc.)
- ❌ No particle effects

**MineRL/MineStudio Advantages:**
- ✅ True first-person POV with hands
- ✅ Held items visible
- ✅ Real Minecraft HUD
- ✅ Full GUI support
- ✅ Particle effects and animations
- ✅ **Matches JarvisVLA training data distribution**

## Critical: Verify Training Data First

Before migrating, **check if JarvisVLA was trained with hands visible:**

```bash
# Download sample from training dataset
huggingface-cli download CraftJarvis/minecraft-vla-sft --repo-type dataset --include "*.png" --local-dir ./dataset_sample

# Visually inspect images
# Look for:
# - Are hands visible at bottom of screen?
# - Is hotbar real Minecraft UI?
# - Are held items shown in first-person?
```

**If training data has hands** → Migration is mandatory  
**If training data has NO hands** → Current setup might be okay

## Migration Steps

### Step 1: Verify MineStudio Installation

```bash
cd /workspace/MineStudio
pip install -e .

# Test
python -c "from minestudio.simulator import MinecraftSim; print('✓ Ready')"
```

### Step 2: Understand Minecraft Version Requirement

**Important:** MineStudio uses Minecraft **1.16.5** (standard for MineRL).

Your current server is **1.21.8** → **Incompatible**

**Options:**
- **A) Set up new 1.16.5 server** (Recommended)
- **B) Test current prismarine setup first** (if hands aren't critical)

### Step 3: Set Up Rendering Backend

MineRL requires a rendering backend:

```bash
# Option A: VirtualGL (GPU, faster)
sudo apt-get install -y mesa-utils virtualgl

# Option B: Xvfb (CPU, slower but always works)
sudo apt-get install -y xvfb mesa-utils libegl1-mesa libgl1-mesa-dev

# Test with Xvfb
xvfb-run python -m minestudio.simulator.entry
```

### Step 4: Use New Environment

```python
# OLD (Prismarine-Viewer):
from mineflayer_env import MineflayerEnv
env = MineflayerEnv(...)

# NEW (MineRL/MineStudio):
from minerl_env import MineRLEnv
env = MineRLEnv(
    obs_size=(360, 640),  # Standard resolution
    render_size=(360, 640),
)

obs, info = env.reset()
# obs['pov'] is PIL Image with HANDS VISIBLE!
```

### Step 5: Run New Server

```bash
# Start VLLM server (if not already running)
./start_vllm_server.sh

# Run MineRL-based agent server
cd /workspace/Herobine/bridge
python server_minerl.py \
    --checkpoint /path/to/jarvis_vla_checkpoint \
    --vllm-url http://localhost:8000/v1 \
    --fps 20

# Interactive mode - it will prompt for instructions
```

### Step 6: Verify Hands Are Visible

```python
# Quick test
from minerl_env import MineRLEnv
from PIL import Image

env = MineRLEnv()
obs, info = env.reset()

# Save screenshot
pov = obs['pov']
pov.save('test_screenshot.png')

# Check bottom-center region for hands
import numpy as np
arr = np.array(pov)
hand_region = arr[270:360, 200:440, :]  # Bottom-center
print(f"Hand region mean brightness: {hand_region.mean():.1f}")
# Should be >100 if hands are visible

env.close()
```

## Action Space Mapping

### JarvisVLA/VPT Format
```python
{
    'buttons': np.array([...]),  # Binary array, length ~20
    'camera': np.array([pitch, yaw])  # Discretized bins
}
```

### MineRL Format
```python
{
    'forward': 0/1,
    'back': 0/1,
    'left': 0/1,
    'right': 0/1,
    'jump': 0/1,
    'sneak': 0/1,
    'sprint': 0/1,
    'attack': 0/1,
    'use': 0/1,
    'hotbar.1': 0/1, ..., 'hotbar.9': 0/1,
    'inventory': 0/1,
    'camera': np.array([pitch_delta, yaw_delta])  # Continuous, degrees
}
```

**Mapping is handled in** `minerl_env.py` → `ActionMapper.jarvis_to_minerl()`

You may need to adjust the button ordering based on how JarvisVLA encodes actions.

## Observation Format

### Old (Mineflayer)
```python
{
    'pov': PIL.Image,  # World view only, NO hands
    'inventory': {...},
    'position': {x, y, z},
    'health': int,
    'food': int,
}
```

### New (MineRL)
```python
{
    'pov': PIL.Image,  # True first-person WITH hands
    'inventory': {...},
    'equipped_items': {...},
    'position': {x, y, z},
    'rotation': {pitch, yaw},
    'health': int,
    'food': int,
}
```

The format is very similar! `VLLMAgentAdapter` should work with minimal changes.

## Performance Expectations

| Metric | Prismarine-Viewer | MineRL/MineStudio |
|--------|-------------------|-------------------|
| Initialization | ~10s | ~5s |
| FPS (GPU) | 20 | 15-20 (VirtualGL) |
| FPS (CPU) | 20 | 5-10 (Xvfb) |
| Latency | ~50ms | ~100ms |
| Screenshot Quality | Good | Excellent |
| **Hands Visible** | ❌ | ✅ |

## Troubleshooting

### "Cannot connect to X server"
```bash
# Use Xvfb wrapper
xvfb-run -a python server_minerl.py ...

# Or set display
export DISPLAY=:0
python server_minerl.py ...
```

### "Malmo failed to start"
```bash
# Check Java version (needs JDK 8)
java -version

# Reinstall if needed
conda install --channel=conda-forge openjdk=8 -y
```

### "Actions don't work correctly"
```bash
# Check action mapping in minerl_env.py
# VPT button order might differ - verify with:
python -c "from minestudio.utils.vpt_lib.actions import Buttons; print(Buttons.ALL)"
```

### Performance is slow
```bash
# Use VirtualGL instead of Xvfb (if you have NVIDIA GPU)
sudo apt-get install virtualgl

# Run with GPU rendering
MINESTUDIO_GPU_RENDER=1 python server_minerl.py ...
```

## Rollback Plan

If migration has issues, you can easily roll back:

```python
# Just use old files
from mineflayer_env import MineflayerEnv
from server_mineflayer import ...

# Old system still works!
```

## Success Criteria

✅ Screenshots show player hands at bottom of frame  
✅ Held items visible in first-person  
✅ Hotbar is real Minecraft UI (not overlay)  
✅ Agent actions execute correctly  
✅ Performance is acceptable (>10 FPS)  
✅ Agent behavior quality improves (less distribution shift)  

## Estimated Time

- **Setup:** 30 min
- **Implementation:** 2 hours  
- **Testing:** 1 hour
- **Debugging:** 1-2 hours
- **Total:** 4-6 hours

## References

- [MineStudio Documentation](https://craftjarvis.github.io/MineStudio/)
- [MineRL GitHub](https://github.com/minerllabs/minerl)
- [JarvisVLA Paper](https://arxiv.org/abs/2503.16365)
- [Your CONTEXT_SUMMARY.md](./CONTEXT_SUMMARY.md)

---

## Quick Command Reference

```bash
# Test MineStudio
python -m minestudio.simulator.entry

# Run new server (interactive)
python server_minerl.py --checkpoint <path>

# Run single episode
python server_minerl.py --checkpoint <path> --instruction "Mine stone" --max-steps 500

# Compare screenshots
python compare_screenshots.py
```
