"""
Main entry point for Tower of Hanoi Multi-Agent Experiment
LangGraph Platform deployment
"""

from .workflow import create_comparison_workflow

# Export the main workflow for LangGraph Platform
def get_workflow():
    """
    Returns the compiled workflow for LangGraph Platform deployment
    """
    return create_comparison_workflow()

# For direct access to the workflow
workflow = create_comparison_workflow()