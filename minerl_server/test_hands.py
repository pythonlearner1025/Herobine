#!/usr/bin/env python3
"""
Quick test to verify MineRL hands visibility
"""

import sys
import os
import numpy as np
from PIL import Image

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_minerl_hands():
    """Test if MineRL environment shows hands"""
    print("=" * 70)
    print("MineRL Hand Visibility Test")
    print("=" * 70)
    print()
    
    try:
        from minerl_server.minerl_env import MineRLEnv
        
        # Create environment
        print("Creating MineRL environment...")
        print("  (This may take 10-15 seconds on first run)")
        env = MineRLEnv(obs_size=(360, 640), render_size=(360, 640))
        
        # Reset and get observation
        print("Resetting environment...")
        obs, info = env.reset()
        
        # Get POV
        pov_image = obs['pov']
        print(f"✓ Got POV image: {pov_image.size}")
        
        # Save screenshot
        screenshot_path = "test_minerl_screenshot.png"
        pov_image.save(screenshot_path)
        print(f"✓ Saved screenshot to: {screenshot_path}")
        
        # Analyze hand region (bottom-center of screen)
        arr = np.array(pov_image)
        height, width = arr.shape[:2]
        
        # Hand region: bottom 25% of screen, center 40% horizontally
        hand_region = arr[int(height * 0.75):, int(width * 0.3):int(width * 0.7), :]
        
        # Calculate statistics
        mean_brightness = hand_region.mean()
        std_brightness = hand_region.std()
        unique_colors = len(np.unique(hand_region.reshape(-1, 3), axis=0))
        
        print()
        print("Hand Region Analysis:")
        print(f"  Region shape: {hand_region.shape}")
        print(f"  Mean brightness: {mean_brightness:.1f}/255")
        print(f"  Std brightness: {std_brightness:.1f}")
        print(f"  Unique colors: {unique_colors}")
        
        # Heuristic check
        print()
        if mean_brightness > 80 and unique_colors > 100:
            print("✓✓✓ HANDS LIKELY VISIBLE! ✓✓✓")
            print("    (High brightness and color diversity in bottom region)")
            success = True
        else:
            print("⚠ HANDS MAY NOT BE VISIBLE")
            print("  (Low brightness/color diversity in bottom region)")
            print("  Please visually inspect the saved screenshot.")
            success = False
        
        # Create visualization with matplotlib if available
        try:
            import matplotlib.pyplot as plt
            
            fig, axes = plt.subplots(1, 2, figsize=(12, 5))
            
            # Full POV
            axes[0].imshow(arr)
            axes[0].set_title("Full POV (MineRL)")
            axes[0].axis('off')
            
            # Hand region highlighted
            axes[1].imshow(arr)
            import matplotlib.patches as patches
            rect = patches.Rectangle(
                (int(width * 0.3), int(height * 0.75)),
                int(width * 0.4), int(height * 0.25),
                linewidth=2, edgecolor='red', facecolor='none'
            )
            axes[1].add_patch(rect)
            axes[1].set_title("Hand Region (red box)")
            axes[1].axis('off')
            
            viz_path = "test_minerl_hand_analysis.png"
            plt.tight_layout()
            plt.savefig(viz_path, dpi=100)
            print(f"\n✓ Saved visualization to: {viz_path}")
        except ImportError:
            print("\n(matplotlib not available - skipping visualization)")
        
        env.close()
        
        print()
        print("=" * 70)
        print("NEXT STEPS:")
        print("=" * 70)
        print("1. Open test_minerl_screenshot.png")
        print("2. Look at the bottom-center of the image")
        print("3. Check if you can see player hands/arms")
        print()
        if success:
            print("✓ If hands are visible → MineRL setup is correct!")
            print("✓ You can now run the full agent server")
        else:
            print("⚠ If hands are NOT visible → may need config adjustments")
        print("=" * 70)
        
        return success
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_minerl_hands()
    sys.exit(0 if success else 1)

