"""
Development utility for local testing
This file is not used in LangGraph Platform deployment
"""

from agents import get_workflow

def test_locally():
    """Test the workflow locally during development"""
    workflow = get_workflow()
    
    # Test single agent
    test_input = {
        "complexity_start": 3,
        "complexity_end": 3,
        "solver_type": "single"
    }
    
    try:
        result = workflow.invoke(test_input)
        print("✅ Local test successful")
        print(f"Results: {len(result.get('results', []))} test cases")
        return result
    except Exception as e:
        print(f"❌ Local test failed: {str(e)}")
        return None

if __name__ == "__main__":
    test_locally()