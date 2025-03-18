"""
Basic example of using the CRM Benchmark library.

This example shows how to create a simple agent and run it against the benchmark.
"""

import sys
import os
import pandas as pd

# Add parent directory to path to import crm_benchmark_lib
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the library
from crm_benchmark_lib import BenchmarkClient

# Define a sample agent function
def my_agent(question: str, data: pd.DataFrame) -> str:
    """
    A simple agent that provides basic answers based on the question.
    
    This is just a placeholder - you should replace this with your actual agent code.
    
    Args:
        question: The question to answer
        data: The dataframe containing the data
        
    Returns:
        The agent's response
    """
    # This is a very simple example agent
    if "email" in question.lower():
        # Simple email-related answer
        return "Based on the data, the email campaign had a 25% conversion rate."
    
    elif "pipeline" in question.lower():
        # Simple pipeline-related answer
        return "The sales pipeline shows $1.2M in potential revenue with 15 deals in negotiation."
    
    elif "performance" in question.lower():
        # Simple performance-related answer
        return "John Smith is the top-performing sales representative with 35 closed deals."
    
    # Generic fallback response
    return "Based on my analysis of the data, the results show positive trends in sales activities."


def main():
    # Replace with your actual API key from the website
    API_KEY = "YOUR_API_KEY_HERE"
    
    print("CRM Benchmark Example")
    print("=====================")
    
    # Create a client
    client = BenchmarkClient(
        api_key=API_KEY,
        server_url="http://localhost:5000",  # Change this to the actual server URL if needed
        show_progress=True
    )
    
    # Run the benchmark and submit results
    print("\nRunning benchmark with parallel processing...")
    results = client.run_and_submit(
        agent_callable=my_agent,
        agent_name="Example Agent v1.0",
        parallel=True,
        visualize=True
    )
    
    # Print final score
    print(f"\nFinal Score: {results['overall_average']:.2f}%")
    
    # Check submission status
    submission = results.get('submission', {})
    if submission.get('status') == 'success':
        print(f"Score successfully submitted to the leaderboard for username: {submission.get('username')}")
    else:
        print(f"Failed to submit score: {submission.get('message')}")


if __name__ == "__main__":
    main() 