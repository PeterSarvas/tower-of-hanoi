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

def hybrid_agent_goal_routing(state):
    if state.get("solved", False):
        return "solved"
    elif state.get("failed", False):
        return "failed"
    else:
        return "continue"

def multi_agent_constraint_routing(state):
    """Route based on multi-agent constraint validation"""
    all_valid = (state.get("single_disk_valid", False) and 
                state.get("top_disk_valid", False) and 
                state.get("size_order_valid", False))
    
    return "apply_move" if all_valid else "regenerate_solver"

def multi_agent_goal_routing(state):
    if state.get("solved", False):
        return "solved"
    elif state.get("failed", False):
        return "failed"
    else:
        return "continue"

def experiment_routing(state):
    return "complete" if state.get("experiment_complete", False) else "continue"