"""
Basic example of using the CRM Benchmark library.

This example shows how to create a simple agent and run it against the benchmark.
"""

import sys
import os
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

# Get the absolute path to the crm_benchmark_lib directory
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LIB_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add the repository root to Python path
sys.path.append(REPO_ROOT)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Import the library
from crm_benchmark_lib import BenchmarkClient

# Define a sample agent function
def my_agent(question: str, data: pd.DataFrame) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an AI Agent that specializes in CRM and Sales. You will be given a question and a dataframe. You will need to answer the question based on the data. Return only the answer, no other text."},
            {"role": "user", "content": f"Question: {question}\n\nData: {data.to_string()}"}
        ]
    )
    return response.choices[0].message.content.strip()



def main():
    # Get API key from environment variable
    API_KEY = os.getenv("API_KEY")
    if not API_KEY:
        print("Warning: API_KEY environment variable not set.")
        print("Please register at http://localhost:5000/register to get an API key")
        print("Then set it in your .env file as API_KEY=your_key_here")
        print("For testing, using a temporary key...")
        # This should match a key in your Flask server's database
        API_KEY = "crm-ed41d521443a456814a9aedf67ef53855925fbbc3f028c05"
    
    print("CRM Benchmark Example")
    print("=====================")
    
    # Create a client
    client = BenchmarkClient(
        api_key=API_KEY,
        server_url="http://localhost:5000",
        show_progress=True
    )
    
    # Run the benchmark and submit results
    print("\nRunning benchmark with parallel processing...")
    try:
        results = client.run_and_submit(
            agent_callable=my_agent,
            agent_name="ChatGPT-o3-mini",
            parallel=True,
            visualize=True
        )
        
        # Handle results
        if isinstance(results, dict):
            if "status" in results and results["status"] == "error":
                print(f"\nError: {results.get('message', 'Unknown error')}")
            else:
                score = results.get('overall_average', 0)
                print(f"\nFinal Score: {score:.2f}%")
                
                # Check submission status
                submission = results.get('submission', {})
                if submission.get('status') == 'success':
                    print(f"Score successfully submitted for: {submission.get('username', 'Unknown')}")
                else:
                    print(f"Failed to submit score: {submission.get('message', 'Unknown error')}")
                    if 'request_payload' in submission:
                        print(f"Submission payload: {submission['request_payload']}")
        else:
            print(f"Unexpected results format: {results}")
            
    except Exception as e:
        print(f"Error running benchmark: {e}")
        raise

if __name__ == "__main__":
    main() 