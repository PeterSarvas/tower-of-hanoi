def record_result_node(state):
    """Record result for current complexity level and run"""
    
    # Extract solution analysis details
    analysis = state.get("solution_analysis", {})
    failure_details = state.get("failure_details", {})
    
    result = {
        "complexity": state["current_complexity"],
        "run": state.get("current_run", 1),
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

def next_iteration_node(state):
    """Move to next run or next complexity level"""
    
    current_complexity = state["current_complexity"]
    current_run = state.get("current_run", 1)
    runs_per_complexity = state.get("runs_per_complexity", 1)
    complexity_end = state["complexity_end"]
    
    # Check if we need more runs for current complexity
    if current_run < runs_per_complexity:
        return {
            "current_run": current_run + 1,
            "experiment_complete": False
        }
    
    # All runs for current complexity done, move to next complexity
    if current_complexity < complexity_end:
        return {
            "current_complexity": current_complexity + 1,
            "current_run": 1,
            "experiment_complete": False
        }
    
    # All complexities and runs complete
    return {"experiment_complete": True}

def generate_report_node(state):
    """Generate final comparison report with success rates"""
    
    results = state.get("results", [])
    
    # Group results by solver type
    single_results = [r for r in results if r["solver_type"] == "single"]
    hybrid_results = [r for r in results if r["solver_type"] == "hybrid"] 
    multi_results = [r for r in results if r["solver_type"] == "multi"]
    
    def calculate_metrics_with_success_rates(results_list):
        if not results_list:
            return {
                "total_runs": 0,
                "solved_count": 0, 
                "overall_success_rate": 0,
                "avg_moves": 0,
                "avg_iterations": 0,
                "success_by_complexity": {}
            }
        
        total_runs = len(results_list)
        solved_count = sum(1 for r in results_list if r["solved"])
        overall_success_rate = solved_count / total_runs
        
        # Calculate success rates by complexity
        complexity_groups = {}
        for result in results_list:
            complexity = result["complexity"]
            if complexity not in complexity_groups:
                complexity_groups[complexity] = {"total": 0, "solved": 0, "runs": []}
            
            complexity_groups[complexity]["total"] += 1
            complexity_groups[complexity]["runs"].append(result)
            if result["solved"]:
                complexity_groups[complexity]["solved"] += 1
        
        success_by_complexity = {}
        for complexity, data in complexity_groups.items():
            success_rate = data["solved"] / data["total"]
            solved_runs = [r for r in data["runs"] if r["solved"]]
            
            success_by_complexity[complexity] = {
                "total_runs": data["total"],
                "solved_runs": data["solved"],
                "success_rate": success_rate,
                "avg_moves_when_solved": sum(r["moves_count"] for r in solved_runs) / len(solved_runs) if solved_runs else 0,
                "avg_iterations_when_solved": sum(r["iterations"] for r in solved_runs) / len(solved_runs) if solved_runs else 0
            }
        
        # Overall averages for solved cases
        solved_results = [r for r in results_list if r["solved"]]
        avg_moves = sum(r["moves_count"] for r in solved_results) / len(solved_results) if solved_results else 0
        avg_iterations = sum(r["iterations"] for r in results_list) / len(results_list)
        
        return {
            "total_runs": total_runs,
            "solved_count": solved_count,
            "overall_success_rate": overall_success_rate,
            "avg_moves": avg_moves,
            "avg_iterations": avg_iterations,
            "success_by_complexity": success_by_complexity
        }
    
    report = {
        "experiment_summary": {
            "complexity_range": f"{state['complexity_start']}-{state['complexity_end']}",
            "runs_per_complexity": state.get("runs_per_complexity", 1),
            "total_tests": len(results),
            "single_agent_tests": len(single_results),
            "hybrid_agent_tests": len(hybrid_results),
            "multi_agent_tests": len(multi_results)
        },
        "single_agent_performance": calculate_metrics_with_success_rates(single_results),
        "hybrid_agent_performance": calculate_metrics_with_success_rates(hybrid_results),
        "multi_agent_performance": calculate_metrics_with_success_rates(multi_results),
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
                "run": result["run"],
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

# Keep old function name for backward compatibility
next_complexity_node = next_iteration_node