"""
MineRL Environment Wrapper for JarvisVLA
Provides proper first-person POV rendering with hands, HUD, and GUI support

Note: JarvisVLA agent outputs actions directly compatible with MineRL's 
action_type="agent" mode. No action mapping needed!
"""

import numpy as np
from typing import Dict, Any, Tuple, Optional
from PIL import Image
import gymnasium as gym

from minestudio.simulator import MinecraftSim
from minestudio.simulator.callbacks import (
    RecordCallback,
    CommandsCallback,
    RewardsCallback,
)


class MineRLEnv:
    """
    Gymnasium-compatible MineRL environment wrapper for JarvisVLA
    Provides proper first-person POV with hands, HUD, and GUI support
    
    Supports interactive mode - allows human players to connect their Minecraft
    client to the agent's world via port forwarding.
    """
    
    def __init__(
        self,
        obs_size=(360, 640),  # Standard MineRL resolution (H, W)
        render_size=(360, 640),
        seed=0,
        callbacks=None,
        interactive_port: Optional[int] = None,  # Port for human interaction
        interactive_realtime: bool = True,
    ):
        """
        Initialize MineRL environment
        
        Args:
            obs_size: Observation image size (height, width)
            render_size: Render image size (height, width)
            seed: Random seed
            callbacks: List of MinecraftSim callbacks
            interactive_port: If set, enables interactive mode on this port
            interactive_realtime: If True, slows tick speed to real-time for humans
        """
        # Default callbacks - minimal set to avoid initialization issues
        if callbacks is None:
            callbacks = []  # Use empty list for simplicity
        
        # Create MineRL simulator
        # Start with 'env' type for initialization, will switch to 'agent' after setup
        self.env = MinecraftSim(
            obs_size=obs_size,
            render_size=render_size,
            seed=seed,
            callbacks=callbacks,
            action_type='env',  # Will be switched to 'agent' after reset
        )
        
        self._last_obs = None
        self.interactive_port = interactive_port
        self.interactive_realtime = interactive_realtime
        self._interactive_enabled = False
        self._action_type_switched = False
        
    def reset(self) -> Tuple[Dict, Dict]:
        """
        Reset environment
        
        Returns:
            observation: Dict with 'pov' (PIL Image) and other info
            info: Additional info dict
        """
        obs, info = self.env.reset()
        self._last_obs = obs
        
        # Enable interactive mode if port specified
        if self.interactive_port and not self._interactive_enabled:
            self.enable_interactive_mode()
        
        # Switch to agent action type (JarvisVLA outputs 'agent' format)
        if not self._action_type_switched:
            self.env.action_type = 'agent'
            self._action_type_switched = True
        
        # Convert observation to expected format
        formatted_obs = self._format_observation(obs, info)
        return formatted_obs, info
    
    def enable_interactive_mode(self):
        """
        Enable interactive mode - allows human players to connect
        
        After calling this, humans can connect with:
        python3 -m minestudio.simulator.minerl.interactor <port> --ip <server_ip>
        
        Or with port forwarding:
        python3 -m minestudio.simulator.minerl.interactor <local_port> --ip localhost
        """
        try:
            self.env.make_interactive(
                port=self.interactive_port,
                realtime=self.interactive_realtime,
                max_players=10
            )
            self._interactive_enabled = True
            print(f"✓ Interactive mode enabled on port {self.interactive_port}")
            print(f"  Connect with: python3 -m minestudio.simulator.minerl.interactor {self.interactive_port}")
        except Exception as e:
            print(f"⚠ Failed to enable interactive mode: {e}")
    
    def step(self, action: Dict) -> Tuple[Dict, float, bool, bool, Dict]:
        """
        Execute action and return new observation
        
        Args:
            action: JarvisVLA-format action dict (already compatible with MineRL 'agent' mode)
            
        Returns:
            observation: Formatted observation dict
            reward: Reward value
            terminated: Whether episode ended
            truncated: Whether episode was truncated
            info: Additional info
        """
        # JarvisVLA agent already outputs actions compatible with action_type='agent'
        # No conversion needed!
        obs, reward, terminated, truncated, info = self.env.step(action)
        self._last_obs = obs
        
        # Format observation
        formatted_obs = self._format_observation(obs, info)
        
        return formatted_obs, reward, terminated, truncated, info
    
    def _format_observation(self, obs: Dict, info: Dict) -> Dict:
        """
        Format observation to match expected format
        
        MineRL obs includes:
        - pov: np.array (H, W, 3) with proper first-person view INCLUDING HANDS
        - inventory: Dict of items
        - equipped_items: Dict of equipped items
        - location_stats: Player position/rotation
        
        Returns dict with:
        {
            'pov': PIL.Image (proper first-person with hands visible!),
            'inventory': dict,
            'equipped_items': dict,
            'position': {x, y, z},
            'rotation': {pitch, yaw},
            'health': int,
            'food': int,
        }
        """
        # Extract POV - THIS WILL HAVE HANDS VISIBLE!
        pov_array = obs.get('pov', np.zeros((360, 640, 3), dtype=np.uint8))
        pov_image = Image.fromarray(pov_array)
        
        # Extract other info
        location = info.get('location_stats', {})
        
        formatted = {
            'pov': pov_image,
            'inventory': info.get('inventory', {}),
            'equipped_items': info.get('equipped_items', {}),
            'position': {
                'x': location.get('xpos', 0),
                'y': location.get('ypos', 0),
                'z': location.get('zpos', 0),
            },
            'rotation': {
                'pitch': location.get('pitch', 0),
                'yaw': location.get('yaw', 0),
            },
            'health': info.get('health', 20),
            'food': info.get('food_level', 20),
        }
        
        return formatted
    
    def get_pov_image(self) -> Image.Image:
        """
        Get current POV image (with hands visible!)
        
        Returns:
            PIL Image of current first-person view
        """
        if self._last_obs is None:
            raise RuntimeError("No observation available. Call reset() first.")
        
        pov_array = self._last_obs.get('pov', np.zeros((360, 640, 3), dtype=np.uint8))
        return Image.fromarray(pov_array)
    
    def send_command(self, command: str):
        """Send Minecraft command via callbacks"""
        # Use CommandsCallback to send commands
        for callback in self.env.callbacks:
            if hasattr(callback, 'send_command'):
                callback.send_command(command)
                break
    
    def close(self):
        """Close environment"""
        self.env.close()
    
    @property
    def action_space(self):
        """Return action space"""
        return self.env.action_space
    
    @property
    def observation_space(self):
        """Return observation space"""
        return self.env.observation_space