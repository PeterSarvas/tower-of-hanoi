# takst
from langgraph.graph import StateGraph, END, START
from .state import ExperimentState
from .setup_nodes import setup_experiment_node, setup_problem_node
from .single_agent import single_agent_solver_node
from .hybrid_agent import (
    hybrid_agent_solver_node, 
    hybrid_agent_validator_node, 
    hybrid_agent_apply_move_node
)
from .multi_agent import (
    multi_agent_solver_node,
    multi_agent_disk_count_validator_node,
    multi_agent_position_validator_node,
    multi_agent_size_order_validator_node,
    multi_agent_validation_resolver_node,
    multi_agent_apply_move_node
)
from .goal_checker import goal_checker_node
from .utils import record_result_node, next_iteration_node, generate_report_node
from .routing import (
    solver_routing,
    hybrid_agent_validation_routing,
    multi_agent_constraint_routing,
    apply_move_routing,
    continue_solving_routing,
    experiment_routing
)
 
def create_comparison_workflow():
    """
    Main workflow: Three-way comparison of solver approaches
    """
    
    workflow = StateGraph(ExperimentState)
    
    # Experiment setup
    workflow.add_node("setup_experiment", setup_experiment_node)
    workflow.add_node("setup_problem", setup_problem_node)
    
    # APPROACH A: Single Agent
    workflow.add_node("single_agent_solver", single_agent_solver_node)
    
    # APPROACH B: Hybrid (Single Solver + Single Validator)
    workflow.add_node("hybrid_agent_solver", hybrid_agent_solver_node)
    workflow.add_node("hybrid_agent_validator", hybrid_agent_validator_node)
    workflow.add_node("hybrid_agent_apply_move", hybrid_agent_apply_move_node)
    
    # APPROACH C: Multi-Agent
    workflow.add_node("multi_agent_solver", multi_agent_solver_node)
    workflow.add_node("multi_agent_disk_count_validator", multi_agent_disk_count_validator_node)
    workflow.add_node("multi_agent_position_validator", multi_agent_position_validator_node)
    workflow.add_node("multi_agent_size_order_validator", multi_agent_size_order_validator_node)
    workflow.add_node("multi_agent_validation_resolver", multi_agent_validation_resolver_node)
    workflow.add_node("multi_agent_apply_move", multi_agent_apply_move_node)
    
    # Unified goal checker for all approaches
    workflow.add_node("goal_checker", goal_checker_node)
    
    # Result processing
    workflow.add_node("record_result", record_result_node)
    workflow.add_node("next_iteration", next_iteration_node)
    workflow.add_node("generate_report", generate_report_node)
    
    # Main experiment flow
    workflow.set_entry_point("setup_experiment")
    workflow.add_edge("setup_experiment", "setup_problem")
    
    # Route to appropriate solver
    workflow.add_conditional_edges(
        "setup_problem",
        solver_routing,
        {
            "single": "single_agent_solver",
            "hybrid": "hybrid_agent_solver",
            "multi": "multi_agent_solver"
        }
    )
    
    # APPROACH A: Single agent solving (paper methodology - one shot)
    workflow.add_edge("single_agent_solver", "goal_checker")
    
    # APPROACH B: Hybrid solving loop
    workflow.add_edge("hybrid_agent_solver", "hybrid_agent_validator")
    workflow.add_conditional_edges(
        "hybrid_agent_validator",
        hybrid_agent_validation_routing,
        {
            "apply_move": "hybrid_agent_apply_move",
            "regenerate_move": "hybrid_agent_solver"  # Loop back to solver!
        }
    )
    workflow.add_edge("hybrid_agent_apply_move", "goal_checker")
    
    workflow.add_edge("multi_agent_apply_move", "goal_checker")
    # APPROACH C: Multi-agent solving loop with parallel validation
    # Parallel edges from solver to all validators
    workflow.add_edge("multi_agent_solver", "multi_agent_disk_count_validator")
    workflow.add_edge("multi_agent_solver", "multi_agent_position_validator") 
    workflow.add_edge("multi_agent_solver", "multi_agent_size_order_validator")
    
    # All validators feed into resolver
    workflow.add_edge("multi_agent_disk_count_validator", "multi_agent_validation_resolver")
    workflow.add_edge("multi_agent_position_validator", "multi_agent_validation_resolver")
    workflow.add_edge("multi_agent_size_order_validator", "multi_agent_validation_resolver")
    
    # Route from resolver - either apply move or regenerate
    workflow.add_conditional_edges(
        "multi_agent_validation_resolver",
        multi_agent_constraint_routing,
        {
            "apply_move": "multi_agent_apply_move",
            "regenerate_solver": "multi_agent_solver"  # Loop back to solver!
        }
    )
    
    workflow.add_edge("multi_agent_apply_move", "goal_checker")
    
    # Unified goal checker routing for all approaches
    workflow.add_conditional_edges(
        "goal_checker",
        goal_checker_routing,
        {
            "record_result": "record_result",
            "continue_hybrid": "hybrid_agent_solver",
            "continue_multi": "multi_agent_solver"
        }
    )
    
    # Experiment progression - now handles multiple runs per complexity
    workflow.add_edge("record_result", "next_iteration")
    
    workflow.add_conditional_edges(
        "next_iteration",
        experiment_routing,
        {
            "continue": "setup_problem",
            "complete": "generate_report"
        }
    )
    
    workflow.add_edge("generate_report", END)
    
    return workflow.compile()