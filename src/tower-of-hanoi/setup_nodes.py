def setup_experiment_node(state):
    """Initialize the complexity range experiment with multiple runs support"""
    start = state.get("complexity_start", 3)
    end = state.get("complexity_end", 3)
    runs_per_complexity = state.get("runs_per_complexity", 1)
    
    return {
        "current_complexity": start,
        "current_run": 1,
        "runs_per_complexity": runs_per_complexity,
        "results": [],
        "experiment_complete": False
    }

def setup_problem_node(state):
    """Setup Tower of Hanoi problem for current complexity level and run"""
    num_disks = state["current_complexity"]
    current_run = state.get("current_run", 1)
    
    initial_pegs = [list(range(num_disks, 0, -1)), [], []]
    goal_pegs = [[], [], list(range(num_disks, 0, -1))]
    
    return {
        "current_state": {"pegs": initial_pegs},
        "goal_state": {"pegs": goal_pegs},
        "moves_made": [],
        "max_moves": min(2 ** num_disks * 2, 100),  # Cap at 100 iterations
        "solved": False,
        "failed": False,
        "iteration_count": 0,
        "solution_analysis": {},
        "failure_details": {}
    }