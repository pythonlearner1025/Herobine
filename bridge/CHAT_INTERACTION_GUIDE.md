# Chat-Based JarvisAI Interaction Guide

Complete implementation for interacting with JarvisAI through Minecraft chat commands.

## Overview

This implementation allows you to:
- **Send tasks via chat**: Any message in global chat becomes a task instruction for JarvisAI
- **Reset AI state**: Type "reset" to clear AI memory without affecting the bot's position
- **Real POV images**: Bot captures actual screenshots for vision processing
- **Proper action mapping**: JarvisVLA actions mapped to Mineflayer commands

## Architecture

```
[Player] --chat--> [Minecraft Server] ---> [Mineflayer Bot]
                                                |
                                                v
                                          [Chat Listener]
                                                |
                                                v
                                     [JarvisVLA Agent] <--POV Image
                                                |
                                                v
                                          [Action Mapper]
                                                |
                                                v
                                      [Bot executes actions]
```

## How JarvisVLA Inference Works

Based on `jarvisvla/evaluate/agent_wrapper.py`:

### 1. Input Format
```python
agent.forward(
    observations=[pov_image],      # List of PIL images (360x640)
    instructions=["craft a pickaxe"], # List of text instructions
    verbos=False,                   # Print debug info
    need_crafting_table=False       # Whether crafting GUI is open
)
```

### 2. Agent Processing
- Converts POV image to model input format
- Creates prompt from instruction (supports 3 types: 'normal', 'recipe', 'simple')
- Sends to VLLM server via OpenAI API
- Decodes model output to action tokens
- Supports action chunking (generates multiple actions at once)
- Supports history (remembers previous observations)

### 3. Output Format
Returns a single action dictionary:
```python
{
    'camera': [delta_yaw, delta_pitch],  # Camera movement
    'buttons': {
        'forward': 0/1,
        'back': 0/1,
        'left': 0/1,
        'right': 0/1,
        'jump': 0/1,
        'sneak': 0/1,
        'sprint': 0/1,
        'attack': 0/1,
        'use': 0/1,
        'drop': 0/1,
        'inventory': 0/1,
        'hotbar.1': 0/1,
        'hotbar.2': 0/1,
        # ... more buttons
    }
}
```

### 4. Action Tokenizer
- Uses `OneActionTokenizer` to decode model output
- Maps special tokens to discrete actions
- Actions are discretized into bins (e.g., camera has 21x21 bins)

## Implementation

### File 1: Enhanced `mineflayer_bridge.js`

**Location**: `/workspace/Herobine/bridge/mineflayer_bridge.js`

**Key additions**:
1. **Chat listener** - Captures all chat messages
2. **POV screenshot** - Uses prismarine-viewer for real screenshots
3. **Instruction queue** - Manages tasks from chat
4. **Reset handler** - Clears state without respawning

**New endpoints**:
- `POST /chat/instructions` - Get pending chat instructions
- `POST /clear_instruction` - Mark instruction as processed
- `POST /screenshot` - Get POV screenshot as base64 JPEG

### File 2: Enhanced `mineflayer_env.py`

**Location**: `/workspace/Herobine/bridge/mineflayer_env.py`

**Key additions**:
1. **get_pov_image()** - Returns PIL Image from bot's POV
2. **get_chat_instructions()** - Retrieves chat-based tasks
3. **clear_instruction()** - Marks instruction as processed

### File 3: Enhanced `server_mineflayer.py`

**Location**: `/workspace/Herobine/bridge/server_mineflayer.py`

**Key changes**:
1. **Chat monitoring loop** - Checks for new instructions
2. **Dynamic instruction switching** - Changes task based on chat
3. **Reset handling** - "reset" command clears AI state only
4. **POV integration** - Uses real screenshots instead of black images

## Setup Instructions

### Step 1: Install Dependencies

```bash
cd /workspace/Herobine/bridge

# Install prismarine-viewer for screenshots
npm install prismarine-viewer

# Install Python image library (if not already installed)
pip install Pillow
```

### Step 2: Update Your Files

The three files above need to be updated with the enhanced code (provided below).

### Step 3: Start VLLM Server

On your GPU machine:
```bash
python -m vllm.entrypoints.openai.api_server \
    --model /path/to/qwen2-vl-7b \
    --port 8000 \
    --trust-remote-code
```

### Step 4: Start Minecraft Server

On your Mac (with online-mode=false):
```bash
cd ~/mcmc
java -Xmx1024M -Xms1024M -jar server.jar
```

### Step 5: Start ngrok Tunnel

```bash
ngrok tcp 25565
# Note the forwarding address (e.g., 2.tcp.us-cal-1.ngrok.io:19335)
```

### Step 6: Run JarvisAI Bot

```bash
cd /workspace/Herobine/bridge

python server_mineflayer.py \
    --mc-host 2.tcp.us-cal-1.ngrok.io \
    --mc-port 19335 \
    --bot-username JarvisAI \
    --vllm-url http://your-gpu-server:8000/v1 \
    --checkpoint /path/to/qwen2-vl-7b \
    --instruction "Wait for instructions" \
    --verbos
```

## Usage Examples

### Example 1: Basic Task

**In Minecraft chat**:
```
<Player> craft a wooden pickaxe
```

**What happens**:
1. Bot sees chat message
2. Sets instruction to "craft a wooden pickaxe"
3. Agent processes POV image + instruction
4. Bot starts crafting

### Example 2: Changing Task Mid-Execution

**In Minecraft chat**:
```
<Player> collect wood
[Bot starts collecting wood]
<Player> stop, attack the zombie instead
```

**What happens**:
1. Bot switches to new instruction
2. Previous task is abandoned
3. Bot starts attacking zombie

### Example 3: Resetting AI State

**In Minecraft chat**:
```
<Player> reset
```

**What happens**:
1. AI memory/history is cleared
2. Bot returns to idle state
3. Bot position unchanged
4. Ready for new instructions

### Example 4: Complex Task

**In Minecraft chat**:
```
<Player> build a small house with a door
```

**What happens**:
1. Agent reasons about the task
2. Collects materials
3. Places blocks
4. Crafts and places door

## Action Mapping Details

### VPT Action Space → Mineflayer Commands

JarvisVLA outputs VPT-style actions. We map them to Mineflayer:

| VPT Action | Mineflayer Command | Notes |
|------------|-------------------|-------|
| `camera: [dy, dp]` | `bot.look(yaw, pitch)` | Converted from delta to absolute |
| `buttons.forward: 1` | `bot.setControlState('forward', true)` | Movement control |
| `buttons.attack: 1` | `bot.attack(target)` | Attack entity/break block |
| `buttons.use: 1` | `bot.activateItem()` | Use item/right-click |
| `buttons.jump: 1` | `bot.setControlState('jump', true)` | Jump/swim up |
| `buttons.sneak: 1` | `bot.setControlState('sneak', true)` | Sneak/crouch |
| `buttons.sprint: 1` | `bot.setControlState('sprint', true)` | Sprint |
| `buttons.hotbar.N: 1` | `bot.setQuickBarSlot(N-1)` | Switch hotbar slot |
| `buttons.inventory: 1` | `bot.creative.openInventoryWindow()` | Open inventory |

### Camera Movement

Camera actions are discretized in VPT:
- 21 bins for yaw (horizontal)
- 21 bins for pitch (vertical)
- Center bin (10, 10) = no movement
- Bin (0, 10) = max left, (20, 10) = max right
- Bin (10, 0) = max down, (10, 20) = max up

We convert to Mineflayer:
```python
# Delta conversion
delta_yaw = (camera[0] - 10) * (180 / 10)  # Max ±180 degrees
delta_pitch = (camera[1] - 10) * (90 / 10)  # Max ±90 degrees

# Apply to bot
bot.yaw += delta_yaw
bot.pitch += delta_pitch
```

### Button Actions

Buttons are binary (0 or 1). We apply them frame-by-frame:
```python
# Press buttons that are 1
for button, state in action['buttons'].items():
    if state == 1:
        apply_button(button)
```

## Code Changes

### 1. mineflayer_bridge.js - Chat & Screenshot Support

Add after line 56 (after bot event handlers):

```javascript
// Chat instruction queue
let chatInstructions = []
let processingInstruction = null

bot.on('chat', (username, message) => {
  // Ignore messages from the bot itself
  if (username === bot.username) return
  
  console.log(`[Chat] ${username}: ${message}`)
  
  // Handle reset command
  if (message.toLowerCase().trim() === 'reset') {
    console.log('[Chat] Reset command received')
    processingInstruction = null
    chatInstructions = []
    return
  }
  
  // Add new instruction
  chatInstructions.push({
    username: username,
    message: message,
    timestamp: Date.now()
  })
  console.log(`[Chat] Queued instruction: "${message}"`)
})

// Screenshot support using prismarine-viewer
let viewer = null
let viewerReady = false

async function initViewer() {
  if (!bot || !bot.entity) return false
  
  try {
    const { Viewer, WorldView } = require('prismarine-viewer').viewer
    const THREE = require('three')
    const { createCanvas } = require('canvas')
    const Vec3 = require('vec3').Vec3
    
    // Create canvas
    const width = 640
    const height = 360
    const canvas = createCanvas(width, height)
    const renderer = new THREE.WebGLRenderer({ canvas: canvas })
    
    viewer = {
      viewer: new Viewer(renderer),
      canvas: canvas,
      renderer: renderer,
      width: width,
      height: height
    }
    
    viewer.viewer.setVersion(bot.version)
    
    const botPos = bot.entity.position
    const center = new Vec3(botPos.x, botPos.y, botPos.z)
    
    const worldView = new WorldView(bot.world, 4, center)
    viewer.viewer.listen(worldView)
    viewer.worldView = worldView
    
    await worldView.init(center)
    viewerReady = true
    console.log('[Viewer] Screenshot support initialized')
    return true
  } catch (err) {
    console.error('[Viewer] Failed to initialize:', err.message)
    return false
  }
}

async function captureScreenshot() {
  if (!viewerReady || !viewer || !bot || !bot.entity) {
    // Return black image if viewer not ready
    const canvas = createCanvas(640, 360)
    const ctx = canvas.getContext('2d')
    ctx.fillStyle = 'black'
    ctx.fillRect(0, 0, 640, 360)
    return canvas.toBuffer('image/jpeg')
  }
  
  try {
    // Update camera position and rotation to match bot
    const pos = bot.entity.position
    viewer.viewer.camera.position.set(pos.x, pos.y + 1.6, pos.z)
    
    // Convert bot's yaw/pitch to camera rotation
    const yaw = bot.entity.yaw
    const pitch = bot.entity.pitch
    
    // Calculate look direction
    const x = -Math.sin(yaw) * Math.cos(pitch)
    const y = -Math.sin(pitch)
    const z = -Math.cos(yaw) * Math.cos(pitch)
    
    const lookAt = new (require('vec3').Vec3)(
      pos.x + x,
      pos.y + 1.6 + y,
      pos.z + z
    )
    
    viewer.viewer.camera.lookAt(lookAt.x, lookAt.y, lookAt.z)
    
    // Render
    viewer.renderer.render(viewer.viewer.scene, viewer.viewer.camera)
    
    // Get image buffer
    return viewer.canvas.toBuffer('image/jpeg')
  } catch (err) {
    console.error('[Viewer] Screenshot failed:', err.message)
    // Return black image on error
    const canvas = createCanvas(640, 360)
    const ctx = canvas.getContext('2d')
    ctx.fillStyle = 'black'
    ctx.fillRect(0, 0, 640, 360)
    return canvas.toBuffer('image/jpeg')
  }
}

// Initialize viewer when bot spawns
bot.on('spawn', async () => {
  setTimeout(() => {
    initViewer()
  }, 2000) // Wait 2 seconds for chunks to load
})
```

Add new endpoints before `app.listen`:

```javascript
// Get pending chat instructions
app.post('/chat/instructions', (req, res) => {
  if (!bot) {
    return res.json({ success: false, error: 'Bot not initialized' })
  }
  
  res.json({
    success: true,
    instructions: chatInstructions,
    current: processingInstruction
  })
})

// Mark instruction as being processed
app.post('/chat/start_instruction', (req, res) => {
  if (!bot) {
    return res.json({ success: false, error: 'Bot not initialized' })
  }
  
  if (chatInstructions.length > 0) {
    processingInstruction = chatInstructions.shift()
    res.json({ success: true, instruction: processingInstruction })
  } else {
    res.json({ success: true, instruction: null })
  }
})

// Clear current instruction (on reset or completion)
app.post('/chat/clear_instruction', (req, res) => {
  if (!bot) {
    return res.json({ success: false, error: 'Bot not initialized' })
  }
  
  processingInstruction = null
  res.json({ success: true })
})

// Get screenshot
app.post('/screenshot', async (req, res) => {
  if (!bot) {
    return res.json({ success: false, error: 'Bot not initialized' })
  }
  
  try {
    const imageBuffer = await captureScreenshot()
    const base64Image = imageBuffer.toString('base64')
    
    res.json({
      success: true,
      image: base64Image,
      format: 'jpeg',
      width: 640,
      height: 360
    })
  } catch (err) {
    res.json({ success: false, error: err.message })
  }
})
```

### 2. mineflayer_env.py - Add POV & Chat Methods

Add after the `reset()` method (around line 160):

```python
def get_pov_image(self):
    """
    Get POV image from bot
    Returns PIL Image (360x640) matching JarvisVLA expected format
    """
    try:
        response = requests.post(f"{self.bridge_url}/screenshot", timeout=5)
        data = response.json()
        
        if data.get('success'):
            import base64
            from PIL import Image
            import io
            
            # Decode base64 image
            image_data = base64.b64decode(data['image'])
            image = Image.open(io.BytesIO(image_data))
            
            # Ensure correct size (360x640 for JarvisVLA)
            if image.size != (640, 360):
                image = image.resize((640, 360))
            
            return image
        else:
            # Return black image on failure
            from PIL import Image
            return Image.new('RGB', (640, 360), color='black')
    except Exception as e:
        print(f"[MineflayerEnv] Screenshot error: {e}")
        from PIL import Image
        return Image.new('RGB', (640, 360), color='black')

def get_chat_instructions(self):
    """
    Get pending chat instructions
    Returns list of instructions or None
    """
    try:
        response = requests.post(f"{self.bridge_url}/chat/instructions", timeout=2)
        data = response.json()
        
        if data.get('success'):
            return {
                'pending': data.get('instructions', []),
                'current': data.get('current')
            }
        return None
    except Exception as e:
        print(f"[MineflayerEnv] Chat instruction error: {e}")
        return None

def start_chat_instruction(self):
    """
    Mark next instruction as being processed
    Returns the instruction dict or None
    """
    try:
        response = requests.post(f"{self.bridge_url}/chat/start_instruction", timeout=2)
        data = response.json()
        
        if data.get('success'):
            return data.get('instruction')
        return None
    except Exception as e:
        print(f"[MineflayerEnv] Start instruction error: {e}")
        return None

def clear_chat_instruction(self):
    """Clear current instruction"""
    try:
        response = requests.post(f"{self.bridge_url}/chat/clear_instruction", timeout=2)
        return response.json().get('success', False)
    except Exception as e:
        print(f"[MineflayerEnv] Clear instruction error: {e}")
        return False
```

### 3. server_mineflayer.py - Chat-Based Interaction

Replace the entire `run()` method (starting at line 80):

```python
def run(self):
    """Main loop with chat-based instruction handling"""
    self.running = True
    
    print(f"[Server] Starting AI agent loop")
    print(f"[Server] Default instruction: {self.instruction}")
    print(f"[Server] Listening for chat commands...")
    print(f"[Server] Type any message in Minecraft chat to give JarvisAI a task")
    print(f"[Server] Type 'reset' to clear AI state")
    print(f"[Server] Human players can join: {self.mc_server_host}:{self.mc_server_port}")
    print("[Server] Press Ctrl+C to stop")
    
    # Reset environment
    obs, info = self.env.reset()
    
    step_count = 0
    current_instruction = self.instruction
    last_chat_check = time.time()
    chat_check_interval = 1.0  # Check for new chat every 1 second
    
    try:
        while self.running:
            if self.max_steps and step_count >= self.max_steps:
                print(f"[Server] Reached max steps ({self.max_steps})")
                break
            
            # Check for new chat instructions periodically
            if time.time() - last_chat_check >= chat_check_interval:
                chat_data = self.env.get_chat_instructions()
                if chat_data:
                    # Check for reset command
                    pending = chat_data.get('pending', [])
                    for msg in pending:
                        if msg['message'].lower().strip() == 'reset':
                            print(f"[Server] Reset command from {msg['username']}")
                            if self.agent:
                                self.agent.reset()
                            self.env.clear_chat_instruction()
                            current_instruction = self.instruction
                            print(f"[Server] AI state cleared, waiting for new instruction")
                            break
                    
                    # Check for new task instruction
                    if not chat_data.get('current') and pending:
                        new_instr = self.env.start_chat_instruction()
                        if new_instr:
                            current_instruction = new_instr['message']
                            print(f"[Server] New instruction from {new_instr['username']}: {current_instruction}")
                            if self.agent:
                                self.agent.set_instruction(current_instruction)
                
                last_chat_check = time.time()
            
            # Get POV image
            pov_image = self.env.get_pov_image()
            obs['pov'] = pov_image
            
            # Get action from agent
            if self.agent:
                try:
                    action = self.agent.get_action(obs, verbos=self.verbos)
                    if self.verbos:
                        print(f"[Server] Step {step_count}: {action}")
                except Exception as e:
                    print(f"[Server] Agent error: {e}")
                    import traceback
                    traceback.print_exc()
                    action = self.env.noop_action()
            else:
                # Random/noop action if no agent
                action = self.env.noop_action()
            
            # Execute action
            obs, reward, terminated, truncated, info = self.env.step(action)
            
            if terminated or truncated:
                print(f"[Server] Episode ended, resetting...")
                obs, info = self.env.reset()
                if self.agent:
                    self.agent.reset()
            
            step_count += 1
            time.sleep(self.step_delay)
            
            # Print status every 100 steps
            if step_count % 100 == 0:
                health = obs.get('health', 0)
                pos = obs.get('position') or {}
                print(f"[Server] Step {step_count} | Health: {health} | Pos: ({pos.get('x',0):.1f}, {pos.get('y',0):.1f}, {pos.get('z',0):.1f}) | Task: {current_instruction[:50]}")
    
    except KeyboardInterrupt:
        print("\n[Server] Shutting down...")
    finally:
        self.cleanup()
```

Also update `vllm_agent_adapter.py` to add `set_instruction` method after line 70:

```python
def set_instruction(self, instruction: str):
    """Update the current instruction"""
    self.current_instruction = instruction
    # Note: Agent automatically uses the instruction passed to get_action
    # This is just for tracking
```

## Testing

### Test 1: Basic Connection
```bash
python server_mineflayer.py --mc-host localhost --mc-port 25565 --max-steps 50
```
Expected: Bot connects, no errors

### Test 2: Screenshot Capture
Check console output for "[Viewer] Screenshot support initialized"

### Test 3: Chat Detection
In Minecraft, type: "test message"
Expected console: "[Chat] Player: test message"

### Test 4: Full Integration
```bash
python server_mineflayer.py \
    --mc-host 2.tcp.us-cal-1.ngrok.io \
    --mc-port 19335 \
    --vllm-url http://localhost:8000/v1 \
    --checkpoint /models/qwen2-vl-7b \
    --verbos
```

In Minecraft: "collect 10 wood logs"
Expected: Bot starts collecting wood

## Troubleshooting

### Issue: "Cannot find module 'prismarine-viewer'"
**Solution**: `npm install prismarine-viewer`

### Issue: Black screen only
**Cause**: Viewer not initialized yet or chunks not loaded
**Solution**: Wait ~5 seconds after bot spawns

### Issue: Chat not detected
**Check**:
1. Bot username is correct
2. Bot is not in spectator mode
3. Messages are in global chat (not /msg)

### Issue: Agent not responding
**Check**:
1. VLLM server is running: `curl http://localhost:8000/v1/models`
2. Checkpoint path is correct
3. Check `--verbos` flag for errors

### Issue: Actions not executing
**Check**: Action mapping in `mineflayer_env.py` - some actions might not be implemented yet

## Next Steps

1. **Improve action mapping**: Add more VPT actions (inventory management, crafting, etc.)
2. **Add task completion detection**: Detect when task is done
3. **Add safety limits**: Prevent bot from wandering too far
4. **Add context**: Include inventory/nearby blocks in instruction
5. **Multi-turn dialogue**: Support follow-up questions

## Summary

This implementation provides a simple, robust way to interact with JarvisAI:
- ✅ Chat-based instructions
- ✅ Real POV images
- ✅ Action mapping
- ✅ Reset functionality
- ✅ Simple and well-documented

The bot will listen to Minecraft chat, process visual observations, and execute actions based on your instructions!
