import os
from langchain_anthropic import ChatAnthropic

# Check for API key at startup
if not os.getenv("ANTHROPIC_API_KEY"):
    raise ValueError("Please set ANTHROPIC_API_KEY environment variable")

# Enable LangSmith tracing if available
if os.getenv("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "tower-of-hanoi-solver-comparison"

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
    
except Exception as e:
    raise ValueError(f"Failed to initialize LLMs: {str(e)}")