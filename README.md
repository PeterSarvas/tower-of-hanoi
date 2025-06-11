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
  "solver_type": "single"
}
```

### Expected Response Structure

```json
{
  "results": [
    {
      "complexity": 3,
      "solver_type": "single",
      "solved": true,
      "failed": false,
      "moves_count": 7,
      "iterations": 1,
      "moves_sequence": ["[1,0,2]", "[2,0,1]", "[1,2,1]", "[3,0,2]", "[1,1,0]", "[2,1,2]", "[1,0,2]"],
      "solution_analysis": {
        "total_moves": 7,
        "valid_moves": 7,
        "invalid_moves": 0,
        "goal_achieved": true,
        "first_invalid_move": null
      },
      "ai_validation_passed": null,
      "ai_constraint_violations": []
    }
  ],
  "final_report": {
    "experiment_summary": {
      "complexity_range": "3-5",
      "total_tests": 3
    },
    "single_agent_performance": {
      "solved_count": 2,
      "success_rate": 0.67,
      "avg_moves": 15.5,
      "avg_iterations": 1.0
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