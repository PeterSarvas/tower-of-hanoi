from langgraph.graph import StateGraph, END, START
from typing import TypedDict, List
from langchain_anthropic import ChatAnthropic
from langsmith import traceable
import os
import json

# Check for API key at startup
if not os.getenv("ANTHROPIC_API_KEY"):
    raise ValueError("Please set ANTHROPIC_API_KEY environment variable")

# Enable LangSmith tracing
if os.getenv("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "tower-of-hanoi-solver-comparison"
    print("✅ LangSmith tracing enabled")
else:
    print("⚠️ LangSmith tracing disabled - set LANGCHAIN_API_KEY to enable")

# Initialize LLMs with different temperatures
try:
    # Creative LLM for move generation and problem solving
    creative_llm = ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        temperature=0.7,  # Exploratory and creative
        max_tokens=1000
    )
    
    # Deterministic LLM for constraint validation
    validation_llm = ChatAnthropic(
        model="claude-3-5-sonnet-20241022", 
        temperature=0,  # Consistent and reliable
        max_tokens=500
    )
    
    print("✅ Both LLMs initialized successfully")
except Exception as e:
    raise ValueError(f"Failed to initialize LLMs: {str(e)}")

class ExperimentState(TypedDict):
    # Experiment configuration
    complexity_start: int
    complexity_end: int
    current_complexity: int
    
    # Current problem state
    current_state: dict
    goal_state: dict
    solver_type: str  # "single", "hybrid", "multi"
    
    # Solving state
    moves_made: List[str]
    max_moves: int
    solved: bool
    failed: bool
    iteration_count: int
    
    # Validation state
    proposed_move: str
    single_disk_valid: bool
    top_disk_valid: bool
    size_order_valid: bool
    overall_valid: bool
    constraint_violations: List[str]
    
    # Results tracking
    results: List[dict]
    experiment_complete: bool

def setup_experiment_node(state):
    """Initialize the complexity range experiment"""
    start = state.get("complexity_start", 3)
    end = state.get("complexity_end", 3)
    
    return {
        "current_complexity": start,
        "results": [],
        "experiment_complete": False
    }

def setup_problem_node(state):
    """Setup Tower of Hanoi problem for current complexity level"""
    num_disks = state["current_complexity"]
    
    initial_pegs = [list(range(num_disks, 0, -1)), [], []]
    goal_pegs = [[], [], list(range(num_disks, 0, -1))]
    
    return {
        "current_state": {"pegs": initial_pegs},
        "goal_state": {"pegs": goal_pegs},
        "moves_made": [],
        "max_moves": min(2 ** num_disks * 2, 100),  # Cap at 100 iterations
        "solved": False,
        "failed": False,
        "iteration_count": 0
    }

# ================== APPROACH A: SINGLE AGENT (Paper's Approach) ==================

@traceable(name="single_agent.solver")
def single_agent_solver_node(state):
    """
    Single agent handling ALL constraints + move generation
    (Replicating the paper's monolithic approach)
    """
    
    prompt = f"""
    You are solving Tower of Hanoi with {state["current_complexity"]} disks.
    Generate the NEXT BEST MOVE following ALL rules simultaneously:

    CURRENT STATE: {state["current_state"]}
    GOAL: Move all disks to peg 2
    MOVES SO FAR: {len(state.get("moves_made", []))}
    ITERATION: {state.get("iteration_count", 0)}

    RULES YOU MUST FOLLOW SIMULTANEOUSLY:
    1. Only one disk can be moved at a time
    2. Only the top disk from any stack can be moved
    3. A larger disk may never be placed on top of a smaller disk
    4. Move should progress toward the goal

    Return JSON:
    {{
        "next_move": "[disk_id, from_peg, to_peg]",
        "reasoning": "strategy explanation",
        "confidence": "high/medium/low"
    }}
    """
    
    response = creative_llm.invoke(prompt)
    
    try:
        result = json.loads(response.content.strip())
        next_move = result.get("next_move", "[1, 0, 2]")
        confidence = result.get("confidence", "low")
    except Exception:
        next_move = "[1, 0, 2]"
        confidence = "low"
    
    return {
        "proposed_move": next_move,
        "agent_confidence": confidence
    }

# ================== APPROACH B: HYBRID (Single Solver + Single Validator) ==================

@traceable(name="hybrid_agent.solver")
def hybrid_agent_solver_node(state):
    """
    Hybrid approach: Generate move (will loop back if invalid)
    """
    
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

# ================== APPROACH C: MULTI-AGENT (Decomposed Constraints) ==================

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
def multi_disk_count_validator_node(state):
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
def multi_position_validator_node(state):
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
def multi_size_order_validator_node(state):
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

@traceable(name="multi_agent.refiner")
def multi_move_refiner_node(state):
    """Multi-agent: Fix constraint violations"""
    
    violations = []
    if not state.get("single_disk_valid", True):
        violations.append("single_disk")
    if not state.get("top_disk_valid", True):
        violations.append("top_disk")
    if not state.get("size_order_valid", True):
        violations.append("size_order")
    
    prompt = f"""
    Fix these constraint violations: {violations}

    CURRENT MOVE: {state.get("proposed_move", "")}
    CURRENT STATE: {state["current_state"]}
    
    Return JSON: {{"corrected_move": "[disk_id, from_peg, to_peg]"}}
    """
    
    response = creative_llm.invoke(prompt)
    
    try:
        result = json.loads(response.content.strip())
        corrected_move = result.get("corrected_move", state.get("proposed_move", "[1,0,2]"))
    except:
        corrected_move = state.get("proposed_move", "[1,0,2]")
    
    return {"proposed_move": corrected_move}

# ================== SHARED UTILITIES ==================

def apply_move_node(state):
    """Apply validated move and update game state"""
    
    move_str = state.get("proposed_move", "[1,0,2]")
    current_pegs = state["current_state"]["pegs"]
    moves_made = state.get("moves_made", [])
    
    try:
        move = json.loads(move_str)
        disk_id, from_peg, to_peg = move[0], move[1], move[2]
        
        if (from_peg < 3 and to_peg < 3 and 
            len(current_pegs[from_peg]) > 0 and
            current_pegs[from_peg][-1] == disk_id):
            
            new_pegs = [peg[:] for peg in current_pegs]
            disk = new_pegs[from_peg].pop()
            new_pegs[to_peg].append(disk)
            
            new_state = {"pegs": new_pegs}
            new_moves = moves_made + [move_str]
        else:
            new_state = state["current_state"]
            new_moves = moves_made
            
    except Exception:
        new_state = state["current_state"]
        new_moves = moves_made
    
    return {
        "current_state": new_state,
        "moves_made": new_moves,
        "iteration_count": state.get("iteration_count", 0) + 1
    }

def goal_checker_node(state):
    """Check if current problem is solved or failed"""
    
    current_pegs = state["current_state"]["pegs"]
    goal_pegs = state["goal_state"]["pegs"]
    max_moves = state.get("max_moves", 50)
    iteration_count = state.get("iteration_count", 0)
    
    solved = current_pegs[2] == goal_pegs[2]
    failed = iteration_count >= max_moves and not solved
    
    return {
        "solved": solved,
        "failed": failed
    }

def record_result_node(state):
    """Record result for current complexity level"""
    
    result = {
        "complexity": state["current_complexity"],
        "solver_type": state["solver_type"],
        "solved": state.get("solved", False),
        "failed": state.get("failed", False),
        "moves_count": len(state.get("moves_made", [])),
        "iterations": state.get("iteration_count", 0),
        "moves_sequence": state.get("moves_made", [])
    }
    
    current_results = state.get("results", [])
    updated_results = current_results + [result]
    
    return {"results": updated_results}

def next_complexity_node(state):
    """Move to next complexity level or complete experiment"""
    
    current = state["current_complexity"]
    end = state["complexity_end"]
    
    if current < end:
        return {
            "current_complexity": current + 1,
            "experiment_complete": False
        }
    else:
        return {"experiment_complete": True}

def generate_report_node(state):
    """Generate final comparison report"""
    
    results = state.get("results", [])
    
    single_results = [r for r in results if r["solver_type"] == "single"]
    hybrid_results = [r for r in results if r["solver_type"] == "hybrid"]
    multi_results = [r for r in results if r["solver_type"] == "multi"]
    
    report = {
        "experiment_summary": {
            "complexity_range": f"{state['complexity_start']}-{state['complexity_end']}",
            "total_tests": len(results)
        },
        "single_agent_performance": {
            "solved_count": sum(1 for r in single_results if r["solved"]),
            "success_rate": sum(1 for r in single_results if r["solved"]) / len(single_results) if single_results else 0,
            "avg_moves": sum(r["moves_count"] for r in single_results if r["solved"]) / sum(1 for r in single_results if r["solved"]) if any(r["solved"] for r in single_results) else 0
        },
        "hybrid_performance": {
            "solved_count": sum(1 for r in hybrid_results if r["solved"]),
            "success_rate": sum(1 for r in hybrid_results if r["solved"]) / len(hybrid_results) if hybrid_results else 0,
            "avg_moves": sum(r["moves_count"] for r in hybrid_results if r["solved"]) / sum(1 for r in hybrid_results if r["solved"]) if any(r["solved"] for r in hybrid_results) else 0
        },
        "multi_agent_performance": {
            "solved_count": sum(1 for r in multi_results if r["solved"]),
            "success_rate": sum(1 for r in multi_results if r["solved"]) / len(multi_results) if multi_results else 0,
            "avg_moves": sum(r["moves_count"] for r in multi_results if r["solved"]) / sum(1 for r in multi_results if r["solved"]) if any(r["solved"] for r in multi_results) else 0
        },
        "detailed_results": results
    }
    
    return {"final_report": report}

# ================== ROUTING FUNCTIONS ==================

def solver_routing(state):
    """Route to appropriate solver approach"""
    return state.get("solver_type", "single")

def single_agent_goal_routing(state):
    if state.get("solved", False):
        return "solved"
    elif state.get("failed", False):
        return "failed"
    else:
        return "continue"

def hybrid_validation_routing(state):
    """Route based on hybrid validation result"""
    if state.get("overall_valid", False):
        return "apply_move"
    else:
        return "regenerate_move"  # Loop back to solver

def hybrid_goal_routing(state):
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
    
    return "apply_move" if all_valid else "refine_move"

def multi_agent_goal_routing(state):
    if state.get("solved", False):
        return "solved"
    elif state.get("failed", False):
        return "failed"
    else:
        return "continue"

def experiment_routing(state):
    return "complete" if state.get("experiment_complete", False) else "continue"

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
    workflow.add_node("single_apply_move", apply_move_node)
    workflow.add_node("single_goal_check", goal_checker_node)
    
    # APPROACH B: Hybrid (Single Solver + Single Validator)
    workflow.add_node("hybrid_agent_solver", hybrid_agent_solver_node)
    workflow.add_node("hybrid_agent_validator", hybrid_agent_validator_node)
    workflow.add_node("hybrid_apply_move", apply_move_node)
    workflow.add_node("hybrid_goal_check", goal_checker_node)
    
    # APPROACH C: Multi-Agent
    workflow.add_node("multi_agent_solver", multi_agent_solver_node)
    workflow.add_node("multi_disk_count_validator", multi_disk_count_validator_node)
    workflow.add_node("multi_position_validator", multi_position_validator_node)
    workflow.add_node("multi_size_order_validator", multi_size_order_validator_node)
    workflow.add_node("multi_move_refiner", multi_move_refiner_node)
    workflow.add_node("multi_apply_move", apply_move_node)
    workflow.add_node("multi_goal_check", goal_checker_node)
    
    # Result processing
    workflow.add_node("record_result", record_result_node)
    workflow.add_node("next_complexity", next_complexity_node)
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
    
    # APPROACH A: Single agent solving loop
    workflow.add_edge("single_agent_solver", "single_apply_move")
    workflow.add_edge("single_apply_move", "single_goal_check")
    workflow.add_conditional_edges(
        "single_goal_check",
        single_agent_goal_routing,
        {
            "continue": "single_agent_solver",
            "solved": "record_result",
            "failed": "record_result"
        }
    )
    
    # APPROACH B: Hybrid solving loop
    workflow.add_edge("hybrid_agent_solver", "hybrid_agent_validator")
    workflow.add_conditional_edges(
        "hybrid_agent_validator",
        hybrid_validation_routing,
        {
            "apply_move": "hybrid_apply_move",
            "regenerate_move": "hybrid_agent_solver"  # Loop back to solver!
        }
    )
    workflow.add_edge("hybrid_apply_move", "hybrid_goal_check")
    workflow.add_conditional_edges(
        "hybrid_goal_check",
        hybrid_goal_routing,
        {
            "continue": "hybrid_agent_solver",
            "solved": "record_result",
            "failed": "record_result"
        }
    )
    
    # APPROACH C: Multi-agent solving loop
    workflow.add_edge("multi_agent_solver", "multi_disk_count_validator")
    workflow.add_edge("multi_disk_count_validator", "multi_position_validator")
    workflow.add_edge("multi_position_validator", "multi_size_order_validator")
    
    workflow.add_conditional_edges(
        "multi_size_order_validator",
        multi_agent_constraint_routing,
        {
            "apply_move": "multi_apply_move",
            "refine_move": "multi_move_refiner"
        }
    )
    
    workflow.add_edge("multi_move_refiner", "multi_disk_count_validator")
    workflow.add_edge("multi_apply_move", "multi_goal_check")
    
    workflow.add_conditional_edges(
        "multi_goal_check",
        multi_agent_goal_routing,
        {
            "continue": "multi_agent_solver",
            "solved": "record_result",
            "failed": "record_result"
        }
    )
    
    # Experiment progression
    workflow.add_edge("record_result", "next_complexity")
    
    workflow.add_conditional_edges(
        "next_complexity",
        experiment_routing,
        {
            "continue": "setup_problem",
            "complete": "generate_report"
        }
    )
    
    workflow.add_edge("generate_report", END)
    
    return workflow.compile()