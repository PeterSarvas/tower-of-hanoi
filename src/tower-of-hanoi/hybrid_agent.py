import json
from langsmith import traceable
from .config import creative_llm, validation_llm

@traceable(name="hybrid_agent.solver")
def hybrid_agent_solver_node(state):
    """
    Hybrid approach: Generate strategic next move
    Handles both normal move generation and regeneration after validation failures
    """
    
    # Check if this is a regeneration request
    if state.get("regeneration_needed", False):
        # Use the prepared regeneration prompt
        prompt = state.get("regeneration_prompt", "")
        
        response = creative_llm.invoke(prompt)
        
        try:
            result = json.loads(response.content.strip())
            proposed_move = result.get("proposed_move", "[1, 0, 2]")
        except:
            proposed_move = "[1, 0, 2]"
        
        # Clear regeneration context for next iteration
        return {
            "proposed_move": proposed_move,
            "regeneration_needed": False,
            "failed_move": None,
            "validation_errors": [],
            "regeneration_prompt": ""
        }
    
    else:
        # Normal move generation
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
    Apply move node handles ALL logic:
    - If validation passed: apply move, check completion, route accordingly
    - If validation failed: prepare regeneration context and route back to solver
    """
    
    validation_passed = state.get("overall_valid", False)
    current_pegs = state["current_state"]["pegs"]
    goal_pegs = state["goal_state"]["pegs"]
    moves_made = state.get("moves_made", [])
    iteration_count = state.get("iteration_count", 0)
    max_moves = state.get("max_moves", 50)
    
    if validation_passed:
        # Validation passed - apply the move
        move_str = state.get("proposed_move", "[1,0,2]")
        
        try:
            move = json.loads(move_str)
            disk_id, from_peg, to_peg = move[0], move[1], move[2]
            
            # Apply move to update current state
            if (from_peg < 3 and to_peg < 3 and 
                len(current_pegs[from_peg]) > 0 and
                current_pegs[from_peg][-1] == disk_id):
                
                new_pegs = [peg[:] for peg in current_pegs]
                disk = new_pegs[from_peg].pop()
                new_pegs[to_peg].append(disk)
                
                new_state = {"pegs": new_pegs}
                new_moves = moves_made + [move_str]
            else:
                # Move cannot be applied - keep current state
                new_state = state["current_state"]
                new_moves = moves_made
                
        except Exception:
            # Parsing error - keep current state
            new_state = state["current_state"]
            new_moves = moves_made
        
        # Check if puzzle is completed
        solved = new_state["pegs"][2] == goal_pegs[2]
        failed = iteration_count + 1 >= max_moves and not solved
        
        result = {
            "current_state": new_state,
            "moves_made": new_moves,
            "iteration_count": iteration_count + 1
        }
        
        if solved or failed:
            result["route_to"] = "goal_checker"
        else:
            result["route_to"] = "continue_solving"
            
        return result
        
    else:
        # Validation failed - prepare regeneration context
        failed_move = state.get("proposed_move", "")
        violations = state.get("constraint_violations", [])
        
        return {
            "current_state": current_pegs,  # No state change
            "moves_made": moves_made,       # No new moves
            "iteration_count": iteration_count + 1,
            "route_to": "regenerate_solver",
            
            # Regeneration context for solver
            "regeneration_needed": True,
            "failed_move": failed_move,
            "validation_errors": violations,
            "regeneration_prompt": f"""
REGENERATION REQUIRED:

Your previous move {failed_move} was INVALID.
AI Validator found these violations: {', '.join(violations)}

Current state: {state["current_state"]}
Moves so far: {moves_made}

Generate a DIFFERENT valid move that avoids the previous error.
Focus on the constraint violations and choose a completely different approach.

Return JSON:
{{
    "proposed_move": "[disk_id, from_peg, to_peg]",
    "strategy": "explanation of why this move avoids the previous error"
}}
"""
        }