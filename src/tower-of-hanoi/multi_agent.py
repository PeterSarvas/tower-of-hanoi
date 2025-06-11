import json
from langsmith import traceable
from .config import creative_llm, validation_llm

@traceable(name="multi_agent.solver")
def multi_agent_solver_node(state):
    """
    Multi-agent: Strategic move generation
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
            "validation_breakdown": {},
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
    Apply move node handles ALL logic for multi-agent:
    - If all validators passed: apply move, check completion, route accordingly  
    - If any validator failed: prepare regeneration context and route back to solver
    """
    
    # Check validation results from all three validators
    single_disk_valid = state.get("single_disk_valid", False)
    top_disk_valid = state.get("top_disk_valid", False)
    size_order_valid = state.get("size_order_valid", False)
    all_valid = single_disk_valid and top_disk_valid and size_order_valid
    
    current_pegs = state["current_state"]["pegs"]
    goal_pegs = state["goal_state"]["pegs"]
    moves_made = state.get("moves_made", [])
    iteration_count = state.get("iteration_count", 0)
    max_moves = state.get("max_moves", 50)
    
    if all_valid:
        # All validation passed - apply the move
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
        
        # Identify which validators failed
        failed_validators = []
        if not single_disk_valid:
            failed_validators.append("disk count (only one disk per move)")
        if not top_disk_valid:
            failed_validators.append("disk position (only top disk can be moved)")
        if not size_order_valid:
            failed_validators.append("size ordering (larger disk cannot go on smaller)")
        
        violation_details = ", ".join(failed_validators)
        
        return {
            "current_state": current_pegs,  # No state change
            "moves_made": moves_made,       # No new moves
            "iteration_count": iteration_count + 1,
            "route_to": "regenerate_solver",
            
            # Regeneration context for solver
            "regeneration_needed": True,
            "failed_move": failed_move,
            "validation_breakdown": {
                "disk_count": single_disk_valid,
                "position": top_disk_valid,
                "size_order": size_order_valid
            },
            "regeneration_prompt": f"""
REGENERATION REQUIRED - MULTI-AGENT VALIDATION FAILED:

Your previous move {failed_move} violated these constraints:
{violation_details}

Detailed validation results:
- Disk count validator: {"✅ PASSED" if single_disk_valid else "❌ FAILED"}
- Position validator: {"✅ PASSED" if top_disk_valid else "❌ FAILED"}  
- Size order validator: {"✅ PASSED" if size_order_valid else "❌ FAILED"}

Current state: {state["current_state"]}
Moves so far: {moves_made}

Generate a DIFFERENT valid move that satisfies ALL three constraints.
Pay special attention to the failed constraint(s) above.

Return JSON:
{{
    "proposed_move": "[disk_id, from_peg, to_peg]",
    "strategy": "explanation of how this move satisfies all constraints"
}}
"""
        }