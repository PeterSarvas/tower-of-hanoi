from typing import TypedDict, List

class ExperimentState(TypedDict):
    # Experiment configuration
    complexity_start: int
    complexity_end: int
    runs_per_complexity: int  # NEW: Number of runs per complexity level
    current_complexity: int
    current_run: int          # NEW: Current run number (1, 2, 3, ...)
    
    # Current problem state
    current_state: dict
    goal_state: dict
    solver_type: str  # "single", "hybrid", "multi"
    
    # Solving state (for iterative approaches)
    moves_made: List[str]
    max_moves: int
    solved: bool
    failed: bool
    iteration_count: int
    
    # Validation state (for hybrid/multi step-by-step validation)
    proposed_move: str
    single_disk_valid: bool
    top_disk_valid: bool
    size_order_valid: bool
    overall_valid: bool
    constraint_violations: List[str]
    
    # Results tracking
    results: List[dict]
    experiment_complete: bool
    
    # Detailed analysis from goal checker
    solution_analysis: dict
    failure_details: dict