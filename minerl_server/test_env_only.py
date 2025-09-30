#!/usr/bin/env python3
"""
Test MineRL environment without agent
Verifies environment setup and hands visibility
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from minerl_server.minerl_env import MineRLEnv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_env():
    """Test environment creation and basic functionality"""
    logger.info("=" * 70)
    logger.info("MineRL Environment Test (No Agent)")
    logger.info("=" * 70)
    
    try:
        # Create environment
        logger.info("Creating MineRL environment...")
        env = MineRLEnv(
            obs_size=(360, 640),
            render_size=(360, 640),
        )
        logger.info("✓ Environment created successfully!")
        
        # Reset
        logger.info("Resetting environment...")
        obs, info = env.reset()
        logger.info("✓ Environment reset successful!")
        
        # Check observation
        logger.info(f"Observation keys: {list(obs.keys())}")
        logger.info(f"POV image size: {obs['pov'].size}")
        logger.info(f"Position: {obs['position']}")
        logger.info(f"Health: {obs['health']}, Food: {obs['food']}")
        
        # Save screenshot
        screenshot_path = "test_env_screenshot.png"
        obs['pov'].save(screenshot_path)
        logger.info(f"✓ Saved screenshot to: {screenshot_path}")
        
        # Check hands visibility
        import numpy as np
        arr = np.array(obs['pov'])
        height, width = arr.shape[:2]
        hand_region = arr[int(height * 0.75):, int(width * 0.3):int(width * 0.7), :]
        mean_brightness = hand_region.mean()
        unique_colors = len(np.unique(hand_region.reshape(-1, 3), axis=0))
        
        logger.info("")
        logger.info("Hand Region Analysis:")
        logger.info(f"  Mean brightness: {mean_brightness:.1f}/255")
        logger.info(f"  Unique colors: {unique_colors}")
        
        if mean_brightness > 80 and unique_colors > 100:
            logger.info("✓✓✓ HANDS LIKELY VISIBLE! ✓✓✓")
            success = True
        else:
            logger.info("⚠ Hands may not be visible")
            success = False
        
        # Test a few steps with noop action
        logger.info("")
        logger.info("Testing environment steps with noop actions...")
        for i in range(5):
            # Noop action for action_type='agent'
            action = {'buttons': 0, 'camera': 0}
            obs, reward, terminated, truncated, info = env.step(action)
            logger.info(f"  Step {i+1}: reward={reward}, terminated={terminated}")
        
        logger.info("✓ Environment stepping works!")
        
        # Cleanup
        env.close()
        logger.info("✓ Environment closed")
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("SUCCESS: Environment is working properly!")
        logger.info("=" * 70)
        logger.info("")
        logger.info("Next step: Run with actual JarvisVLA checkpoint")
        logger.info(f"  python server_minerl.py --checkpoint <path_to_model>")
        
        return success
        
    except Exception as e:
        logger.error(f"✗ Error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_env()
    sys.exit(0 if success else 1)

