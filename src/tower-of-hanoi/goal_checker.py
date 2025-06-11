from .simulator import TowerOfHanoiSimulator

def goal_checker_node(state):
    """
    Unified deterministic goal checker for ALL approaches.
    Uses the Tower of Hanoi simulator for mechanical validation.
    
    All approaches now provide the same structure:
    - moves_made: complete sequence of moves
    - current_state: final state after moves
    - iteration_count: number of iterations used
    """
    
    num_disks = state["current_complexity"]
    
    # Initialize simulator
    simulator = TowerOfHanoiSimulator(num_disks)
    
    # All approaches now use the same structure
    moves_sequence = state.get("moves_made", [])
    
    # Always use the same deterministic validation for all approaches
    if moves_sequence:
        analysis = simulator.validate_complete_solution(moves_sequence)
    else:
        # No moves to validate
        analysis = {
            "total_moves": 0,
            "valid_moves": 0,
            "invalid_moves": 0,
            "first_invalid_move": None,
            "final_state": simulator.pegs,  # Initial state
            "goal_achieved": False,
            "move_details": [],
            "error_summary": ["No moves provided"]
        }
    
    # Determine success/failure using the same criteria for all approaches
    solved = analysis["goal_achieved"]
    failed = not solved
    
    # For iterative approaches, also check iteration limits
    solver_type = state["solver_type"]
    if solver_type in ["hybrid", "multi"]:
        max_moves = state.get("max_moves", 50)
        iteration_count = state.get("iteration_count", 0)
        if iteration_count >= max_moves and not solved:
            failed = True
    
    # Create detailed failure analysis (same format for all approaches)
    failure_details = {}
    if failed:
        failure_details = {
            "first_invalid_move_index": analysis.get("first_invalid_move"),
            "total_valid_moves": analysis["valid_moves"],
            "total_invalid_moves": analysis["invalid_moves"],
            "error_summary": analysis["error_summary"],
            "final_state_reached": analysis["final_state"],
            "goal_state_expected": simulator.get_goal_state(),
            "moves_attempted": len(moves_sequence)
        }
        
        # Add iteration info for iterative approaches
        if solver_type in ["hybrid", "multi"]:
            failure_details["iterations_used"] = state.get("iteration_count", 0)
            failure_details["max_iterations"] = state.get("max_moves", 50)
            failure_details["timeout"] = state.get("iteration_count", 0) >= state.get("max_moves", 50)
        
        # Add specific error details for the first failure
        if analysis["first_invalid_move"] is not None:
            move_details = analysis["move_details"]
            if analysis["first_invalid_move"] < len(move_details):
                first_error = move_details[analysis["first_invalid_move"]]
                failure_details["first_error_details"] = first_error
    
    return {
        "solved": solved,
        "failed": failed,
        "solution_analysis": analysis,
        "failure_details": failure_details
    }