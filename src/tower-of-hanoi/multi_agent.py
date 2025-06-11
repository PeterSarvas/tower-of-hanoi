import json
from langsmith import traceable
from .config import creative_llm, validation_llm

@traceable(name="multi_agent.solver")
def multi_agent_solver_node(state):
    """
    Multi-agent: Strategic move generation
    """
    
    prompt = f"""
    Generate strategic next move for {state["current_complexity"]}-disk Tower of Hanoi:

    CURRENT STATE: {state["current_state"]}
    GOAL: Move all disks to peg 2
    MOVES SO FAR: {state.get("moves_made", [])}
    ITERATION: {state.get("iteration_count", 0)}

    Focus ONLY on strategy. Constraint specialists will handle validation.

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

@traceable(name="multi_agent.validator.disk_count")
def multi_agent_disk_count_validator_node(state):
    """Multi-agent: Disk count constraint specialist"""
    
    prompt = f"""
    Check ONLY: Is exactly one disk being moved?

    PROPOSED MOVE: {state.get("proposed_move", "")}

    Return JSON: {{"single_disk_valid": true/false}}
    """
    
    response = validation_llm.invoke(prompt)
    
    try:
        result = json.loads(response.content.strip())
        valid = result.get("single_disk_valid", False)
    except:
        valid = False
    
    return {"single_disk_valid": valid}

@traceable(name="multi_agent.validator.position")
def multi_agent_position_validator_node(state):
    """Multi-agent: Position constraint specialist"""
    
    prompt = f"""
    Check ONLY: Is the moved disk on top of its source stack?

    PROPOSED MOVE: {state.get("proposed_move", "")}
    CURRENT STATE: {state["current_state"]}

    Return JSON: {{"top_disk_valid": true/false}}
    """
    
    response = validation_llm.invoke(prompt)
    
    try:
        result = json.loads(response.content.strip())
        valid = result.get("top_disk_valid", False)
    except:
        valid = False
    
    return {"top_disk_valid": valid}

@traceable(name="multi_agent.validator.size_order")
def multi_agent_size_order_validator_node(state):
    """Multi-agent: Size ordering constraint specialist"""
    
    prompt = f"""
    Check ONLY: Does this move maintain size ordering?

    PROPOSED MOVE: {state.get("proposed_move", "")}
    CURRENT STATE: {state["current_state"]}

    Return JSON: {{"size_order_valid": true/false}}
    """
    
    response = validation_llm.invoke(prompt)
    
    try:
        result = json.loads(response.content.strip())
        valid = result.get("size_order_valid", False)
    except:
        valid = False
    
    return {"size_order_valid": valid}

def multi_agent_validation_resolver_node(state):
    """Resolver that aggregates all parallel validation results"""
    
    single_disk_valid = state.get("single_disk_valid", False)
    top_disk_valid = state.get("top_disk_valid", False) 
    size_order_valid = state.get("size_order_valid", False)
    
    all_valid = single_disk_valid and top_disk_valid and size_order_valid
    
    violations = []
    if not single_disk_valid: violations.append("single_disk")
    if not top_disk_valid: violations.append("top_disk") 
    if not size_order_valid: violations.append("size_order")
    
    return {
        "overall_valid": all_valid,
        "constraint_violations": violations,
        "validation_summary": {
            "disk_count": single_disk_valid,
            "position": top_disk_valid,
            "size_order": size_order_valid
        }
    }

def multi_agent_apply_move_node(state):
    """
    Apply validated move and update game state for multi agent
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