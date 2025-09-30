# Critical Fix: Removed Unnecessary Action Mapping

## Problem

Initial implementation incorrectly assumed JarvisVLA needed action conversion from its output format to MineRL format. This was wrong!

## Solution

**JarvisVLA's `VLLM_AGENT.forward()` already outputs actions directly compatible with MineRL's `action_type='agent'` mode.**

No conversion needed!

## Changes Made

### 1. Removed ActionMapper Class

**Old (WRONG):**
```python
class ActionMapper:
    @staticmethod
    def jarvis_to_minerl(jarvis_action: Dict) -> Dict:
        # Complex conversion logic...
```

**New (CORRECT):**
```python
# No ActionMapper needed!
```

### 2. Switch to 'agent' Action Type

**In `minerl_env.py`:**
```python
def reset(self):
    obs, info = self.env.reset()
    
    # Switch to agent action type (JarvisVLA outputs 'agent' format)
    if not self._action_type_switched:
        self.env.action_type = 'agent'
        self._action_type_switched = True
    
    return obs, info
```

### 3. Direct Action Pass-through

**In `minerl_env.py`:**
```python
def step(self, action: Dict):
    # JarvisVLA agent already outputs actions compatible with action_type='agent'
    # No conversion needed!
    obs, reward, terminated, truncated, info = self.env.step(action)
    return obs, reward, terminated, truncated, info
```

### 4. Use JarvisVLA Agent Directly

**Old (used custom wrapper):**
```python
from bridge.vllm_agent_adapter import VLLMAgentAdapter

self.agent = VLLMAgentAdapter(...)
action = self.agent.get_action(obs)
```

**New (use JarvisVLA directly):**
```python
from jarvisvla.evaluate import agent_wrapper

self.agent = agent_wrapper.VLLM_AGENT(...)
action = self.agent.forward(
    observations=[pov_image],
    instructions=[instruction],
    verbos=False,
    need_crafting_table=False
)
```

## How It Works Now

```python
# 1. Create environment with action_type='env' (for initialization)
env = MinecraftSim(action_type='env', ...)

# 2. Reset and switch to 'agent' type
obs, info = env.reset()
env.action_type = 'agent'  # Critical step!

# 3. Get action from JarvisVLA (already in 'agent' format)
action = agent.forward([obs['pov']], [instruction], ...)

# 4. Pass action directly to environment
obs, reward, done, truncated, info = env.step(action)
# No conversion needed!
```

## Action Type Comparison

### action_type='env' (Human-friendly)
```python
{
    'forward': 0/1,
    'attack': 0/1,
    'camera': [pitch, yaw],
    # ... 20+ individual keys
}
```

### action_type='agent' (VPT-style, used by JarvisVLA)
```python
{
    'buttons': 8641,  # Single int encoding all buttons
    'camera': 121     # Single int encoding camera bins
}
```

**JarvisVLA outputs the 'agent' format directly!**

## Reference

See `/workspace/Herobine/JarvisVLA/jarvisvla/evaluate/evaluate.py`:
- Lines 106-122 show the correct usage pattern
- Line 106: `env.action_type = "agent"`
- Line 119: `action = agent.forward([info["pov"]], instructions, ...)`
- Line 122: `env.step(action)` - direct pass-through

## Summary

✅ **Removed unnecessary ActionMapper**  
✅ **Switch to action_type='agent' after reset**  
✅ **Use JarvisVLA's VLLM_AGENT directly**  
✅ **Pass actions directly to env.step()**  

**Code is now simpler and correct!**

