"""
MineRL-based Agent Server for JarvisVLA
Uses proper Minecraft client rendering for first-person POV with hands

Supports interactive mode - humans can connect their Minecraft client
to watch/interact with the agent in real-time.
"""

import time
import sys
from pathlib import Path
import logging
from PIL import Image
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from minerl_server.minerl_env import MineRLEnv

# Import JarvisVLA agent directly
from jarvisvla.evaluate import agent_wrapper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MineRLAgentServer:
    """
    Main server that runs JarvisVLA agent in MineRL environment
    Supports interactive mode for human spectators/players
    """
    
    def __init__(
        self,
        checkpoint_path: str,
        vllm_base_url: str = "http://localhost:8000/v1",
        log_dir: str = "agent_logs_minerl",
        fps: int = 20,
        temperature: float = 0.7,
        interactive_port: int = None,
        interactive_realtime: bool = True,
    ):
        """
        Initialize MineRL agent server
        
        Args:
            checkpoint_path: Path to JarvisVLA checkpoint
            vllm_base_url: URL of VLLM server
            log_dir: Directory to save screenshots and logs
            fps: Target FPS for agent loop
            temperature: VLLM sampling temperature
            interactive_port: If set, enables interactive mode on this port
            interactive_realtime: If True, slows tick speed to real-time
        """
        self.checkpoint_path = checkpoint_path
        self.vllm_base_url = vllm_base_url
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True, parents=True)
        self.fps = fps
        self.step_delay = 1.0 / fps
        self.interactive_port = interactive_port
        
        # Initialize environment (THIS WILL USE REAL MINECRAFT CLIENT!)
        logger.info("Initializing MineRL environment...")
        logger.info("  - Minecraft 1.16.5 with Malmo")
        logger.info("  - First-person POV with hands visible")
        logger.info("  - Real Minecraft HUD and GUI")
        
        if interactive_port:
            logger.info(f"  - Interactive mode enabled on port {interactive_port}")
            logger.info(f"    Connect with: python3 -m minestudio.simulator.minerl.interactor {interactive_port}")
            logger.info(f"    (Use port forwarding if running on remote server)")
        
        self.env = MineRLEnv(
            obs_size=(360, 640),
            render_size=(360, 640),
            interactive_port=interactive_port,
            interactive_realtime=interactive_realtime,
        )
        logger.info("✓ MineRL environment ready!")
        
        # Initialize agent (using JarvisVLA directly)
        logger.info(f"Initializing JarvisVLA agent with {vllm_base_url}...")
        self.agent = agent_wrapper.VLLM_AGENT(
            checkpoint_path=checkpoint_path,
            base_url=vllm_base_url,
            temperature=temperature,
            history_num=0,
            action_chunk_len=1,
            instruction_type='normal',
        )
        logger.info("✓ Agent initialized!")
        
        self.current_instruction = None
        
        if interactive_port:
            logger.info("")
            logger.info("=" * 60)
            logger.info("INTERACTIVE MODE INSTRUCTIONS:")
            logger.info("=" * 60)
            logger.info("")
            logger.info("To connect your Minecraft client:")
            logger.info("")
            logger.info("1. On your LOCAL computer, forward the port:")
            logger.info(f"   ssh -L {interactive_port}:localhost:{interactive_port} user@server")
            logger.info("")
            logger.info("2. Install MineStudio on your local computer:")
            logger.info("   pip install minestudio")
            logger.info("")
            logger.info("3. Start the interactor:")
            logger.info(f"   python3 -m minestudio.simulator.minerl.interactor {interactive_port} --ip localhost")
            logger.info("")
            logger.info("4. A Minecraft window will open - you'll be in the agent's world!")
            logger.info("")
            logger.info("5. To spectate without being seen by agent:")
            logger.info("   Press 't' and type: /gamemode sp")
            logger.info("")
            logger.info("=" * 60)
            logger.info("")
        
        self.step_count = 0
        self.running = False
        
    def run_episode(self, instruction: str, max_steps: int = 1000):
        """
        Run single episode with given instruction
        
        Args:
            instruction: Task instruction for agent
            max_steps: Maximum steps per episode
        """
        logger.info(f"Starting episode with instruction: {instruction}")
        
        # Reset environment
        obs, info = self.env.reset()
        self.agent.reset()
        self.current_instruction = instruction
        
        if self.interactive_port:
            logger.info("")
            logger.info("=" * 60)
            logger.info("Episode started - you can now connect your Minecraft client!")
            logger.info(f"Command: python3 -m minestudio.simulator.minerl.interactor {self.interactive_port}")
            logger.info("=" * 60)
            logger.info("")
        
        self.running = True
        self.step_count = 0
        
        # Main loop
        while self.running and self.step_count < max_steps:
            step_start = time.time()
            
            try:
                # Get POV image (THIS WILL HAVE HANDS!)
                pov_image = obs['pov']
                
                # Save screenshot for debugging
                if self.step_count % 10 == 0:  # Save every 10 steps
                    screenshot_path = self.log_dir / f"step_{self.step_count:05d}_input.jpg"
                    pov_image.save(screenshot_path, quality=95)
                
                # Log observation info
                if self.step_count % 20 == 0:
                    logger.info(
                        f"Step {self.step_count}: "
                        f"pos=({obs['position']['x']:.1f}, {obs['position']['y']:.1f}, {obs['position']['z']:.1f}), "
                        f"health={obs['health']}, food={obs['food']}"
                    )
                
                # Get action from agent
                # JarvisVLA agent.forward() returns actions directly compatible with MineRL
                action = self.agent.forward(
                    observations=[pov_image],  # List of images
                    instructions=[self.current_instruction],  # List of instructions
                    verbos=(self.step_count % 20 == 0),
                    need_crafting_table=False
                )
                
                # Execute action
                obs, reward, terminated, truncated, info = self.env.step(action)
                
                # Check termination
                if terminated or truncated:
                    logger.info(f"Episode ended at step {self.step_count}")
                    break
                
                self.step_count += 1
                
                # Maintain FPS
                elapsed = time.time() - step_start
                if elapsed < self.step_delay:
                    time.sleep(self.step_delay - elapsed)
                
                actual_fps = 1.0 / max(elapsed, 0.001)
                if self.step_count % 100 == 0:
                    logger.info(f"Running at {actual_fps:.1f} FPS")
                    
            except KeyboardInterrupt:
                logger.info("Interrupted by user")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Error at step {self.step_count}: {e}", exc_info=True)
                break
        
        logger.info(f"Episode completed: {self.step_count} steps")
        
    def run_interactive(self):
        """
        Run in interactive mode - ask for instructions via console
        """
        logger.info("Starting interactive mode")
        logger.info("Enter task instructions (or 'quit' to exit)")
        
        while True:
            try:
                instruction = input("\nEnter instruction: ").strip()
                
                if instruction.lower() in ['quit', 'exit', 'q']:
                    logger.info("Exiting...")
                    break
                
                if not instruction:
                    logger.warning("Empty instruction, skipping")
                    continue
                
                # Run episode with this instruction
                self.run_episode(instruction, max_steps=500)
                
            except KeyboardInterrupt:
                logger.info("\nInterrupted by user")
                break
            except Exception as e:
                logger.error(f"Error: {e}", exc_info=True)
        
        self.close()
    
    def close(self):
        """Clean up resources"""
        logger.info("Closing environment...")
        self.env.close()
        logger.info("Done!")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="MineRL Agent Server for JarvisVLA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with interactive mode (humans can connect)
  python server_minerl.py --checkpoint /path/to/model --interactive-port 6666
  
  # Run single episode
  python server_minerl.py --checkpoint /path/to/model --instruction "Mine stone"
  
  # Interactive console mode
  python server_minerl.py --checkpoint /path/to/model
        """
    )
    
    parser.add_argument(
        "--checkpoint",
        type=str,
        required=True,
        help="Path to JarvisVLA checkpoint",
    )
    parser.add_argument(
        "--vllm-url",
        type=str,
        default="http://localhost:8000/v1",
        help="VLLM server URL",
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default="agent_logs_minerl",
        help="Directory for logs and screenshots",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=20,
        help="Target FPS (ignored if --interactive-realtime is set)",
    )
    parser.add_argument(
        "--instruction",
        type=str,
        default=None,
        help="Task instruction (if not provided, runs interactive console mode)",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=1000,
        help="Maximum steps per episode",
    )
    parser.add_argument(
        "--interactive-port",
        type=int,
        default=None,
        help="Enable interactive mode on this port (allows human players to connect)",
    )
    parser.add_argument(
        "--no-realtime",
        action="store_true",
        help="Disable real-time mode (agent runs at full speed, not human-watchable)",
    )
    
    args = parser.parse_args()
    
    # Create server
    server = MineRLAgentServer(
        checkpoint_path=args.checkpoint,
        vllm_base_url=args.vllm_url,
        log_dir=args.log_dir,
        fps=args.fps,
        interactive_port=args.interactive_port,
        interactive_realtime=not args.no_realtime,
    )
    
    # Run
    if args.instruction:
        # Single episode mode
        server.run_episode(args.instruction, max_steps=args.max_steps)
        server.close()
    else:
        # Interactive console mode
        server.run_interactive()


if __name__ == "__main__":
    main()