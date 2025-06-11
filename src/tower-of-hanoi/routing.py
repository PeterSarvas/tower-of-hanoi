def solver_routing(state):
    """Route to appropriate solver approach"""
    return state.get("solver_type", "single")

def single_agent_goal_routing(state):
    """Single agent always proceeds to record result after one attempt (paper methodology)"""
    return "solved"  # Always record result after single attempt, regardless of success

def hybrid_agent_validation_routing(state):
    """Route based on hybrid validation result"""
    if state.get("overall_valid", False):
        return "apply_move"
    else:
        return "regenerate_move"  # Loop back to solver

def multi_agent_constraint_routing(state):
    """Route based on multi-agent constraint validation"""
    all_valid = (state.get("single_disk_valid", False) and 
                state.get("top_disk_valid", False) and 
                state.get("size_order_valid", False))
    
    return "apply_move" if all_valid else "regenerate_solver"

def apply_move_goal_routing(state):
    """Route from apply_move based on goal achievement"""
    current_pegs = state["current_state"]["pegs"]
    goal_pegs = state["goal_state"]["pegs"]
    max_moves = state.get("max_moves", 50)
    iteration_count = state.get("iteration_count", 0)
    
    # Check if goal is reached
    solved = current_pegs[2] == goal_pegs[2]
    
    # Check if failed (timeout)
    failed = iteration_count >= max_moves and not solved
    
    if solved or failed:
        return "goal_checker"  # Final validation
    else:
        return "continue_solving"  # Keep going

def continue_solving_routing(state):
    """Route back to appropriate solver for next iteration"""
    solver_type = state.get("solver_type", "single")
    if solver_type == "hybrid":
        return "hybrid_agent_solver"
    else:  # multi
        return "multi_agent_solver"

def experiment_routing(state):
    return "complete" if state.get("experiment_complete", False) else "continue"