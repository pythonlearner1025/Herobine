"""
Minecraft Server with AI Agent (using Mineflayer)
- Runs a Minecraft server where human players can join
- AI agent (via VLLM) controls a bot in the same world
- Compatible with JarvisVLA's agent architecture
"""

import argparse
import time
import signal
import sys
import json
from datetime import datetime
from pathlib import Path

from mineflayer_env import MineflayerEnv
from vllm_agent_adapter import VLLMAgentAdapter


class MinecraftAIServer:
    """
    Server that runs AI agent in Minecraft world alongside human players
    """
    
    def __init__(
        self,
        # Minecraft server config
        mc_server_host='localhost',
        mc_server_port=25565,
        bot_username='JarvisAI',
        
        # VLLM config
        vllm_base_url=None,
        checkpoint_path=None,
        
        # Agent config
        instruction="Explore and survive in Minecraft",
        temperature=0.7,
        history_num=0,
        instruction_type='normal',
        action_chunk_len=1,
        
        # Loop config
        max_steps=None,
        step_delay=0.05,  # 20 fps
        verbos=False
    ):
        self.mc_server_host = mc_server_host
        self.mc_server_port = mc_server_port
        self.bot_username = bot_username
        self.instruction = instruction
        self.max_steps = max_steps
        self.step_delay = step_delay
        self.verbos = verbos
        
        # Setup logging directory
        self.log_dir = Path('/workspace/Herobine/bridge/agent_logs')
        self.log_dir.mkdir(exist_ok=True)
        self.session_log = self.log_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        self.step_log_counter = 0
        
        # Initialize environment
        print(f"[Server] Connecting bot to Minecraft server at {mc_server_host}:{mc_server_port}")
        self.env = MineflayerEnv(
            server_host=mc_server_host,
            server_port=mc_server_port,
            bot_username=bot_username
        )
        
        # Initialize agent
        if vllm_base_url and checkpoint_path:
            print(f"[Server] Initializing VLLM agent from {checkpoint_path}")
            self.agent = VLLMAgentAdapter(
                checkpoint_path=checkpoint_path,
                base_url=vllm_base_url,
                temperature=temperature,
                history_num=history_num,
                instruction_type=instruction_type,
                action_chunk_len=action_chunk_len
            )
            self.agent.set_instruction(instruction)
        else:
            print("[Server] No VLLM config provided, using random agent")
            self.agent = None
        
        self.running = False
        
    def run(self):
        """Main loop with chat-based instruction handling"""
        self.running = True
        
        print(f"[Server] Starting AI agent loop")
        print(f"[Server] Default instruction: {self.instruction}")
        print(f"[Server] Listening for chat commands...")
        print(f"[Server] Type messages in Minecraft chat to control JarvisAI")
        print(f"[Server] Type 'reset' to clear AI state")
        print(f"[Server] Players can join: {self.mc_server_host}:{self.mc_server_port}")
        print("[Server] Press Ctrl+C to stop")
        
        # Reset environment
        obs, info = self.env.reset()
        
        step_count = 0
        current_instruction = self.instruction
        last_chat_check = time.time()
        chat_check_interval = 1.0  # Check chat every second
        
        try:
            while self.running:
                if self.max_steps and step_count >= self.max_steps:
                    print(f"[Server] Reached max steps ({self.max_steps})")
                    break
                
                # Check for chat messages
                if time.time() - last_chat_check >= chat_check_interval:
                    chat_data = self.env.get_chat_instructions()
                    if chat_data:
                        pending = chat_data.get('pending', [])
                        
                        # Handle reset
                        for msg in pending:
                            if msg['message'].lower().strip() == 'reset':
                                print(f"[Server] Reset from {msg['username']}")
                                if self.agent:
                                    self.agent.reset()
                                self.env.clear_chat_instruction()
                                current_instruction = self.instruction
                                print(f"[Server] AI state cleared")
                                break
                        
                        # Get new instruction
                        if not chat_data.get('current') and pending:
                            new_instr = self.env.start_chat_instruction()
                            if new_instr:
                                current_instruction = new_instr['message']
                                print(f"[Server] New task from {new_instr['username']}: {current_instruction}")
                                if self.agent:
                                    self.agent.set_instruction(current_instruction)
                    
                    last_chat_check = time.time()
                
                # Get POV image
                pov_image = self.env.get_pov_image()
                obs['pov'] = pov_image
                
                # Get action from agent
                if self.agent:
                    try:
                        # Log input to agent
                        pov_path = self.log_dir / f"step_{step_count:05d}_input.jpg"
                        if pov_image:
                            pov_image.save(pov_path, 'JPEG')
                        
                        # Get action
                        action = self.agent.get_action(obs, verbos=self.verbos)
                        
                        # Log request/response
                        log_entry = {
                            'step': step_count,
                            'timestamp': datetime.now().isoformat(),
                            'instruction': current_instruction,
                            'health': obs.get('health', 0),
                            'position': obs.get('position'),
                            'pov_saved': str(pov_path),
                            'action': str(action),
                            'action_type': action.get('type') if isinstance(action, dict) else None
                        }
                        
                        with open(self.session_log, 'a') as f:
                            f.write(json.dumps(log_entry) + '\n')
                        
                        if self.verbos:
                            print(f"[Server] Step {step_count}: {action}")
                            print(f"[Log] Saved to {pov_path}")
                    except Exception as e:
                        print(f"[Server] Agent error: {e}")
                        import traceback
                        traceback.print_exc()
                        action = self.env.noop_action()
                else:
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
                
                # Status every 100 steps
                if step_count % 100 == 0:
                    health = obs.get('health', 0)
                    pos = obs.get('position') or {}
                    task_preview = current_instruction[:40] + "..." if len(current_instruction) > 40 else current_instruction
                    print(f"[Server] Step {step_count} | Health: {health} | Pos: ({pos.get('x',0):.1f}, {pos.get('y',0):.1f}, {pos.get('z',0):.1f}) | Task: {task_preview}")
        
        except KeyboardInterrupt:
            print("\n[Server] Shutting down...")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        print("[Server] Closing environment...")
        self.env.close()
        print("[Server] Shutdown complete")
    
    def signal_handler(self, sig, frame):
        """Handle shutdown signals"""
        print("\n[Server] Received shutdown signal")
        self.cleanup()
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description='Minecraft AI Server using Mineflayer + VLLM')
    
    # Minecraft server config
    parser.add_argument('--mc-host', type=str, default='localhost',
                        help='Minecraft server hostname')
    parser.add_argument('--mc-port', type=int, default=25565,
                        help='Minecraft server port')
    parser.add_argument('--bot-username', type=str, default='JarvisAI',
                        help='Bot username in-game')
    
    # VLLM config
    parser.add_argument('--vllm-url', type=str, default=None,
                        help='VLLM server base URL (e.g., http://localhost:8000/v1)')
    parser.add_argument('--checkpoint', type=str, default=None,
                        help='Path to model checkpoint')
    
    # Agent config
    parser.add_argument('--instruction', type=str, default='Explore and survive in Minecraft',
                        help='Task instruction for the agent')
    parser.add_argument('--temperature', type=float, default=0.7,
                        help='Sampling temperature')
    parser.add_argument('--history-num', type=int, default=0,
                        help='Number of history frames')
    parser.add_argument('--instruction-type', type=str, default='normal',
                        choices=['normal', 'recipe', 'simple'],
                        help='Instruction type')
    parser.add_argument('--action-chunk-len', type=int, default=1,
                        help='Number of actions to generate at once')
    
    # Loop config
    parser.add_argument('--max-steps', type=int, default=None,
                        help='Maximum number of steps (None for infinite)')
    parser.add_argument('--fps', type=int, default=20,
                        help='Actions per second')
    parser.add_argument('--verbos', action='store_true',
                        help='Verbose output')
    
    args = parser.parse_args()
    
    # Create and run server
    server = MinecraftAIServer(
        mc_server_host=args.mc_host,
        mc_server_port=args.mc_port,
        bot_username=args.bot_username,
        vllm_base_url=args.vllm_url,
        checkpoint_path=args.checkpoint,
        instruction=args.instruction,
        temperature=args.temperature,
        history_num=args.history_num,
        instruction_type=args.instruction_type,
        action_chunk_len=args.action_chunk_len,
        max_steps=args.max_steps,
        step_delay=1.0/args.fps,
        verbos=args.verbos
    )
    
    # Register signal handlers
    signal.signal(signal.SIGINT, server.signal_handler)
    signal.signal(signal.SIGTERM, server.signal_handler)
    
    # Run
    server.run()


if __name__ == '__main__':
    main()

