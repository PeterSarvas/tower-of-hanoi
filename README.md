# Tower of Hanoi Multi-Agent Reasoning Experiment

This project implements a systematic comparison of three AI reasoning approaches for solving Tower of Hanoi puzzles, deployed on LangGraph Platform.

## Overview

Based on the research paper "The Illusion of Thinking: Understanding the Strengths and Limitations of Reasoning Models via the Lens of Problem Complexity", this experiment compares:

1. **Single Agent**: Monolithic approach (paper's baseline) - generates complete solution in one step
2. **Hybrid Agent**: AI solver + AI validator - iterative move generation with AI validation
3. **Multi-Agent**: AI solver + specialized constraint validators - iterative with decomposed AI validation

## API Usage

### Basic Experiment Run

```json
{
  "complexity_start": 3,
  "complexity_end": 5,
  "solver_type": "single",
  "runs_per_complexity": 10
}
```

### Expected Response Structure

```json
{
  "results": [
    {
      "complexity": 3,
      "run": 1,
      "solver_type": "single",
      "solved": true,
      "failed": false,
      "moves_count": 7,
      "iterations": 1,
      "moves_sequence": ["[1,0,2]", "[2,0,1]", "[1,2,1]", "[3,0,2]", "[1,1,0]", "[2,1,2]", "[1,0,2]"]
    },
    {
      "complexity": 3,
      "run": 2,
      "solver_type": "single",
      "solved": false,
      "failed": true,
      "moves_count": 4,
      "iterations": 1
    }
  ],
  "final_report": {
    "experiment_summary": {
      "complexity_range": "3-5",
      "runs_per_complexity": 10,
      "total_tests": 30
    },
    "single_agent_performance": {
      "total_runs": 30,
      "solved_count": 18,
      "overall_success_rate": 0.6,
      "success_by_complexity": {
        "3": {
          "total_runs": 10,
          "solved_runs": 9,
          "success_rate": 0.9,
          "avg_moves_when_solved": 7.0
        },
        "4": {
          "total_runs": 10,
          "solved_runs": 7,
          "success_rate": 0.7,
          "avg_moves_when_solved": 15.0
        },
        "5": {
          "total_runs": 10,
          "solved_runs": 2,
          "success_rate": 0.2,
          "avg_moves_when_solved": 31.0
        }
      }
    }
  }
}
```

## Solver Types

### Single Agent (`solver_type: "single"`)
- **Approach**: Replicates paper's monolithic methodology
- **Process**: Generates complete solution sequence in one step
- **Output**: Full `moves_sequence` from AI reasoning
- **Validation**: No AI validation (paper's baseline)
- **Iterations**: Always 1

### Hybrid Agent (`solver_type: "hybrid"`)
- **Approach**: Decomposed solver + unified validator
- **Process**: 
  1. Generate one move at a time
  2. AI validator checks all constraints together
  3. Apply move if valid, retry if invalid
  4. Repeat until solved/failed
- **Output**: Accumulated `moves_sequence` built iteratively
- **Validation**: Single AI checks all rules
- **Iterations**: Variable (depends on convergence)

### Multi-Agent (`solver_type: "multi"`)
- **Approach**: Decomposed solver + specialized validators  
- **Process**:
  1. Generate one move at a time
  2. Three parallel AI validators check specialized constraints:
     - Disk count validator (exactly one disk moved)
     - Position validator (top disk access only)
     - Size order validator (no large on small)
  3. Aggregate validation results
  4. Apply move if all valid, retry if any invalid
  5. Repeat until solved/failed
- **Output**: Accumulated `moves_sequence` built iteratively
- **Validation**: Specialized AI constraint decomposition
- **Iterations**: Variable (depends on convergence)

## Unified Validation

**Key Feature**: All approaches are validated identically using deterministic Tower of Hanoi simulator:

- **Same Input**: All provide `moves_sequence` array
- **Same Validation**: 4-layer mechanical validation (peg boundaries, disk presence, top disk access, size ordering)
- **Same Analysis**: Detailed error reporting showing exactly where and why solutions fail
- **Same Success Criteria**: Goal state achievement via simulator

## Input Parameters

- `complexity_start`: Starting number of disks (default: 3)
- `complexity_end`: Ending number of disks (default: 5)  
- `solver_type`: "single", "hybrid", or "multi"
- `runs_per_complexity`: Number of runs per complexity level (default: 1, recommended: 10-25 for statistical significance)

## Statistical Analysis

### Success Rate by Complexity
The system now tracks success rates across multiple runs, enabling analysis of the stochastic behavior described in the research paper:

```json
{
  "success_by_complexity": {
    "3": {"success_rate": 0.95, "total_runs": 20},
    "4": {"success_rate": 0.85, "total_runs": 20}, 
    "5": {"success_rate": 0.65, "total_runs": 20},
    "6": {"success_rate": 0.40, "total_runs": 20},
    "7": {"success_rate": 0.15, "total_runs": 20},
    "8": {"success_rate": 0.05, "total_runs": 20},
    "9": {"success_rate": 0.0, "total_runs": 20}
  }
}
```

### Recommended Test Configurations

**Quick Test:**
```json
{
  "complexity_start": 3,
  "complexity_end": 6,
  "solver_type": "single",
  "runs_per_complexity": 5
}
```

**Statistical Analysis:**
```json
{
  "complexity_start": 3,
  "complexity_end": 10,
  "solver_type": "single", 
  "runs_per_complexity": 20
}
```

**Full Comparison:**
```json
{
  "complexity_start": 3,
  "complexity_end": 8,
  "solver_type": "multi",
  "runs_per_complexity": 15
}
```

## Output Analysis

### Core Metrics (All Approaches)
- `solved`/`failed`: Boolean success indicators
- `moves_count`: Number of moves in solution
- `iterations`: Number of reasoning iterations
- `moves_sequence`: Complete move sequence `["[1,0,2]", "[2,0,1]", ...]`

### Validation Analysis
- `solution_analysis`: Detailed simulator validation results
- `failure_details`: Specific error locations and descriptions
- `ai_validation_passed`: AI validation decision (hybrid/multi only)
- `ai_constraint_violations`: AI-detected violations (hybrid/multi only)

### Multi-Agent Specific
- `multi_agent_breakdown`: Individual validator results
  ```json
  {
    "disk_count": true,
    "position": false, 
    "size_order": true
  }
  ```

## Research Questions

1. **Constraint Decomposition**: Does breaking validation into specialized AI agents improve accuracy?
2. **AI Validation Accuracy**: How often do AI validators match deterministic validation?
3. **Complexity Thresholds**: At what disk count do different approaches fail?
4. **Failure Patterns**: Where in the solution sequence do different approaches break down?
5. **Iteration Efficiency**: How do reasoning iterations scale with problem complexity?

## Error Analysis

The system provides detailed failure analysis:

```json
{
  "failure_details": {
    "first_invalid_move_index": 3,
    "total_valid_moves": 3,
    "total_invalid_moves": 1,
    "error_summary": ["Move 3: Cannot place larger disk 3 on smaller disk 1"],
    "first_error_details": {
      "move_index": 3,
      "move_string": "[3,1,0]",
      "parsed_move": [3, 1, 0],
      "status": "invalid",
      "message": "Cannot place larger disk 3 on smaller disk 1"
    }
  }
}
```

This enables precise analysis of where each reasoning approach fails and why.