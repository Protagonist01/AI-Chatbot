# from typing import Dict

# OpenAI Pricing (as of 2025) - Update these as needed
PRICING = {
    "gpt-4": {
        "input": 0.03 / 1000,   # $0.03 per 1K input tokens
        "output": 0.06 / 1000   # $0.06 per 1K output tokens
    },
    "gpt-4-turbo": {
        "input": 0.01 / 1000,
        "output": 0.03 / 1000
    },
    "gpt-3.5-turbo": {
        "input": 0.0005 / 1000,
        "output": 0.0015 / 1000
    },
    "text-embedding-ada-002": {
        "input": 0.0001 / 1000,
        "output": 0.0  # No output tokens for embeddings
    },
    "text-embedding-3-small": {
        "input": 0.00002 / 1000,
        "output": 0.0
    },
    "text-embedding-3-large": {
        "input": 0.00013 / 1000,
        "output": 0.0
    }
}

def calculate_openai_cost(model: str, input_tokens: int, output_tokens: int = 0) -> float:
    """
    Calculate cost of OpenAI API call
    
    Args:
        model: Model name (e.g., 'gpt-4', 'gpt-3.5-turbo')
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
    
    Returns:
        Cost in USD
    """
    if model not in PRICING:
        # Default to GPT-3.5 pricing if unknown model
        model = "gpt-3.5-turbo"
    
    pricing = PRICING[model]
    
    input_cost = input_tokens * pricing["input"]
    output_cost = output_tokens * pricing["output"]
    
    total_cost = input_cost + output_cost
    
    return round(total_cost, 6)  # Round to 6 decimal places

def calculate_pinecone_cost(query_count: int, vector_dimensions: int = 1536) -> float:
    """
    Calculate Pinecone query cost (approximate)
    Pinecone pricing is complex, this is a simplified estimation
    
    Args:
        query_count: Number of queries
        vector_dimensions: Dimension of vectors (default 1536 for OpenAI)
    
    Returns:
        Approximate cost in USD
    """
    # Approximate cost: $0.0001 per query (very rough estimate)
    cost_per_query = 0.0001
    return round(query_count * cost_per_query, 6)

def estimate_tokens(text: str) -> int:
    """
    Rough estimate of token count
    Rule of thumb: 1 token ≈ 4 characters for English text
    
    Args:
        text: Input text
    
    Returns:
        Estimated token count
    """
    return len(text) // 4