"""
VLLM Agent Adapter for Mineflayer Environment
Wraps JarvisVLA's VLLM_AGENT to work with Mineflayer
"""

import sys
from pathlib import Path

# Add JarvisVLA to path (it's one level up from bridge directory)
sys.path.insert(0, str(Path(__file__).parent.parent / "JarvisVLA"))

from jarvisvla.evaluate import agent_wrapper
from mineflayer_env import ActionMapper


class VLLMAgentAdapter:
    """
    Adapter that wraps JarvisVLA's VLLM_AGENT for use with Mineflayer
    """
    
    def __init__(
        self,
        checkpoint_path: str,
        base_url: str,
        temperature: float = 0.7,
        history_num: int = 0,
        instruction_type: str = 'normal',
        action_chunk_len: int = 1
    ):
        """
        Initialize VLLM agent
        
        Args:
            checkpoint_path: Path to model checkpoint
            base_url: URL of VLLM server
            temperature: Sampling temperature
            history_num: Number of history frames
            instruction_type: Type of instruction ('normal', 'recipe', 'simple')
            action_chunk_len: Number of actions to generate at once
        """
        self.agent = agent_wrapper.VLLM_AGENT(
            checkpoint_path=checkpoint_path,
            base_url=base_url,
            temperature=temperature,
            history_num=history_num,
            instruction_type=instruction_type,
            action_chunk_len=action_chunk_len
        )
        
        self.action_mapper = ActionMapper()
        self.current_instruction = None
        
    def reset(self):
        """Reset agent state"""
        self.agent.reset()
        self.current_instruction = None
    
    def set_instruction(self, instruction: str):
        """Set the current task instruction"""
        self.current_instruction = instruction
    
    def get_action(self, observation: dict, need_crafting_table: bool = False, verbos: bool = False) -> dict:
        """
        Get action from VLLM agent based on current observation
        
        Args:
            observation: Dict with 'pov' (image) and other state info
            need_crafting_table: Whether crafting table is needed
            verbos: Whether to print verbose output
            
        Returns:
            Mineflayer-compatible action dict
        """
        if self.current_instruction is None:
            raise ValueError("Instruction not set. Call set_instruction() first.")
        
        # Extract POV image
        pov_image = observation.get('pov')
        if pov_image is None:
            raise ValueError("Observation missing 'pov' key")
        
        # Get action from VLLM agent
        # agent.forward expects: (observations, instructions, verbos, need_crafting_table)
        jarvis_action = self.agent.forward(
            observations=[pov_image],
            instructions=[self.current_instruction],
            verbos=verbos,
            need_crafting_table=need_crafting_table
        )
        
        # Convert JarvisVLA action to Mineflayer action
        mineflayer_action = self.action_mapper.jarvis_to_mineflayer(jarvis_action)
        
        return mineflayer_action

