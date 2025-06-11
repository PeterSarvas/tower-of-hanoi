def solver_routing(state):
    """Route to appropriate solver approach"""
    return state.get("solver_type", "single")

def hybrid_agent_validation_routing(state):
    """Route from validator always to apply_move (apply_move handles validation results)"""
    return "apply_move"

def multi_agent_constraint_routing(state):
    """Route from resolver always to apply_move (apply_move handles validation results)"""
    return "apply_move"

def apply_move_routing(state):
    """Route based on apply_move decision"""
    route_to = state.get("route_to", "continue_solving")
    
    if route_to == "goal_checker":
        return "goal_checker"
    elif route_to == "regenerate_solver":
        return "regenerate_solver"
    else:  # continue_solving
        return "continue_solving"

def continue_solving_routing(state):
    """Route back to appropriate solver for next iteration"""
    solver_type = state.get("solver_type", "single")
    if solver_type == "hybrid":
        return "hybrid_agent_solver"
    else:  # multi
        return "multi_agent_solver"

def experiment_routing(state):
    return "complete" if state.get("experiment_complete", False) else "continue"