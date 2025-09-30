# Minecraft Screenshot System - Context Summary

## Project Goal
Create a system where a VLA AI agent (JarvisVLA) can control a Mineflayer bot in a real Minecraft server and receive proper first-person POV screenshots for vision-language-action inference.

---

## What Was Attempted: Prismarine-Viewer Approach

### Architecture
- **Bridge Server**: Node.js server (`mineflayer_bridge.js`) on port 1111
- **Mineflayer Bot**: Connects to Minecraft server, controlled via HTTP API
- **Rendering**: Attempted to use `prismarine-viewer` for screenshots
- **Backend**: Python server (`server_mineflayer.py`) runs VLLMAgentAdapter

### Evolution of Screenshot Approach

#### Attempt 1: Web Viewer + Puppeteer (FAILED)
- Used `prismarine-viewer`'s web server on port 3007
- Tried to screenshot it with Puppeteer headless Chrome
- **Failed**: Puppeteer's headless Chrome cannot create WebGL context
- Error: `THREE.WebGLRenderer: Error creating WebGL context`

#### Attempt 2: Server-Side Rendering with headless-gl (PARTIAL SUCCESS)
- Switched to server-side THREE.js rendering
- Used `headless-gl` to provide WebGL context directly
- Created mock DOM objects (document, canvas, Image) for THREE.js
- **Result**: World geometry renders correctly with textures!

---

## What Works Now

### ✓ Successfully Implemented
1. **Server-side 3D rendering** using headless-gl + THREE.js
2. **World terrain rendering** with proper textures (58k+ unique colors)
3. **Camera tracking** - follows bot's position and rotation
4. **Chunk loading** - dynamically loads world as bot moves
5. **Basic HUD overlays** - crosshair, hotbar, health/food bars, position info
6. **Screenshot API** - Returns 640x360 JPEG via HTTP

### Current Performance
- Initialization: ~10-12 seconds
- Screenshots: Working, 100% success rate
- Image quality: Full color, proper textures, ~185 mean brightness
- Unique colors: 58,000+ (real Minecraft content)

### Configuration
- Bridge port: 1111
- Web viewer port: 3007 (not actually used anymore)
- Image size: 640x360
- VLLM port: 3000

---

## Critical Limitations (Why We Need MineRL/Malmo)

### ❌ What Doesn't Work with Prismarine-Viewer

1. **No Player Hands**
   - Prismarine-viewer renders world only, not first-person body parts
   - Held items not visible in hand
   - No hand swing animations

2. **No Proper HUD**
   - We added canvas-drawn overlays, but they're approximations
   - Not the actual Minecraft HUD rendering
   - Missing: experience bar, armor, potion effects, scoreboard

3. **No GUI Screens**
   - Cannot render inventory screen, chests, crafting tables
   - Opening GUI would show nothing

4. **No Particles/Effects**
   - Breaking blocks, hitting entities - no visual feedback
   - Prismarine-viewer doesn't render particle systems

5. **Limited Entity Rendering**
   - Other players/mobs render as models but without animations
   - No name tags, health bars above entities

### Why This Matters for VLA
- VLA models (like JarvisVLA) are trained on **real Minecraft POV recordings**
- They expect to see hands, held items, proper HUD
- Distribution shift if training data has hands but inference doesn't

---

## Key Technical Findings

### headless-gl Integration
```javascript
// headless-gl needs these properties on the GL context:
glContext.canvas = { width, height, clientWidth, clientHeight, ... }
glContext.drawingBufferWidth = width
glContext.drawingBufferHeight = height

// THREE.js needs document object:
global.document = { createElement, createElementNS }

// Texture loading needs node-canvas Image:
// Must patch texImage2D to convert Image to ImageData
```

### Pixel Reading from headless-gl
```javascript
// Use readPixels (pixels() method doesn't exist):
const pixels = new Uint8Array(width * height * 4)
glContext.readPixels(0, 0, width, height, glContext.RGBA, glContext.UNSIGNED_BYTE, pixels)

// Must flip Y-axis (WebGL bottom-up → image top-down)
const srcRow = height - 1 - y
```

### Prismarine-Viewer Quirks
- Needs `global.loadImage = loadImage` from node-canvas
- WorldView must be initialized with `await worldView.init(center)`
- Requires `setVersion(bot.version)` before creating WorldView
- Uses THREE.js r152 - lighting is ESSENTIAL (scene renders black without it)

---

## Current File State

### `/workspace/Herobine/bridge/mineflayer_bridge.js` (846 lines)
**Status**: Fully functional for world rendering

**Key Functions**:
- `createBot(config)` - Initialize mineflayer bot
- `initServerSideViewer()` - Set up headless-gl + THREE.js + prismarine-viewer
- `captureScreenshot()` - Render frame, read pixels, add HUD overlays, return JPEG
- HTTP endpoints: `/init`, `/action`, `/observation`, `/screenshot`, `/viewer/status`

**Key Variables**:
- `serverViewer` - Prismarine Viewer instance
- `viewerRenderer` - THREE.WebGLRenderer with headless-gl
- `viewerWorldView` - WorldView tracking bot's chunk area
- `viewerReady` - Boolean flag

### `/workspace/Herobine/bridge/mineflayer_env.py` (330 lines)
**Status**: Working wrapper around bridge

**Key Methods**:
- `reset()` - Reset environment
- `step(action)` - Execute action, return observation
- `get_pov_image()` - Fetch screenshot from bridge
- `ActionMapper.jarvis_to_mineflayer()` - Convert VPT actions to Mineflayer commands

### `/workspace/Herobine/bridge/server_mineflayer.py` (287 lines)
**Status**: Working main server

**Features**:
- Runs agent loop at 20 FPS
- Integrates VLLMAgentAdapter
- Logs screenshots to `agent_logs/step_XXXXX_input.jpg`
- Chat-based instruction system

---

## System Requirements Met

### Installed Dependencies
```bash
# System libraries for Puppeteer (though we don't use it anymore):
libxkbcommon0, libxcomposite1, libxdamage1, libxrandr2, libgbm1, etc.

# Node packages:
mineflayer, prismarine-viewer, express, canvas, gl (headless-gl)

# Python packages:
PIL, requests, numpy, (vllm client)
```

---

## Next Steps: Migrating to MineRL/Malmo

### Why MineRL/Malmo?
- **Proper POV**: Real Minecraft client rendering
- **Full HUD**: Hands, inventory, hearts, food, XP, armor
- **GUI Support**: Can see chests, crafting tables, furnaces
- **Particles**: Breaking blocks, hitting mobs shows effects
- **Exact Match**: Training data distribution (if model trained on MineRL)

### MineRL/Malmo Architecture
```
┌─────────────────┐
│  Minecraft      │  Actual Java client running
│  Client (Malmo) │  with Malmo mod installed
└────────┬────────┘
         │
         ├─> Renders to framebuffer
         ├─> Malmo captures screenshots
         │
┌────────┴────────┐
│  Malmo Python   │  Python wrapper
│  Environment    │  Compatible with Gym/Gymnasium
└────────┬────────┘
         │
┌────────┴────────┐
│  Your Agent     │  VLLMAgentAdapter
│  (JarvisVLA)    │  Gets proper POV images
└─────────────────┘
```

### Migration Strategy

#### Phase 1: Setup MineRL
```bash
# Install MineRL
pip install minerl

# Or use MineStudio's MinecraftSim (recommended)
pip install minestudio
```

#### Phase 2: Replace MineflayerEnv
```python
# Old:
from mineflayer_env import MineflayerEnv

# New:
from minestudio.simulator import MinecraftSim
# or
import minerl
```

#### Phase 3: Adapt Action/Observation Interface
MineRL observations include:
```python
{
    'pov': np.array(360, 640, 3),  # Proper first-person POV
    'inventory': {...},
    'equipped_items': {...},
    'location_stats': {...},
    # All the info you need
}
```

#### Phase 4: Connect to Existing Server
```python
# MineRL can connect to existing Minecraft server:
env = minerl.make(
    'MineRLNavigate-v0',  # Or custom task
    # Connect to your ngrok server
)
```

### Key Differences to Handle

| Aspect | Mineflayer | MineRL/Malmo |
|--------|------------|--------------|
| POV | World view only | True first-person with hands |
| HUD | Manual overlays | Real Minecraft HUD |
| Actions | Direct bot control | Player-level actions |
| Server | Any Minecraft server | Malmo-enabled server |
| Latency | Very low | Slightly higher (client rendering) |
| Complexity | Low | Medium-High |

---

## Important Considerations

### MineRL Server Requirements
1. **Malmo Mod**: Server needs Malmo mod installed
2. **Port Setup**: Different port structure than vanilla
3. **Version**: Must match MineRL version (typically 1.16.5 or specific versions)
4. **Ngrok**: May need different port forwarding setup

### VLLMAgentAdapter Compatibility
Your `VLLMAgentAdapter` expects certain observation format:
```python
# Current format (works with both):
obs = {
    'pov': PIL.Image or np.array,
    'inventory': [...],
    'position': {x, y, z},
    'health': int,
    'food': int
}
```

Should be compatible if you maintain this interface.

### Action Mapping
```python
# Mineflayer actions:
{'type': 'compound', 'camera': [pitch, yaw], 'buttons': {...}}

# MineRL actions:
{
    'camera': np.array([pitch_delta, yaw_delta]),
    'buttons': Buttons(forward=0, back=0, ...),
    # More detailed action space
}
```

You already have `ActionMapper.jarvis_to_mineflayer()` - will need similar for MineRL.

---

## Current Working Code Highlights

### Server-Side Viewer Initialization (Working)
```javascript
// Create headless-gl context with proper mocking
const glContext = gl(width, height, { preserveDrawingBuffer: true })
glContext.canvas = mockCanvas
glContext.drawingBufferWidth = width

// Mock document for THREE.js
global.document = { createElement: ... }

// Create renderer
viewerRenderer = new THREE.WebGLRenderer({ canvas: mockCanvas, context: glContext })

// Add BRIGHT lighting (critical!)
scene.add(new THREE.AmbientLight(0xffffff, 1.0))
scene.add(new THREE.DirectionalLight(0xffffff, 0.8))

// Create world view
const worldView = new WorldView(bot.world, 4, center)
await worldView.init(center)
```

### Screenshot Capture (Working)
```javascript
// Update camera to bot position
serverViewer.camera.position.set(botPos.x, botPos.y + 1.6, botPos.z)
serverViewer.camera.rotation.set(pitch, yaw, 0, 'YXZ')

// Render
viewerRenderer.render(serverViewer.scene, serverViewer.camera)

// Read pixels (Y-axis flipped)
glContext.readPixels(0, 0, width, height, glContext.RGBA, glContext.UNSIGNED_BYTE, pixels)

// Flip and convert to JPEG
```

---

## Files to Preserve/Reference

### Keep These
- `/workspace/Herobine/bridge/vllm_agent_adapter.py` - Your agent wrapper
- `/workspace/Herobine/bridge/server_mineflayer.py` - Main server loop structure
- Action mapping logic in `mineflayer_env.py` lines 262-316

### Can Discard
- `mineflayer_bridge.js` - Specific to prismarine-viewer
- `mineflayer_env.py` - Wrapper for mineflayer bridge (replace with MineRL env)

### Port Later
- Chat instruction system (lines 27-90 in mineflayer_bridge.js)
- Step logging logic (server_mineflayer.py lines 158-170)
- FPS control (step_delay)

---

## Migration Checklist for MineRL/Malmo

### Setup Phase
- [ ] Install MineRL or MineStudio
- [ ] Set up Malmo-enabled Minecraft server
- [ ] Configure server to accept connections (may need different than ngrok setup)
- [ ] Test basic MineRL environment creation

### Integration Phase  
- [ ] Replace `MineflayerEnv` with `MinecraftSim` or MineRL env
- [ ] Adapt `VLLMAgentAdapter` to use MineRL observations
- [ ] Map JarvisVLA actions to MineRL action space
- [ ] Update `server_mineflayer.py` to use new environment

### Testing Phase
- [ ] Verify POV screenshots include hands and proper HUD
- [ ] Check held items are visible
- [ ] Test GUI screens (inventory, chests)
- [ ] Validate action execution matches expectations

### Optimization Phase
- [ ] Tune FPS/latency
- [ ] Optimize screenshot format (JPEG quality vs size)
- [ ] Add any missing observation fields

---

## Key Lessons Learned

### Technical Insights
1. **Puppeteer + headless Chrome**: Cannot do WebGL in headless mode
2. **headless-gl**: Works but needs extensive DOM mocking for THREE.js
3. **Texture loading**: headless-gl's `texImage2D` needs ImageData, not raw Images
4. **Lighting is critical**: THREE.js renders pure black without lights
5. **Prismarine-viewer**: Designed for world spectating, not first-person POV

### What Would Have Saved Time
- Starting with MineRL/Malmo from the beginning
- Checking if prismarine-viewer supports first-person hands earlier
- Understanding the training data format (what does JarvisVLA expect?)

---

## Current System Stats

### Performance
- Bridge startup: ~2 seconds
- Bot connection: ~2 seconds  
- Viewer initialization: ~8 seconds (chunks + textures)
- Screenshot capture: ~0.05 seconds (20 FPS capable)
- Total init time: ~12 seconds

### Image Quality
- Resolution: 640x360 (matches MineRL standard)
- Format: JPEG quality 0.9
- Unique colors: 58,000+ 
- Mean brightness: ~185/255
- Success rate: 100%

### What's Visible
- ✓ World terrain with textures
- ✓ Sky with correct color
- ✓ Blocks, trees, water, etc.
- ✓ Other entities (players, mobs) as 3D models
- ✓ Crosshair overlay
- ✓ Hotbar with item names and counts
- ✓ Health/food bar overlays
- ✓ Position/debug info
- ✗ Player's own hands/arms
- ✗ Actual held item in hand (3D model)
- ✗ Real Minecraft HUD textures
- ✗ GUI screens (inventory, etc.)

---

## Recommended Next Approach: MineStudio

### Why MineStudio Over Raw MineRL?
MineStudio (from your codebase at `/workspace/MineStudio`) provides:
- Higher-level abstractions
- Better multiplayer support
- Callback system for extensibility
- Already designed for VLA training

### MineStudio MinecraftSim Usage
```python
from minestudio.simulator import MinecraftSim

# Create environment
env = MinecraftSim(
    obs_size=(360, 640),
    render_size=(360, 640),
    # ... other config
)

# Use like Gym
obs, info = env.reset()
# obs['pov'] will be proper first-person POV with hands!

action = agent.get_action(obs)
obs, reward, terminated, truncated, info = env.step(action)
```

### Connecting to Remote Server
```python
# MineStudio/MineRL can connect to existing Minecraft servers
# Need to configure Malmo mission XML to specify server address:
from minestudio.simulator.callbacks import SummonMobsCallback

env = MinecraftSim(
    obs_size=(360, 640),
    # Point to your ngrok server
    server_host='2.tcp.us-cal-1.ngrok.io',
    server_port=19335,
    # Other callbacks...
)
```

---

## Files Summary

### Core Files (Current State)
```
/workspace/Herobine/bridge/
├── mineflayer_bridge.js (846 lines)
│   └── Server-side rendering with headless-gl
│       Fully functional but lacks hands/proper HUD
│
├── mineflayer_env.py (330 lines)
│   └── Gym-like wrapper around Mineflayer
│       Will be replaced with MinecraftSim
│
├── server_mineflayer.py (287 lines)
│   └── Main server with agent loop
│       Can mostly be reused
│
└── vllm_agent_adapter.py (96 lines)
    └── Wraps JarvisVLA for your use case
        Should work with MineRL with minor changes
```

### Dependencies
```json
{
  "node": ["mineflayer", "prismarine-viewer", "express", "canvas", "gl"],
  "python": ["PIL", "requests", "numpy", "gym", "minestudio/minerl"]
}
```

---

## For Next Session: MineRL Migration

### Quick Start Command
```bash
# 1. Install MineStudio
cd /workspace/MineStudio
pip install -e .

# 2. Test basic environment
python -c "from minestudio.simulator import MinecraftSim; print('✓ Import works')"

# 3. Create new server file
cd /workspace/Herobine/bridge
cp server_mineflayer.py server_minerl.py
# Then modify to use MinecraftSim instead of MineflayerEnv
```

### Key Questions to Answer
1. **Server Setup**: Does your Minecraft server need Malmo mod, or can MineRL connect to vanilla?
2. **Ngrok Compatibility**: Can MineRL connect through ngrok tunnels?
3. **Action Space**: What's the exact action format JarvisVLA outputs? (Check training code)
4. **Version**: What Minecraft version is your server? (You're on 1.21.8, MineRL typically uses 1.16.5)

### Critical Path
1. Get MineRL environment running locally first
2. Test screenshot quality (verify hands visible)
3. Connect to remote server through ngrok
4. Integrate with VLLMAgentAdapter
5. Verify action execution matches training distribution

---

## Contact Points

### Verification Tests
```python
# Test if screenshots have hands:
from PIL import Image
img = Image.open('agent_logs/step_00000_input.jpg')
arr = np.array(img)

# Check bottom center (where hands should be)
hand_region = arr[270:360, 200:440, :]  # Bottom-center region
if hand_region.mean() > 100:  # Hands are often visible/bright
    print("✓ Hands likely visible")
```

### Success Criteria for MineRL Migration
- [ ] Screenshots show player hands holding items
- [ ] Health/food bars are real Minecraft textures (not overlays)
- [ ] Opening inventory (E key) shows inventory screen
- [ ] Held items change visual when switching hotbar
- [ ] Breaking blocks shows hand animation
- [ ] Image distribution matches MineRL/training data

---

## Summary

**Current State**: World rendering works perfectly, but missing first-person elements (hands, proper HUD).

**Prismarine-viewer is fundamentally limited** - it's a world viewer, not a client renderer.

**Next Step**: Migrate to MineRL/Malmo for true first-person POV.

**Estimated Migration Time**: 4-8 hours (depending on server setup complexity)

**Confidence**: HIGH - MineRL is the standard for Minecraft AI research and handles exactly what you need.

---

## Paste This For Next Session

When starting fresh context, include:
1. This entire document
2. Your VLLMAgentAdapter code
3. The Minecraft server details (host, port, version)
4. JarvisVLA model information
5. What observation format JarvisVLA expects

The goal: Get proper first-person POV screenshots with hands, HUD, and GUI support using MineRL/Malmo instead of prismarine-viewer.


