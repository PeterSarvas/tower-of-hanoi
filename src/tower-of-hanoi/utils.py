def record_result_node(state):
    """Record result for current complexity level"""
    
    # Extract solution analysis details
    analysis = state.get("solution_analysis", {})
    failure_details = state.get("failure_details", {})
    
    result = {
        "complexity": state["current_complexity"],
        "solver_type": state["solver_type"],
        "solved": state.get("solved", False),
        "failed": state.get("failed", False),
        
        # Unified solution metrics (same structure for all approaches)
        "moves_count": len(state.get("moves_made", [])),
        "iterations": state.get("iteration_count", 0),
        "moves_sequence": state.get("moves_made", []),
        
        # AI validation results (for hybrid/multi approaches)
        "ai_validation_passed": state.get("overall_valid", None),
        "ai_constraint_violations": state.get("constraint_violations", []),
        
        # Detailed analysis from unified goal checker
        "solution_analysis": analysis,
        "failure_details": failure_details
    }
    
    # Add multi-agent specific validation breakdown
    if state["solver_type"] == "multi":
        result["multi_agent_breakdown"] = state.get("validation_summary", {})
    
    # Add single agent specific metadata (for research analysis)
    if state["solver_type"] == "single":
        result["complete_solution"] = state.get("complete_solution", False)
        result["paper_style_response"] = state.get("paper_style_response", "")
    
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
    
    def calculate_metrics(results_list):
        if not results_list:
            return {"solved_count": 0, "success_rate": 0, "avg_moves": 0, "avg_iterations": 0}
        
        solved_count = sum(1 for r in results_list if r["solved"])
        success_rate = solved_count / len(results_list)
        
        # Average moves for solved cases
        solved_results = [r for r in results_list if r["solved"]]
        avg_moves = sum(r["moves_count"] for r in solved_results) / len(solved_results) if solved_results else 0
        
        # Average iterations
        avg_iterations = sum(r["iterations"] for r in results_list) / len(results_list)
        
        return {
            "solved_count": solved_count,
            "success_rate": success_rate,
            "avg_moves": avg_moves,
            "avg_iterations": avg_iterations
        }
    
    report = {
        "experiment_summary": {
            "complexity_range": f"{state['complexity_start']}-{state['complexity_end']}",
            "total_tests": len(results)
        },
        "single_agent_performance": calculate_metrics(single_results),
        "hybrid_performance": calculate_metrics(hybrid_results),
        "multi_agent_performance": calculate_metrics(multi_results),
        "detailed_results": results,
        
        # AI validation analysis
        "ai_validation_analysis": {
            "hybrid_accuracy": None,
            "multi_accuracy": None,
            "detailed_comparisons": []
        }
    }
    
    # Calculate AI validation accuracy for hybrid approach
    hybrid_ai_results = [r for r in hybrid_results if r.get("ai_validation_passed") is not None]
    if hybrid_ai_results:
        correct_validations = sum(1 for r in hybrid_ai_results 
                                if r["ai_validation_passed"] == r["solved"])
        report["ai_validation_analysis"]["hybrid_accuracy"] = correct_validations / len(hybrid_ai_results)
    
    # Calculate AI validation accuracy for multi-agent approach
    multi_ai_results = [r for r in multi_results if r.get("ai_validation_passed") is not None]
    if multi_ai_results:
        correct_validations = sum(1 for r in multi_ai_results 
                                if r["ai_validation_passed"] == r["solved"])
        report["ai_validation_analysis"]["multi_accuracy"] = correct_validations / len(multi_ai_results)
    
    # Detailed AI vs deterministic comparisons
    for result in hybrid_results + multi_results:
        if result.get("ai_validation_passed") is not None:
            comparison = {
                "complexity": result["complexity"],
                "solver_type": result["solver_type"],
                "ai_said_valid": result["ai_validation_passed"],
                "actually_solved": result["solved"],
                "match": result["ai_validation_passed"] == result["solved"],
                "ai_violations": result.get("ai_constraint_violations", [])
            }
            
            if result["solver_type"] == "multi":
                comparison["validator_breakdown"] = result.get("multi_agent_breakdown", {})
                
            report["ai_validation_analysis"]["detailed_comparisons"].append(comparison)
    
    return {"final_report": report}