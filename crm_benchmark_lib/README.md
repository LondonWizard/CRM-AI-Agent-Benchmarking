# CRM Benchmark Library

A Python library for benchmarking CRM AI agents using standardized datasets and questions.

## Installation

Install the library using pip:

```bash
pip install crm-benchmark-lib
```

## Basic Usage

```python
from crm_benchmark_lib import BenchmarkClient

# Create a client with your API key
client = BenchmarkClient(
    api_key="your-api-key-here",
    server_url="https://your-domain.com"
)

# Define your agent function
def my_agent(question, data):
    """
    Your CRM agent implementation.
    
    Args:
        question (str): The question to answer
        data (pandas.DataFrame): The dataset to use
        
    Returns:
        str: The agent's answer
    """
    # Your agent implementation here
    return "Agent's answer"

# Run benchmarks and submit results
results = client.run_and_submit(
    agent_callable=my_agent,
    agent_name="My CRM Agent v1.0"
)

# Print results
print(f"Final Score: {results.get('overall_average', 0):.2f}%")
```

## Advanced Usage

### Running Benchmarks Without Submitting

```python
# Just run the benchmark without submitting to the leaderboard
results = client.run_full_benchmark(
    agent_callable=my_agent,
    parallel=True  # Use parallel processing for faster results
)

# Visualize the results
client.visualize_results(results)

# Print detailed results
print(f"Overall Score: {results['overall_average']:.2f}%")
for dataset_name, score in results['dataset_scores'].items():
    print(f"- {dataset_name}: {score:.2f}%")
```

### Asynchronous Benchmarking

```python
import asyncio
from crm_benchmark_lib import AsyncBenchmarkClient

async def run_async_benchmark():
    # Create an asynchronous client
    client = AsyncBenchmarkClient(
        api_key="your-api-key-here",
        server_url="https://your-domain.com"
    )
    
    # Run benchmark and submit
    results = await client.run_and_submit(
        agent_callable=my_agent,
        agent_name="My CRM Agent v1.0"
    )
    
    return results

# Run the async benchmark
results = asyncio.run(run_async_benchmark())
```

### Direct API Access

For advanced users who want to integrate directly with the API:

```python
import requests
import json

# Submit a score directly
response = requests.post(
    "https://your-domain.com/submit_agent_score_api",
    headers={"Content-Type": "application/json"},
    json={
        "api_key": "your-api-key-here",
        "agent_name": "My CRM Agent v1.0",
        "score": 87.5,
        "dataset_scores": {
            "dataset_1": 90.2,
            "dataset_2": 85.7,
            "dataset_3": 88.1,
            "dataset_4": 91.3,
            "dataset_5": 82.4
        }
    }
)

# Check response
if response.status_code == 200:
    print("Score submitted successfully!")
    print(response.json())
else:
    print(f"Error: {response.status_code}")
    print(response.text)
```

## Getting an API Key

To use this library, you'll need an API key:

1. Register at [https://your-domain.com/register](https://your-domain.com/register)
2. Verify your email address
3. Log in to view your API key on your profile page

## Advanced Configuration

The `BenchmarkClient` class accepts several configuration options:

```python
client = BenchmarkClient(
    api_key="your-api-key-here",
    server_url="https://your-domain.com",
    max_retries=3,                # Number of retries for failed requests
    backoff_factor=0.5,           # Backoff factor between retries
    max_workers=4,                # Number of parallel workers
    show_progress=True,           # Show progress bars
    log_level=logging.INFO        # Logging level
)
```

## Support

If you encounter any issues or have questions, please contact support@your-domain.com or file an issue on our GitHub repository. 