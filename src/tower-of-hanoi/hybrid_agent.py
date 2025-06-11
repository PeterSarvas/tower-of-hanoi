import json
from langsmith import traceable
from .config import creative_llm, validation_llm

@traceable(name="hybrid_agent.solver")
def hybrid_agent_solver_node(state):
    """
    Hybrid approach: Generate strategic next move (will loop back if invalid)
    """
    
    prompt = f"""
    Generate strategic next move for {state["current_complexity"]}-disk Tower of Hanoi:

    CURRENT STATE: {state["current_state"]}
    GOAL: Move all disks to peg 2
    MOVES SO FAR: {state.get("moves_made", [])}
    ITERATION: {state.get("iteration_count", 0)}

    Focus on strategy and game progression. Validation will happen separately.

    Return JSON:
    {{
        "proposed_move": "[disk_id, from_peg, to_peg]",
        "strategy": "reasoning"
    }}
    """
    
    response = creative_llm.invoke(prompt)
    
    try:
        result = json.loads(response.content.strip())
        proposed_move = result.get("proposed_move", "[1, 0, 2]")
    except:
        proposed_move = "[1, 0, 2]"
    
    return {"proposed_move": proposed_move}

@traceable(name="hybrid_agent.validator")
def hybrid_agent_validator_node(state):
    """
    Single validator checking all constraints
    Returns validation result without fixing anything
    """
    
    prompt = f"""
    Validate this Tower of Hanoi move against ALL constraints:

    PROPOSED MOVE: {state.get("proposed_move", "")}
    CURRENT STATE: {state["current_state"]}

    Check ALL these rules:
    1. Only one disk can be moved at a time
    2. Only the top disk from any stack can be moved
    3. A larger disk may never be placed on top of a smaller disk

    Return JSON:
    {{
        "valid": true/false,
        "violations": ["list of violated rules if any"],
        "explanation": "brief explanation of validation result"
    }}
    """
    
    response = validation_llm.invoke(prompt)
    
    try:
        result = json.loads(response.content.strip())
        valid = result.get("valid", False)
        violations = result.get("violations", [])
    except:
        valid = False
        violations = ["parsing_error"]
    
    return {
        "overall_valid": valid,
        "constraint_violations": violations
    }

def hybrid_agent_apply_move_node(state):
    """
    Apply validated move and update game state for hybrid agent
    This node:
    1. Updates the current game state (for iteration tracking)
    2. Accumulates moves in the solution sequence (for final validation)
    """
    
    move_str = state.get("proposed_move", "[1,0,2]")
    current_pegs = state["current_state"]["pegs"]
    moves_made = state.get("moves_made", [])
    
    try:
        move = json.loads(move_str)
        disk_id, from_peg, to_peg = move[0], move[1], move[2]
        
        # Validate move can be applied to current state
        if (from_peg < 3 and to_peg < 3 and 
            len(current_pegs[from_peg]) > 0 and
            current_pegs[from_peg][-1] == disk_id):
            
            # Apply move to update current state
            new_pegs = [peg[:] for peg in current_pegs]
            disk = new_pegs[from_peg].pop()
            new_pegs[to_peg].append(disk)
            
            new_state = {"pegs": new_pegs}
            # Accumulate move in solution sequence
            new_moves = moves_made + [move_str]
        else:
            # Move cannot be applied - keep current state
            new_state = state["current_state"]
            new_moves = moves_made
            
    except Exception:
        # Parsing error - keep current state
        new_state = state["current_state"]
        new_moves = moves_made
    
    return {
        "current_state": new_state,           # For iteration tracking
        "moves_made": new_moves,              # For final simulator validation
        "iteration_count": state.get("iteration_count", 0) + 1
    }