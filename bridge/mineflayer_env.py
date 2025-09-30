"""
Mineflayer Environment Wrapper
Mimics MineStudio's MinecraftSim interface but uses Mineflayer + real Minecraft server
"""

import numpy as np
import requests
import time
import subprocess
import os
import signal
from typing import Dict, Any, Tuple, Optional
from pathlib import Path


class MineflayerEnv:
    """
    Gym-like environment that wraps Mineflayer bot
    Compatible with MineStudio's MinecraftSim API
    """
    
    def __init__(
        self,
        server_host='localhost',
        server_port=25565,
        bot_username='AIBot',
        bridge_port=1111,
        obs_size=(360, 640),  # Height, Width - matching MineStudio
        auto_start_bridge=True
    ):
        self.server_host = server_host
        self.server_port = server_port
        self.bot_username = bot_username
        self.bridge_port = bridge_port
        self.obs_size = obs_size
        
        self.bridge_url = f"http://localhost:{bridge_port}"
        self.bridge_process = None
        self.action_type = "env"  # Compatible with MineStudio
        
        if auto_start_bridge:
            self._start_bridge()
        
        # Initialize bot
        self._init_bot()
        
    def _start_bridge(self):
        """Start the Node.js bridge server"""
        bridge_path = Path(__file__).parent / "mineflayer_bridge.js"
        if not bridge_path.exists():
            raise FileNotFoundError(f"Bridge script not found: {bridge_path}")
        
        env = os.environ.copy()
        env['MINEFLAYER_PORT'] = str(self.bridge_port)
        env['DISPLAY'] = ':99'  # Use Xvfb virtual display for WebGL
        
        # Start bridge with visible output for debugging
        self.bridge_process = subprocess.Popen(
            ['node', str(bridge_path)],
            env=env,
            stdout=None,  # Show stdout in console
            stderr=None   # Show stderr in console
        )
        
        # Wait for server to start
        time.sleep(2)
        print(f"[MineflayerEnv] Bridge server started on port {self.bridge_port}")
    
    def _init_bot(self):
        """Initialize the bot connection and wait for it to spawn"""
        try:
            response = requests.post(
                f"{self.bridge_url}/init",
                json={
                    'host': self.server_host,
                    'port': self.server_port,
                    'username': self.bot_username
                },
                timeout=10
            )
            if response.status_code == 200:
                print(f"[MineflayerEnv] Bot '{self.bot_username}' connecting to {self.server_host}:{self.server_port}")
                
                # Wait for bot to actually spawn and viewer to initialize
                print(f"[MineflayerEnv] Waiting for bot to spawn and server-side viewer to initialize...")
                print(f"[MineflayerEnv] This should take ~10-12 seconds (includes texture loading)...")
                time.sleep(12)  # Wait for: spawn (2s) + chunks (3s) + viewer init (2s) + textures (5s)
                
                # Verify bot is connected
                status = requests.get(f"{self.bridge_url}/status", timeout=2).json()
                if status.get('connected'):
                    print(f"[MineflayerEnv] ✓ Bot connected and ready")
                else:
                    print(f"[MineflayerEnv] ⚠ Bot not connected yet")
                
                # Check viewer status
                try:
                    viewer_status = requests.get(f"{self.bridge_url}/viewer/status", timeout=2).json()
                    if viewer_status.get('viewerReady'):
                        print(f"[MineflayerEnv] ✓ Viewer ready - screenshots will work")
                    else:
                        print(f"[MineflayerEnv] ⚠ Viewer not ready yet - screenshots may be black")
                        print(f"[MineflayerEnv]   Viewer status: {viewer_status}")
                except Exception as e:
                    print(f"[MineflayerEnv] ⚠ Could not check viewer status: {e}")
            else:
                print(f"[MineflayerEnv] Warning: Init returned {response.status_code}")
        except Exception as e:
            print(f"[MineflayerEnv] Error initializing bot: {e}")
    
    def reset(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Reset the environment
        Returns: (observation, info)
        """
        try:
            response = requests.post(
                f"{self.bridge_url}/reset",
                json={},
                timeout=10
            )
            data = response.json()
            
            if data.get('success'):
                obs_dict = self._process_observation(data.get('observation', {}))
                info = data.get('observation', {})
                return obs_dict, info
            else:
                raise RuntimeError(f"Reset failed: {data.get('error')}")
        except Exception as e:
            print(f"[MineflayerEnv] Reset error: {e}")
            # Return dummy observation
            return self._empty_observation(), {}
    
    def step(self, action: Dict[str, Any]) -> Tuple[Dict[str, Any], float, bool, bool, Dict[str, Any]]:
        """
        Execute action and return (obs, reward, terminated, truncated, info)
        Compatible with Gymnasium API
        """
        try:
            response = requests.post(
                f"{self.bridge_url}/action",
                json=action,
                timeout=5
            )
            data = response.json()
            
            obs_dict = self._process_observation(data.get('observation', {}))
            reward = 0.0  # TODO: Implement reward logic
            terminated = False
            truncated = False
            info = data.get('observation', {})
            
            return obs_dict, reward, terminated, truncated, info
            
        except Exception as e:
            print(f"[MineflayerEnv] Step error: {e}")
            return self._empty_observation(), 0.0, False, False, {}
    
    def _process_observation(self, raw_obs: Dict) -> Dict[str, Any]:
        """
        Process raw observation from Mineflayer into MineStudio-compatible format
        """
        # Create a dummy image (black screen) - in real implementation, 
        # you'd use mineflayer-viewer or screenshotting
        pov = np.zeros((*self.obs_size, 3), dtype=np.uint8)
        
        obs = {
            'pov': pov,
            'inventory': raw_obs.get('inventory', []),
            'position': raw_obs.get('position', {'x': 0, 'y': 0, 'z': 0}),
            'yaw': raw_obs.get('yaw', 0),
            'pitch': raw_obs.get('pitch', 0),
            'health': raw_obs.get('health', 20),
            'food': raw_obs.get('food', 20),
            'entities': raw_obs.get('entities', [])
        }
        
        return obs
    
    def _empty_observation(self) -> Dict[str, Any]:
        """Return empty observation"""
        return {
            'pov': np.zeros((*self.obs_size, 3), dtype=np.uint8),
            'inventory': [],
            'position': {'x': 0, 'y': 0, 'z': 0},
            'yaw': 0,
            'pitch': 0,
            'health': 0,
            'food': 0,
            'entities': []
        }
    
    def noop_action(self) -> Dict[str, Any]:
        """Return a no-op action"""
        return {'type': 'noop'}
    
    def get_pov_image(self):
        """Get POV image from bot (640x360 PIL Image)"""
        try:
            response = requests.post(f"{self.bridge_url}/screenshot", timeout=5)
            data = response.json()
            
            if data.get('success'):
                import base64
                from PIL import Image
                import io
                
                image_data = base64.b64decode(data['image'])
                image = Image.open(io.BytesIO(image_data))
                
                if image.size != (640, 360):
                    image = image.resize((640, 360))
                
                return image
            else:
                from PIL import Image
                return Image.new('RGB', (640, 360), color='black')
        except Exception as e:
            print(f"[MineflayerEnv] Screenshot error: {e}")
            from PIL import Image
            return Image.new('RGB', (640, 360), color='black')

    def get_chat_instructions(self):
        """Get pending chat instructions"""
        try:
            response = requests.post(f"{self.bridge_url}/chat/instructions", timeout=2)
            data = response.json()
            return {
                'pending': data.get('instructions', []),
                'current': data.get('current')
            } if data.get('success') else None
        except Exception as e:
            print(f"[MineflayerEnv] Chat error: {e}")
            return None

    def start_chat_instruction(self):
        """Mark next instruction as being processed"""
        try:
            response = requests.post(f"{self.bridge_url}/chat/start_instruction", timeout=2)
            data = response.json()
            return data.get('instruction') if data.get('success') else None
        except Exception as e:
            print(f"[MineflayerEnv] Start instruction error: {e}")
            return None

    def clear_chat_instruction(self):
        """Clear current instruction"""
        try:
            response = requests.post(f"{self.bridge_url}/chat/clear_instruction", timeout=2)
            return response.json().get('success', False)
        except:
            return False

    def close(self):
        """Clean up resources"""
        try:
            requests.post(f"{self.bridge_url}/close", timeout=2)
        except:
            pass
        
        if self.bridge_process:
            self.bridge_process.terminate()
            try:
                self.bridge_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.bridge_process.kill()
            print("[MineflayerEnv] Bridge server stopped")
    
    def __del__(self):
        self.close()


class ActionMapper:
    """
    Maps VPT-style actions from JarvisVLA to Mineflayer API calls
    VPT actions come from action_tokenizer.decode() in agent_wrapper.py
    """
    
    @staticmethod
    def jarvis_to_mineflayer(vpt_action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert VPT action format to Mineflayer format
        
        VPT action from action_tokenizer.decode():
        {
            'buttons': Buttons object (VPT button state),
            'camera': np.array([pitch_delta, yaw_delta])
        }
        
        Args:
            vpt_action: Action dict from VLLM_AGENT.forward()
            
        Returns:
            Mineflayer-compatible action dict
        """
        # Extract camera and buttons
        camera = vpt_action.get('camera', np.array([0, 0]))
        buttons = vpt_action.get('buttons', {})
        
        # Convert camera to Python list
        if isinstance(camera, np.ndarray):
            camera = [int(x) for x in camera.tolist()]
        elif isinstance(camera, (int, np.integer)):
            # Single value - split into [pitch, yaw]
            camera = [int(camera), 0]
        elif isinstance(camera, list):
            camera = [int(x) for x in camera]
        
        # Convert Buttons object to dict and handle numpy types
        if hasattr(buttons, '__dict__'):
            button_dict = {}
            for key, val in buttons.__dict__.items():
                if isinstance(val, (np.integer, np.floating)):
                    button_dict[key] = int(val) if isinstance(val, np.integer) else float(val)
                else:
                    button_dict[key] = val
        else:
            button_dict = buttons if isinstance(buttons, dict) else {}
        
        # Build Mineflayer action
        mf_action = {
            'type': 'compound',
            'camera': camera,
            'buttons': button_dict
        }
        
        return mf_action

