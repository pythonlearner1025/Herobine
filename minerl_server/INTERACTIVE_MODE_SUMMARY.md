# Interactive Mode Complete Guide

## What is Interactive Mode?

**Interactive mode allows human players to connect their Minecraft client to the agent's world and spectate/interact in real-time.**

This is a built-in MineRL feature that:
- Launches a Minecraft client on your local computer
- Connects it to the remote MineRL environment
- Lets you see exactly what the agent sees (plus more!)
- Works over SSH port forwarding

---

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  YOUR LOCAL COMPUTER                                         │
│                                                              │
│  1. SSH Port Forward: 6666 → server:6666                    │
│                                                              │
│  2. Run interactor:                                          │
│     python3 -m minestudio.simulator.minerl.interactor 6666  │
│                                                              │
│  3. Minecraft client opens automatically                     │
│                                                              │
│  4. You join the agent's world                               │
│                                                              │
└───────────────────────┬──────────────────────────────────────┘
                        │
                        │ Port 6666 (forwarded via SSH)
                        │
┌───────────────────────▼──────────────────────────────────────┐
│  REMOTE SERVER                                               │
│                                                              │
│  1. MineRL environment running                               │
│  2. Interactive mode enabled on port 6666                    │
│  3. Agent executing actions                                  │
│  4. Minecraft 1.16.5 + Malmo rendering                       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Setup Instructions

### Step 1: Enable Interactive Mode on Server

```bash
cd /workspace/Herobine/minerl_server

python server_minerl.py \
  --checkpoint /path/to/jarvis_vla_model \
  --interactive-port 6666 \
  --instruction "Build a house"
```

**Output:**
```
✓ MineRL environment ready!
✓ Agent initialized!

============================================================
INTERACTIVE MODE INSTRUCTIONS:
============================================================

To connect your Minecraft client:

1. On your LOCAL computer, forward the port:
   ssh -L 6666:localhost:6666 user@server

2. Install MineStudio on your local computer:
   pip install minestudio

3. Start the interactor:
   python3 -m minestudio.simulator.minerl.interactor 6666 --ip localhost

4. A Minecraft window will open - you'll be in the agent's world!

5. To spectate without being seen by agent:
   Press 't' and type: /gamemode sp

============================================================
```

### Step 2: Forward Port (Local Computer - Terminal 1)

```bash
ssh -L 6666:localhost:6666 user@your-server-ip
```

**Keep this terminal open!** The port forward stays active as long as SSH is connected.

### Step 3: Install MineStudio (Local Computer)

```bash
# One-time setup
pip install minestudio

# Verify
python3 -c "from minestudio.simulator.minerl import interactor; print('✓ Ready')"
```

### Step 4: Connect Interactor (Local Computer - Terminal 2)

```bash
python3 -m minestudio.simulator.minerl.interactor 6666 --ip localhost
```

**What happens:**
1. MineStudio launches Minecraft 1.16.5 client
2. Client connects to the agent's world
3. You spawn in the world
4. You can see the agent as another player

### Step 5: Become Invisible (Optional)

To spectate without interfering:

```
Press 't' (opens chat)
Type: /gamemode sp
Press Enter
```

You're now in **spectator mode** - invisible to the agent!

---

## Port Forwarding Options

### Option 1: SSH Port Forward (Recommended)

**Pros:** Secure, easy, works everywhere  
**Cons:** Requires SSH access

```bash
ssh -L 6666:localhost:6666 user@server
```

### Option 2: Direct Connection

**Pros:** Simple, no SSH needed  
**Cons:** Requires firewall rules, less secure

```bash
# On server: Allow port 6666
sudo ufw allow 6666

# On local:
python3 -m minestudio.simulator.minerl.interactor 6666 --ip server-public-ip
```

### Option 3: Ngrok

**Pros:** Works through NAT  
**Cons:** Additional service, potential latency

```bash
# On server:
ngrok tcp 6666
# Shows: tcp://0.tcp.ngrok.io:12345

# On local:
python3 -m minestudio.simulator.minerl.interactor 12345 --ip 0.tcp.ngrok.io
```

---

## What You Can Do

### As Observer (Spectator Mode)

```
/gamemode sp        - Become invisible spectator
/tp <x> <y> <z>     - Teleport to coordinates
/time set day       - Change time
```

- Fly through walls
- Watch agent from any angle
- No collision with world
- Agent can't see you

### As Participant (Survival Mode)

```
/gamemode survival  - Return to survival mode
```

- Interact with same world
- Can affect agent's environment
- Agent can see you
- Be careful not to interfere!

### Recording

- Use OBS or other screen recording software
- Record the Minecraft window
- Perfect for creating demo videos!

---

## Multiple Spectators

You can have **multiple people** watching the same agent:

**Person 1's local computer:**
```bash
ssh -L 6666:localhost:6666 user@server
python3 -m minestudio.simulator.minerl.interactor 6666 --ip localhost
```

**Person 2's local computer:**
```bash
ssh -L 6667:localhost:6666 user@server  # Different local port
python3 -m minestudio.simulator.minerl.interactor 6667 --ip localhost
```

Everyone sees the same world in real-time!

---

## Troubleshooting

### "Connection refused"

**Cause:** Server not running or port not forwarded

**Fix:**
```bash
# Check server is running
ps aux | grep server_minerl

# Check port forward
netstat -an | grep 6666  # Should show LISTEN

# Restart port forward
ssh -L 6666:localhost:6666 user@server
```

### "Interactor hangs at 'Starting client'"

**Cause:** Java not installed or wrong version

**Fix:**
```bash
# Install Java 8 on LOCAL computer
conda install --channel=conda-forge openjdk=8 -y

# Verify
java -version  # Should be 1.8.0_xxx
```

### "Cannot connect to X server"

**Cause:** No display on local computer (rare)

**Fix:**
```bash
# Use Xvfb
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 &
python3 -m minestudio.simulator.minerl.interactor 6666 --ip localhost
```

### "Minecraft crashes immediately"

**Cause:** Memory issue or Java version

**Fix:**
```bash
# Increase Java memory
export _JAVA_OPTIONS="-Xmx4G"
python3 -m minestudio.simulator.minerl.interactor 6666 --ip localhost
```

---

## Performance Notes

### Real-time Mode (Default)

```bash
python server_minerl.py --interactive-port 6666 ...
```

- Agent runs at **human-watchable speed** (~20 FPS)
- Perfect for spectating
- Uses `interactive_realtime=True`

### Fast Mode (Not Recommended for Interactive)

```bash
python server_minerl.py --interactive-port 6666 --no-realtime ...
```

- Agent runs at **full speed** (50+ FPS)
- Too fast for humans to watch
- Only use if you want to stress-test

---

## Use Cases

### 1. **Research & Development**
- Watch agent behavior in real-time
- Identify failure modes visually
- Debug action execution
- Understand agent's "thinking" process

### 2. **Demos & Presentations**
- Show live agent performance
- Record videos for papers/blogs
- Share with collaborators
- Create engaging visualizations

### 3. **Multi-Agent Scenarios**
- Have multiple agents in same world
- Human can provide interventions
- Test agent-human interaction
- Collaborative task completion

### 4. **Teaching & Tutorials**
- Students can watch AI play
- Explain agent decisions visually
- Compare human vs AI strategies
- Interactive learning experience

---

## Advanced Configuration

### Custom Port

```bash
python server_minerl.py --interactive-port 8888 ...

# On local:
python3 -m minestudio.simulator.minerl.interactor 8888 --ip localhost
```

### Multiple Agents, Multiple Ports

```bash
# Agent 1
python server_minerl.py --interactive-port 6666 --instruction "Mine" &

# Agent 2
python server_minerl.py --interactive-port 6667 --instruction "Build" &

# Watch both simultaneously!
```

### Disable Interactive Mid-Run

Interactive mode is set at environment creation. To disable:
```python
env = MineRLEnv(interactive_port=None)  # No interactive mode
```

---

## Comparison with Other Approaches

| Method | Pros | Cons |
|--------|------|------|
| **Interactive Mode** | Real-time, proper Minecraft client, multiplayer | Requires port forward |
| **Screenshot logs** | Simple, no network needed | Not real-time, tedious |
| **Video recording** | Good for archival | Can't interact, large files |
| **Web viewer** | Browser-based | Prismarine limitations (no hands) |

---

## Security Considerations

### Safe Practices

✅ Use SSH port forwarding (encrypted)  
✅ Limit to localhost (not 0.0.0.0)  
✅ Use firewall rules if direct connection  
✅ Don't expose port publicly without auth  

### Unsafe Practices

❌ Binding to 0.0.0.0 without firewall  
❌ Using unsecured ngrok public URLs  
❌ Allowing unknown players to connect  

---

## Example Session

**Full workflow:**

```bash
# ============================================
# TERMINAL 1: Server (remote)
# ============================================
cd /workspace/Herobine/minerl_server

python server_minerl.py \
  --checkpoint /path/to/model \
  --interactive-port 6666 \
  --instruction "Build a house" \
  --max-steps 1000

# Output: "Interactive mode enabled on port 6666"
# Keep running...


# ============================================
# TERMINAL 2: Local computer (port forward)
# ============================================
ssh -L 6666:localhost:6666 user@server-ip

# Keep open!


# ============================================
# TERMINAL 3: Local computer (interactor)
# ============================================
python3 -m minestudio.simulator.minerl.interactor 6666 --ip localhost

# Minecraft launches...
# You're in the world!

# In Minecraft:
# Press 't'
# Type: /gamemode sp
# Now you're invisible and can fly around!
```

---

## FAQ

**Q: Can I control the agent?**  
A: No, you're a spectator. The agent controls the main player.

**Q: Can I modify the world?**  
A: Yes, if you're in survival/creative mode. But this affects the agent!

**Q: Does the agent see me?**  
A: Only if you're in survival mode. Use `/gamemode sp` to be invisible.

**Q: Can I use mods?**  
A: No, Malmo uses vanilla Minecraft 1.16.5.

**Q: Does this work over the internet?**  
A: Yes! Use SSH port forwarding or ngrok.

**Q: Multiple spectators at once?**  
A: Yes! Each person runs the interactor command separately.

---

## Summary

**Interactive mode is a powerful feature that:**
- ✅ Lets you watch agents in real-time
- ✅ Works over network via port forwarding
- ✅ Supports multiple spectators
- ✅ Uses real Minecraft client (not headless)
- ✅ Perfect for demos, debugging, research

**Requirements:**
- MineRL 0.4.4+ (included in MineStudio)
- Java 8 on both server and local
- SSH access or port forwarding capability

**Next step:** Try it yourself!

```bash
python server_minerl.py --checkpoint <path> --interactive-port 6666
```

---

**Watch your AI agent play Minecraft in real-time!** 🎮🤖

