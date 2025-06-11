import os
import json
from typing import TypedDict

try:
    from langgraph import StateGraph, END
    from langchain_anthropic import ChatAnthropic
except ImportError as e:
    print(f"Import error: {e}")
    raise

# Initialize Claude
llm = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",
    temperature=0,
    max_tokens=1000
)

class ComparisonState(TypedDict):
    experiment_type: str
    move: str
    current_state: dict
    single_result: dict
    multi_result: dict
    budget_result: dict
    position_result: dict
    size_result: dict
    comparison: dict

def single_agent_node(state):
    """
    Single agent trying to handle all Tower of Hanoi constraints simultaneously
    (Replicating the paper's approach that showed failure)
    """
    
    prompt = f"""
    You are validating a Tower of Hanoi move. You must check ALL these rules simultaneously:

    RULES YOU MUST ENFORCE:
    1. Only one disk can be moved at a time
    2. Only the top disk from any stack can be moved  
    3. A larger disk may never be placed on top of a smaller disk

    MOVE TO VALIDATE: {state["move"]}
    CURRENT STATE: {state["current_state"]}

    Example of move format: [disk_id, from_peg, to_peg]
    Example of state format: {{"pegs": [[3,2,1], [], []]}} where inner arrays show disks from bottom to top

    Analyze this move carefully and return ONLY a JSON response:
    {{
        "valid": true/false,
        "violations": ["list of any rule violations"],
        "reasoning": "your step-by-step analysis",
        "confidence": "high/medium/low"
    }}
    """
    
    response = llm.invoke(prompt)
    
    try:
        import json
        # Try to extract JSON from Claude's response
        content = response.content
        if "```json" in content:
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            json_str = content[json_start:json_end].strip()
        else:
            json_str = content.strip()
        
        result = json.loads(json_str)
    except Exception as e:
        result = {
            "valid": False, 
            "violations": ["parsing_error"], 
            "reasoning": f"Failed to parse response: {response.content}",
            "confidence": "low"
        }
    
    return {"single_result": result}

def disk_count_agent_node(state):
    """
    Specialized agent ONLY for constraint 1: Single disk movement validation
    """
    
    prompt = f"""
    You are a Tower of Hanoi specialist focused EXCLUSIVELY on disk count validation.
    
    Your ONLY job: Check if exactly ONE disk is being moved.

    EXAMPLES of what you should validate:
    ✓ VALID: [1, 0, 2] - moves exactly one disk (disk 1)
    ✓ VALID: [3, 1, 0] - moves exactly one disk (disk 3)  
    ✗ INVALID: [[1, 0, 2], [2, 0, 1]] - multiple moves
    ✗ INVALID: [] - no move specified

    MOVE TO CHECK: {state["move"]}

    Focus ONLY on: "Is exactly one disk being moved?"
    Ignore all other rules (position, size constraints, etc.)

    Return ONLY JSON:
    {{
        "single_disk_valid": true/false,
        "reasoning": "brief explanation focusing only on disk count"
    }}
    """
    
    response = llm.invoke(prompt)
    
    try:
        import json
        content = response.content
        if "```json" in content:
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            json_str = content[json_start:json_end].strip()
        else:
            json_str = content.strip()
        
        result = json.loads(json_str)
    except:
        result = {"single_disk_valid": False, "reasoning": f"Parse error: {response.content}"}
    
    return {"budget_result": result}

def position_agent_node(state):
    """
    Specialized agent ONLY for constraint 2: Top disk position validation
    """
    
    prompt = f"""
    You are a Tower of Hanoi specialist focused EXCLUSIVELY on disk position validation.
    
    Your ONLY job: Check if the disk being moved is on top of its source stack.

    EXAMPLES of what you should validate:
    ✓ VALID: State [[3,2,1], [], []], Move [1, 0, 2] - disk 1 is on top of peg 0
    ✓ VALID: State [[3,2], [1], []], Move [2, 0, 1] - disk 2 is on top of peg 0
    ✗ INVALID: State [[3,2,1], [], []], Move [3, 0, 2] - disk 3 is buried under 2,1

    MOVE TO CHECK: {state["move"]}
    CURRENT STATE: {state["current_state"]}

    Focus ONLY on: "Is the moved disk actually on top of its source stack?"
    Ignore all other rules (disk count, size constraints, etc.)

    Return ONLY JSON:
    {{
        "top_disk_valid": true/false,
        "reasoning": "brief explanation focusing only on disk position"
    }}
    """
    
    response = llm.invoke(prompt)
    
    try:
        import json
        content = response.content
        if "```json" in content:
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            json_str = content[json_start:json_end].strip()
        else:
            json_str = content.strip()
        
        result = json.loads(json_str)
    except:
        result = {"top_disk_valid": False, "reasoning": f"Parse error: {response.content}"}
    
    return {"position_result": result}

def size_order_agent_node(state):
    """
    Specialized agent ONLY for constraint 3: Size ordering validation
    """
    
    prompt = f"""
    You are a Tower of Hanoi specialist focused EXCLUSIVELY on size ordering validation.
    
    Your ONLY job: Check if the disk placement violates size ordering (larger on smaller).

    EXAMPLES of what you should validate:
    ✓ VALID: Disk 1 on disk 2 - smaller disk (1) on larger disk (2)
    ✓ VALID: Disk 2 on empty peg - any disk can go on empty space
    ✓ VALID: Disk 1 on empty peg - any disk can go on empty space
    ✗ INVALID: Disk 3 on disk 1 - larger disk (3) on smaller disk (1)
    ✗ INVALID: Disk 2 on disk 1 - larger disk (2) on smaller disk (1)

    MOVE TO CHECK: {state["move"]}
    CURRENT STATE: {state["current_state"]}

    Focus ONLY on: "Would this placement violate size ordering?"
    Ignore all other rules (disk count, position validity, etc.)

    Return ONLY JSON:
    {{
        "size_order_valid": true/false,
        "reasoning": "brief explanation focusing only on size constraints"
    }}
    """
    
    response = llm.invoke(prompt)
    
    try:
        import json
        content = response.content
        if "```json" in content:
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            json_str = content[json_start:json_end].strip()
        else:
            json_str = content.strip()
        
        result = json.loads(json_str)
    except:
        result = {"size_order_valid": False, "reasoning": f"Parse error: {response.content}"}
    
    return {"size_result": result}

def multi_agent_combiner(state):
    """
    Combine results from all three specialized constraint agents
    """
    
    # Extract results from each specialist
    disk_count_valid = state.get("budget_result", {}).get("single_disk_valid", False)
    position_valid = state.get("position_result", {}).get("top_disk_valid", False)
    size_valid = state.get("size_result", {}).get("size_order_valid", False)
    
    # Determine violations
    violations = []
    if not disk_count_valid:
        violations.append("single_disk_rule")
    if not position_valid:
        violations.append("top_disk_rule")  
    if not size_valid:
        violations.append("size_order_rule")
    
    # Combine into final result
    multi_result = {
        "valid": len(violations) == 0,
        "violations": violations,
        "detailed_analysis": {
            "single_disk_check": {
                "passed": disk_count_valid,
                "details": state.get("budget_result", {}).get("reasoning", "No details")
            },
            "top_disk_check": {
                "passed": position_valid,
                "details": state.get("position_result", {}).get("reasoning", "No details")
            },
            "size_order_check": {
                "passed": size_valid,
                "details": state.get("size_result", {}).get("reasoning", "No details")
            }
        },
        "approach": "decomposed_multi_agent"
    }
    
    return {"multi_result": multi_result}

def compare_results_node(state):
    """
    Compare single-agent vs multi-agent constraint validation results
    """
    
    single_result = state.get("single_result", {})
    multi_result = state.get("multi_result", {})
    
    # Analyze agreement and differences
    single_valid = single_result.get("valid", False)
    multi_valid = multi_result.get("valid", False)
    
    comparison = {
        "experiment_summary": {
            "move_tested": state.get("move", "Unknown"),
            "current_state": state.get("current_state", "Unknown")
        },
        "single_agent_approach": {
            "valid": single_valid,
            "violations_found": single_result.get("violations", []),
            "confidence": single_result.get("confidence", "unknown"),
            "reasoning": single_result.get("reasoning", "No reasoning provided")
        },
        "multi_agent_approach": {
            "valid": multi_valid,
            "violations_found": multi_result.get("violations", []),
            "detailed_breakdown": multi_result.get("detailed_analysis", {}),
            "approach": "specialized_agents"
        },
        "comparison_analysis": {
            "approaches_agree": single_valid == multi_valid,
            "single_agent_violations_count": len(single_result.get("violations", [])),
            "multi_agent_violations_count": len(multi_result.get("violations", [])),
            "detail_advantage": "Multi-agent provides constraint-specific analysis",
            "hypothesis_test": "Testing if decomposed constraints outperform monolithic approach"
        }
    }
    
    return {"comparison": comparison}

def create_comparison_workflow():
    """
    Main workflow function that creates the Tower of Hanoi constraint validation comparison
    This function is referenced in langgraph.json
    """
    
    workflow = StateGraph(ComparisonState)
    
    # Single agent path (replicating paper's monolithic approach)
    workflow.add_node("single_agent_validator", single_agent_node)
    
    # Multi-agent path (your innovative decomposed approach)
    workflow.add_node("disk_count_agent", disk_count_agent_node)
    workflow.add_node("position_agent", position_agent_node) 
    workflow.add_node("size_order_agent", size_order_agent_node)
    workflow.add_node("multi_agent_combiner", multi_agent_combiner)
    
    # Results analysis
    workflow.add_node("compare_results", compare_results_node)
    
    # Define execution flow
    workflow.set_entry_point("single_agent_validator")
    
    # After single agent completes, start all multi-agents in parallel
    workflow.add_edge("single_agent_validator", "disk_count_agent")
    workflow.add_edge("single_agent_validator", "position_agent")
    workflow.add_edge("single_agent_validator", "size_order_agent")
    
    # Combine multi-agent results
    workflow.add_edge(["disk_count_agent", "position_agent", "size_order_agent"], "multi_agent_combiner")
    
    # Final comparison
    workflow.add_edge("multi_agent_combiner", "compare_results")
    workflow.add_edge("compare_results", END)
    
    return workflow.compile()