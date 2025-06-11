import json
import re
from langsmith import traceable
from .config import creative_llm

@traceable(name="single_agent.solver")
def single_agent_solver_node(state):
    """
    Single agent handling ALL constraints + move generation
    (Replicating the paper's exact monolithic approach)
    
    Generates complete solution, then converts to unified structure
    """
    
    num_disks = state["current_complexity"]
    
    # System prompt - exact copy from paper
    system_prompt = """You are a helpful assistant. Solve this puzzle for me.
There are three pegs and n disks of different sizes stacked on the first peg. The disks are numbered from 1 (smallest) to n (largest). Disk moves in this puzzle should follow:
1. Only one disk can be moved at a time.
2. Each move consists of taking the upper disk from one stack and placing it on top of another stack.
3. A larger disk may not be placed on top of a smaller disk.
The goal is to move the entire stack to the third peg.
Example: With 3 disks numbered 1 (smallest), 2, and 3 (largest), the initial state is [[3, 2, 1], [], []], and a solution might be:
moves = [[1, 0, 2], [2, 0, 1], [1, 2, 1], [3, 0, 2], [1, 1, 0], [2, 1, 2], [1, 0, 2]]
This means: Move disk 1 from peg 0 to peg 2, then move disk 2 from peg 0 to peg 1, and so on.
Requirements:
• When exploring potential solutions in your thinking process, always include the corresponding complete list of moves.
• The positions are 0-indexed (the leftmost peg is 0).
• Ensure your final answer includes the complete list of moves in the format:
moves = [[disk_id, from_peg, to_peg], ...]"""

    # User prompt - exact copy from paper with substituted variables
    user_prompt = f"""I have a puzzle with {num_disks} disks of different sizes with
Initial configuration:
• Peg 0: {num_disks} (bottom), ... 2, 1 (top)
• Peg 1: (empty)
• Peg 2: (empty)

Goal configuration:
• Peg 0: (empty)
• Peg 1: (empty)
• Peg 2: {num_disks} (bottom), ... 2, 1 (top)

Rules:
• Only one disk can be moved at a time.
• Only the top disk from any stack can be moved.
• A larger disk may not be placed on top of a smaller disk.

Find the sequence of moves to transform the initial configuration into the goal configuration."""

    # Combine system and user prompts
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    
    response = creative_llm.invoke(full_prompt)
    
    try:
        # Extract complete move sequence from paper-style response
        response_text = response.content.strip()
        
        # Look for moves = [...] pattern in response
        moves_pattern = r'moves\s*=\s*(\[.*?\])'
        match = re.search(moves_pattern, response_text, re.DOTALL)
        
        if match:
            moves_str = match.group(1)
            moves_list = json.loads(moves_str)
            # Convert to unified string format (same as hybrid/multi)
            # PRESERVE THE COMPLETE SEQUENCE - even if it has mistakes
            moves_made = [str(move) for move in moves_list]
        else:
            # Fallback if pattern not found
            moves_made = ["[1, 0, 2]"]  # Minimal fallback
            
    except Exception:
        # Fallback for any parsing errors
        moves_made = ["[1, 0, 2]"]  # Minimal fallback
    
    # DON'T run simulator here - just preserve what agent produced
    # The goal_checker will do the validation and show where mistakes occur
    
    # For current_state, we'll use the initial state since we're not validating here
    # The goal_checker will determine the actual final state after validation
    initial_state = state["current_state"]
    
    return {
        "moves_made": moves_made,                    # ✅ Complete agent output (mistakes included)
        "current_state": initial_state,             # ✅ Keep initial state (goal_checker will determine final)
        "iteration_count": 1,                       # ✅ Single iteration
        # Keep original data for debugging/analysis
        "paper_style_response": response_text,
        "complete_solution": True
    }