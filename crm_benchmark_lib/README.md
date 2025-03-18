# CRM Benchmark Library

A powerful library for evaluating AI agents on Customer Relationship Management (CRM) tasks, with features for performance evaluation, parallel processing, and automatic leaderboard submission.

## Features

- **User-friendly API**: Simple interface to benchmark your AI agents
- **Progress Tracking**: Visual progress bars for benchmark runs
- **Parallel Processing**: Run benchmarks concurrently for faster execution
- **Asynchronous Support**: Async API for high-performance applications
- **Automatic Submission**: Submit scores directly to the leaderboard
- **Visualization**: Automatic results visualization with charts

## Installation

```bash
# Install from the directory
pip install -r requirements.txt
```

## Getting Started

1. Register on the [CRM Benchmark Website](http://localhost:5000) to get your API key
2. Import the library and create a client:

```python
from crm_benchmark_lib import BenchmarkClient

# Create a client with your API key
client = BenchmarkClient(api_key="your_api_key_here")
```

3. Define your agent function:

```python
def my_agent(question: str, data_frame: pd.DataFrame) -> str:
    """
    This function should implement your agent's logic.
    It receives a question and a pandas DataFrame with the data.
    It should return the agent's response as a string.
    """
    # Your agent implementation here
    return "The answer is..."
```

4. Run the benchmark and submit results:

```python
results = client.run_and_submit(
    agent_callable=my_agent,
    agent_name="My CRM Agent v1.0"
)

print(f"Final Score: {results['overall_average']:.2f}%")
```

## Examples

Check out the `examples` directory for complete example scripts:

- `basic_usage.py`: Shows the basic usage of the library
- `async_usage.py`: Demonstrates asynchronous benchmark execution

## Advanced Usage

### Parallel Processing

By default, benchmarks are run in parallel for faster execution:

```python
results = client.run_full_benchmark(
    agent_callable=my_agent,
    parallel=True  # Enable parallel processing (default)
)
```

You can control the number of parallel workers:

```python
client = BenchmarkClient(
    api_key="your_api_key_here",
    max_workers=8  # Run up to 8 benchmarks in parallel
)
```

### Asynchronous Processing

For even higher performance, use the async client:

```python
import asyncio
from crm_benchmark_lib import AsyncBenchmarkClient

async def main():
    async with AsyncBenchmarkClient(api_key="your_api_key_here") as client:
        results = await client.run_and_submit(
            agent_callable=my_agent,
            agent_name="My CRM Agent v1.0"
        )
        print(f"Final Score: {results['overall_average']:.2f}%")

asyncio.run(main())
```

### Custom Paths

Specify custom paths for question files and CSV data:

```python
results = client.run_full_benchmark(
    agent_callable=my_agent,
    base_dir="/path/to/question/files",
    csv_dir="/path/to/csv/files"
)
```

## API Documentation

### BenchmarkClient

The main client for running benchmarks and submitting scores.

```python
client = BenchmarkClient(
    api_key="your_api_key_here",
    server_url="http://localhost:5000",  # Default server URL
    max_workers=4,  # Maximum number of parallel workers
    show_progress=True,  # Show progress bars
    log_level=logging.INFO  # Logging level
)
```

#### Methods

- `run_benchmark(agent_callable, questions_json_path, csv_data_path)`: Run a single benchmark
- `run_batch(agent_callable, questions_json_paths, csv_data_paths, parallel=True)`: Run multiple benchmarks
- `run_full_benchmark(agent_callable, parallel=True, base_dir=None, csv_dir=None)`: Run the full benchmark suite
- `submit_score(agent_name, score)`: Submit a score to the leaderboard
- `run_and_submit(agent_callable, agent_name, parallel=True, visualize=True)`: Run benchmarks and submit scores

### AsyncBenchmarkClient

Asynchronous version of the benchmark client for high-performance applications.

```python
client = AsyncBenchmarkClient(
    api_key="your_api_key_here",
    server_url="http://localhost:5000",
    max_concurrency=4,  # Maximum concurrent tasks
    show_progress=True,
    log_level=logging.INFO
)
```

#### Methods

Similar to BenchmarkClient, but with async versions:

- `run_benchmark_async(agent_callable, questions_json_path, csv_data_path)`: Run a benchmark asynchronously
- `run_batch_async(agent_callable, questions_json_paths, csv_data_paths)`: Run multiple benchmarks asynchronously
- `run_full_benchmark_async(agent_callable, base_dir=None, csv_dir=None)`: Run the full benchmark suite asynchronously
- `submit_score(agent_name, score)`: Submit a score to the leaderboard asynchronously
- `run_and_submit(agent_callable, agent_name, visualize=True)`: Run and submit asynchronously

## Contributing

Contributions are welcome! Feel free to submit pull requests or open issues.

## License

MIT 