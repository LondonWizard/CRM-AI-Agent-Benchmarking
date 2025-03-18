"""
Client implementations for the CRM Benchmark library.

This module provides user-friendly clients that integrate with the leaderboard API,
include progress tracking, and support async/parallel execution for faster benchmarking.
"""

import os
import time
import json
import asyncio
import aiohttp
import requests
import logging
import pandas as pd
from typing import Callable, Dict, List, Any, Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import matplotlib.pyplot as plt
from .benchmark import run_benchmark
from .evaluator import load_questions

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Default server URL for API submission
DEFAULT_SERVER_URL = "http://localhost:5000"


class BenchmarkClient:
    """
    A client for the CRM Benchmark system that provides:
    - API integration for automatic score submission
    - Progress bars for benchmark runs
    - Parallel processing for faster benchmarking
    - Visualization of results
    
    Basic usage:
    ```python
    from crm_benchmark_lib import BenchmarkClient
    
    # Create a client with your API key
    client = BenchmarkClient(api_key="your_api_key_here")
    
    # Define your agent function
    def my_agent(question: str, data: pd.DataFrame) -> str:
        # Your agent implementation here
        return "The answer is..."
    
    # Run benchmarks and submit results
    client.run_and_submit(
        agent_callable=my_agent,
        agent_name="My CRM Agent v1.0"
    )
    ```
    """
    
    def __init__(
        self, 
        api_key: str, 
        server_url: str = DEFAULT_SERVER_URL,
        max_workers: int = 4,
        show_progress: bool = True,
        log_level: int = logging.INFO
    ):
        """
        Initialize the benchmark client.
        
        Args:
            api_key: Your API key from the CRM Benchmark website
            server_url: URL of the leaderboard server
            max_workers: Maximum number of parallel workers for batch processing
            show_progress: Whether to show progress bars
            log_level: Logging level (default: INFO)
        """
        self.api_key = api_key
        self.server_url = server_url.rstrip("/")
        self.max_workers = max_workers
        self.show_progress = show_progress
        
        # Set up logging
        logger.setLevel(log_level)
        
        # Validate API key format
        if not self._validate_api_key_format(api_key):
            logger.warning("API key format appears invalid. This may cause submission errors.")
    
    def _validate_api_key_format(self, api_key: str) -> bool:
        """Perform basic validation on API key format."""
        # Simple validation: should be a hex string of appropriate length (48 chars)
        return isinstance(api_key, str) and len(api_key) == 48 and all(c in "0123456789abcdef" for c in api_key.lower())
    
    def run_benchmark(
        self,
        agent_callable: Callable[[str, pd.DataFrame], str],
        questions_json_path: str,
        csv_data_path: str
    ) -> Dict[str, Any]:
        """
        Run a single benchmark.
        
        Args:
            agent_callable: Function that takes a question and data frame and returns a response
            questions_json_path: Path to the questions JSON
            csv_data_path: Path to the CSV file to use
            
        Returns:
            Dictionary with benchmark results
        """
        return run_benchmark(
            agent_callable=agent_callable,
            questions_json_path=questions_json_path,
            csv_data_path=csv_data_path
        )
    
    def run_batch(
        self,
        agent_callable: Callable[[str, pd.DataFrame], str],
        questions_json_paths: List[str],
        csv_data_paths: List[str],
        parallel: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Run multiple benchmarks in batch, with optional parallel processing.
        
        Args:
            agent_callable: Function that takes a question and data frame and returns a response
            questions_json_paths: List of paths to question JSON files
            csv_data_paths: List of paths to CSV files
            parallel: Whether to run benchmarks in parallel
            
        Returns:
            List of dictionaries with benchmark results
        """
        if len(questions_json_paths) != len(csv_data_paths):
            raise ValueError("questions_json_paths and csv_data_paths must have the same length")
        
        total_benchmarks = len(questions_json_paths)
        results = []
        
        # Set up progress bar
        progress_bar = None
        if self.show_progress:
            progress_bar = tqdm(total=total_benchmarks, desc="Running benchmarks")
        
        if not parallel or total_benchmarks == 1:
            # Sequential execution
            for i in range(total_benchmarks):
                result = self.run_benchmark(
                    agent_callable=agent_callable,
                    questions_json_path=questions_json_paths[i],
                    csv_data_path=csv_data_paths[i]
                )
                results.append(result)
                if progress_bar:
                    progress_bar.update(1)
        else:
            # Parallel execution using ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=min(self.max_workers, total_benchmarks)) as executor:
                # Submit all tasks
                future_to_idx = {
                    executor.submit(
                        self.run_benchmark,
                        agent_callable=agent_callable,
                        questions_json_path=questions_json_paths[i],
                        csv_data_path=csv_data_paths[i]
                    ): i for i in range(total_benchmarks)
                }
                
                # Process completed tasks
                for future in as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    try:
                        result = future.result()
                        # Store result in correct order
                        results.append((idx, result))
                        if progress_bar:
                            progress_bar.update(1)
                    except Exception as e:
                        logger.error(f"Error in benchmark {idx}: {str(e)}")
                        results.append((idx, {"error": str(e)}))
                        if progress_bar:
                            progress_bar.update(1)
                
                # Sort results by original index
                results.sort(key=lambda x: x[0])
                results = [r[1] for r in results]
        
        if progress_bar:
            progress_bar.close()
        
        return results
    
    def submit_score(self, agent_name: str, score: float) -> Dict[str, Any]:
        """
        Submit a score to the leaderboard.
        
        Args:
            agent_name: Name of the agent
            score: Final score (0-100)
            
        Returns:
            API response
        """
        url = f"{self.server_url}/submit_agent_score_api"
        payload = {
            "api_key": self.api_key,
            "agent_name": agent_name,
            "score": score
        }
        
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                logger.info(f"Score submitted successfully: {score}")
                return response.json()
            else:
                logger.error(f"Error submitting score: {response.status_code} - {response.text}")
                return {"status": "error", "message": response.text}
        except Exception as e:
            logger.error(f"Exception when submitting score: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def locate_csv_files(self, base_dir: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Locate CSV files for benchmarking in the standard directory structure.
        
        Args:
            base_dir: Base directory to search in (default: current directory)
            
        Returns:
            Dictionary mapping dataset prefixes to lists of CSV files
        """
        if base_dir is None:
            base_dir = os.path.join(os.getcwd(), "generated_csvs")
        
        if not os.path.exists(base_dir):
            base_dir = os.path.join(os.getcwd(), "crm_benchmark_lib", "generated_csvs")
            if not os.path.exists(base_dir):
                raise FileNotFoundError(f"Cannot find generated_csvs directory")
        
        result = {
            "D1": [],
            "D2": [],
            "D3": [],
            "D4": [],
            "D5": []
        }
        
        for filename in os.listdir(base_dir):
            if not filename.endswith(".csv"):
                continue
                
            for prefix in result.keys():
                if filename.startswith(prefix):
                    result[prefix].append(os.path.join(base_dir, filename))
        
        # Sort file lists for consistent ordering
        for prefix in result:
            result[prefix].sort()
        
        return result
    
    def run_full_benchmark(
        self,
        agent_callable: Callable[[str, pd.DataFrame], str],
        parallel: bool = True,
        base_dir: Optional[str] = None,
        csv_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run the full benchmark suite (all datasets and CSVs).
        
        Args:
            agent_callable: Function that takes a question and data frame and returns a response
            parallel: Whether to run benchmarks in parallel
            base_dir: Base directory for question files (default: current directory)
            csv_dir: Directory containing CSV files (default: 'generated_csvs')
            
        Returns:
            Dictionary with all results
        """
        # Find question files
        if base_dir is None:
            base_dir = os.getcwd()
            
        # Locate dataset question files
        dataset_to_json_map = {}
        for i in range(1, 6):
            json_path = os.path.join(base_dir, f"dataset_{i}_questions.json")
            if not os.path.exists(json_path):
                # Try alternate path
                json_path = os.path.join(base_dir, "..", f"dataset_{i}_questions.json")
                if not os.path.exists(json_path):
                    logger.warning(f"Could not find dataset_{i}_questions.json")
                    continue
            dataset_to_json_map[f"D{i}"] = json_path
        
        # Find CSV files
        dataset_csvs = self.locate_csv_files(csv_dir)
        
        # Prepare batch run parameters
        questions_json_paths = []
        csv_data_paths = []
        csv_to_dataset = {}  # Keep track of which dataset each CSV belongs to
        
        for dataset_prefix, json_path in dataset_to_json_map.items():
            csv_files = dataset_csvs.get(dataset_prefix, [])
            for csv_file in csv_files:
                questions_json_paths.append(json_path)
                csv_data_paths.append(csv_file)
                csv_to_dataset[csv_file] = dataset_prefix
        
        # Check if we have any benchmarks to run
        if len(questions_json_paths) == 0:
            logger.error("No valid CSV files or question sets found")
            return {"status": "error", "message": "No valid CSV files or question sets found"}
        
        # Run the benchmarks
        logger.info(f"Running {len(questions_json_paths)} benchmarks...")
        results = self.run_batch(
            agent_callable=agent_callable,
            questions_json_paths=questions_json_paths,
            csv_data_paths=csv_data_paths,
            parallel=parallel
        )
        
        # Process results by dataset
        scores_by_dataset = {f"D{i}": [] for i in range(1, 6)}
        all_scores = []
        
        for i, result in enumerate(results):
            score = result.get("overall_weighted_score_percent", 0)
            csv_path = csv_data_paths[i]
            dataset = csv_to_dataset[csv_path]
            
            scores_by_dataset[dataset].append(score)
            all_scores.append(score)
            
            logger.info(f"{os.path.basename(csv_path)} => Score: {score:.2f}%")
        
        # Calculate averages
        avg_scores = {}
        for dataset, scores in scores_by_dataset.items():
            if not scores:
                continue
            avg_scores[dataset] = sum(scores) / len(scores)
        
        # Calculate overall average
        overall_avg = sum(all_scores) / len(all_scores) if all_scores else 0
        
        # Print summary
        logger.info("\n=== Average Scores by Dataset ===")
        for dataset in sorted(avg_scores.keys()):
            logger.info(f"{dataset}: {avg_scores[dataset]:.2f}%")
        logger.info(f"Overall Average: {overall_avg:.2f}%")
        
        # Create result summary
        summary = {
            "overall_average": overall_avg,
            "dataset_averages": avg_scores,
            "individual_results": results
        }
        
        return summary
    
    def visualize_results(self, results: Dict[str, Any]) -> None:
        """
        Visualize benchmark results with a bar chart.
        
        Args:
            results: Results from run_full_benchmark
        """
        avg_scores = results.get("dataset_averages", {})
        if not avg_scores:
            logger.warning("No dataset averages to visualize")
            return
        
        # Create bar chart
        labels = sorted(avg_scores.keys())
        values = [avg_scores[dataset] for dataset in labels]
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(labels, values, color='skyblue')
        
        # Add overall average line
        overall_avg = results.get("overall_average", 0)
        plt.axhline(y=overall_avg, color='red', linestyle='--', label=f'Overall: {overall_avg:.2f}%')
        
        # Add labels and formatting
        plt.ylim(0, 100)
        plt.title("Benchmark Results by Dataset")
        plt.xlabel("Dataset")
        plt.ylabel("Score (%)")
        plt.legend()
        
        # Add data labels to bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{height:.2f}%', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.show()
    
    def run_and_submit(
        self,
        agent_callable: Callable[[str, pd.DataFrame], str],
        agent_name: str,
        parallel: bool = True,
        visualize: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run the full benchmark suite and submit the results to the leaderboard.
        
        Args:
            agent_callable: Function that takes a question and data frame and returns a response
            agent_name: Name of the agent for the leaderboard
            parallel: Whether to run benchmarks in parallel
            visualize: Whether to show visualization of results
            **kwargs: Additional arguments to pass to run_full_benchmark
            
        Returns:
            Dictionary with benchmark results and submission status
        """
        # Run the full benchmark
        logger.info(f"Running full benchmark for agent: {agent_name}")
        results = self.run_full_benchmark(
            agent_callable=agent_callable,
            parallel=parallel,
            **kwargs
        )
        
        # Check if benchmark was successful
        if "overall_average" not in results:
            logger.error("Benchmark failed")
            return {"status": "error", "message": "Benchmark failed", "results": results}
        
        # Submit score
        score = results["overall_average"]
        logger.info(f"Submitting score for {agent_name}: {score:.2f}%")
        submission = self.submit_score(agent_name=agent_name, score=score)
        
        # Add submission status to results
        results["submission"] = submission
        
        # Visualize if requested
        if visualize:
            self.visualize_results(results)
        
        return results


class AsyncBenchmarkClient:
    """
    Asynchronous client for the CRM Benchmark system that provides:
    - Concurrent API calls and benchmark runs
    - Progress tracking
    - High-performance batch processing
    
    Basic usage:
    ```python
    import asyncio
    from crm_benchmark_lib import AsyncBenchmarkClient
    
    # Define your agent function
    def my_agent(question: str, data: pd.DataFrame) -> str:
        # Your agent implementation here
        return "The answer is..."
    
    async def main():
        # Create async client
        client = AsyncBenchmarkClient(api_key="your_api_key_here")
        
        # Run benchmarks and submit results
        results = await client.run_and_submit(
            agent_callable=my_agent,
            agent_name="My CRM Agent v1.0"
        )
        print(f"Final score: {results['overall_average']:.2f}%")
    
    # Run the async function
    asyncio.run(main())
    ```
    """
    
    def __init__(
        self, 
        api_key: str, 
        server_url: str = DEFAULT_SERVER_URL,
        max_concurrency: int = 4,
        show_progress: bool = True,
        log_level: int = logging.INFO
    ):
        """
        Initialize the async benchmark client.
        
        Args:
            api_key: Your API key from the CRM Benchmark website
            server_url: URL of the leaderboard server
            max_concurrency: Maximum number of concurrent tasks
            show_progress: Whether to show progress bars
            log_level: Logging level (default: INFO)
        """
        self.api_key = api_key
        self.server_url = server_url.rstrip("/")
        self.max_concurrency = max_concurrency
        self.show_progress = show_progress
        self.session = None  # Async HTTP session will be initialized when needed
        
        # Set up logging
        logger.setLevel(log_level)
        
        # Validate API key
        if not isinstance(api_key, str) or len(api_key) != 48:
            logger.warning("API key format appears invalid. This may cause submission errors.")
    
    async def _ensure_session(self):
        """Ensure that we have an active HTTP session."""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close the HTTP session."""
        if self.session is not None:
            await self.session.close()
            self.session = None
    
    async def __aenter__(self):
        """Context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()
    
    async def submit_score(self, agent_name: str, score: float) -> Dict[str, Any]:
        """
        Submit a score to the leaderboard asynchronously.
        
        Args:
            agent_name: Name of the agent
            score: Final score (0-100)
            
        Returns:
            API response
        """
        url = f"{self.server_url}/submit_agent_score_api"
        payload = {
            "api_key": self.api_key,
            "agent_name": agent_name,
            "score": score
        }
        
        session = await self._ensure_session()
        
        try:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Score submitted successfully: {score}")
                    return result
                else:
                    text = await response.text()
                    logger.error(f"Error submitting score: {response.status} - {text}")
                    return {"status": "error", "message": text}
        except Exception as e:
            logger.error(f"Exception when submitting score: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def run_benchmark_async(
        self,
        agent_callable: Callable[[str, pd.DataFrame], str],
        questions_json_path: str,
        csv_data_path: str
    ) -> Dict[str, Any]:
        """
        Run a single benchmark asynchronously.
        
        This still blocks the event loop while the benchmark runs,
        but it allows us to run multiple benchmarks concurrently.
        
        Args:
            agent_callable: Function that takes a question and data frame and returns a response
            questions_json_path: Path to the questions JSON
            csv_data_path: Path to the CSV file to use
            
        Returns:
            Dictionary with benchmark results
        """
        # Run the benchmark in a separate thread to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: run_benchmark(
                agent_callable=agent_callable,
                questions_json_path=questions_json_path,
                csv_data_path=csv_data_path
            )
        )
        return result
    
    async def run_batch_async(
        self,
        agent_callable: Callable[[str, pd.DataFrame], str],
        questions_json_paths: List[str],
        csv_data_paths: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Run multiple benchmarks asynchronously.
        
        Args:
            agent_callable: Function that takes a question and data frame and returns a response
            questions_json_paths: List of paths to question JSON files
            csv_data_paths: List of paths to CSV files
            
        Returns:
            List of dictionaries with benchmark results
        """
        if len(questions_json_paths) != len(csv_data_paths):
            raise ValueError("questions_json_paths and csv_data_paths must have the same length")
        
        total_benchmarks = len(questions_json_paths)
        results = [None] * total_benchmarks  # Pre-allocate results list
        
        # Set up progress bar
        progress_bar = None
        if self.show_progress:
            import tqdm.asyncio
            progress_bar = tqdm.asyncio.tqdm(total=total_benchmarks, desc="Running benchmarks")
        
        # Use a semaphore to limit concurrency
        semaphore = asyncio.Semaphore(self.max_concurrency)
        
        async def run_with_semaphore(idx):
            async with semaphore:
                result = await self.run_benchmark_async(
                    agent_callable=agent_callable,
                    questions_json_path=questions_json_paths[idx],
                    csv_data_path=csv_data_paths[idx]
                )
                results[idx] = result
                if progress_bar:
                    progress_bar.update(1)
                return idx, result
        
        # Create tasks for all benchmarks
        tasks = [run_with_semaphore(i) for i in range(total_benchmarks)]
        
        # Run all tasks concurrently
        await asyncio.gather(*tasks)
        
        if progress_bar:
            progress_bar.close()
        
        return results
    
    async def run_full_benchmark_async(
        self,
        agent_callable: Callable[[str, pd.DataFrame], str],
        base_dir: Optional[str] = None,
        csv_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run the full benchmark suite asynchronously.
        
        Args:
            agent_callable: Function that takes a question and data frame and returns a response
            base_dir: Base directory for question files (default: current directory)
            csv_dir: Directory containing CSV files (default: 'generated_csvs')
            
        Returns:
            Dictionary with all results
        """
        # We'll reuse the synchronous client's helper methods for file discovery
        sync_client = BenchmarkClient(
            api_key=self.api_key,
            server_url=self.server_url,
            show_progress=False
        )
        
        # Find question files
        if base_dir is None:
            base_dir = os.getcwd()
            
        # Locate dataset question files
        dataset_to_json_map = {}
        for i in range(1, 6):
            json_path = os.path.join(base_dir, f"dataset_{i}_questions.json")
            if not os.path.exists(json_path):
                # Try alternate path
                json_path = os.path.join(base_dir, "..", f"dataset_{i}_questions.json")
                if not os.path.exists(json_path):
                    logger.warning(f"Could not find dataset_{i}_questions.json")
                    continue
            dataset_to_json_map[f"D{i}"] = json_path
        
        # Find CSV files
        dataset_csvs = sync_client.locate_csv_files(csv_dir)
        
        # Prepare batch run parameters
        questions_json_paths = []
        csv_data_paths = []
        csv_to_dataset = {}  # Keep track of which dataset each CSV belongs to
        
        for dataset_prefix, json_path in dataset_to_json_map.items():
            csv_files = dataset_csvs.get(dataset_prefix, [])
            for csv_file in csv_files:
                questions_json_paths.append(json_path)
                csv_data_paths.append(csv_file)
                csv_to_dataset[csv_file] = dataset_prefix
        
        # Check if we have any benchmarks to run
        if len(questions_json_paths) == 0:
            logger.error("No valid CSV files or question sets found")
            return {"status": "error", "message": "No valid CSV files or question sets found"}
        
        # Run the benchmarks
        logger.info(f"Running {len(questions_json_paths)} benchmarks asynchronously...")
        results = await self.run_batch_async(
            agent_callable=agent_callable,
            questions_json_paths=questions_json_paths,
            csv_data_paths=csv_data_paths
        )
        
        # Process results by dataset
        scores_by_dataset = {f"D{i}": [] for i in range(1, 6)}
        all_scores = []
        
        for i, result in enumerate(results):
            score = result.get("overall_weighted_score_percent", 0)
            csv_path = csv_data_paths[i]
            dataset = csv_to_dataset[csv_path]
            
            scores_by_dataset[dataset].append(score)
            all_scores.append(score)
            
            logger.info(f"{os.path.basename(csv_path)} => Score: {score:.2f}%")
        
        # Calculate averages
        avg_scores = {}
        for dataset, scores in scores_by_dataset.items():
            if not scores:
                continue
            avg_scores[dataset] = sum(scores) / len(scores)
        
        # Calculate overall average
        overall_avg = sum(all_scores) / len(all_scores) if all_scores else 0
        
        # Print summary
        logger.info("\n=== Average Scores by Dataset ===")
        for dataset in sorted(avg_scores.keys()):
            logger.info(f"{dataset}: {avg_scores[dataset]:.2f}%")
        logger.info(f"Overall Average: {overall_avg:.2f}%")
        
        # Create result summary
        summary = {
            "overall_average": overall_avg,
            "dataset_averages": avg_scores,
            "individual_results": results
        }
        
        return summary
    
    def visualize_results(self, results: Dict[str, Any]) -> None:
        """
        Visualize benchmark results with a bar chart.
        
        Args:
            results: Results from run_full_benchmark_async
        """
        # Reuse the synchronous client's visualization method
        sync_client = BenchmarkClient(
            api_key=self.api_key,
            server_url=self.server_url,
            show_progress=False
        )
        sync_client.visualize_results(results)
    
    async def run_and_submit(
        self,
        agent_callable: Callable[[str, pd.DataFrame], str],
        agent_name: str,
        visualize: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run the full benchmark suite asynchronously and submit the results to the leaderboard.
        
        Args:
            agent_callable: Function that takes a question and data frame and returns a response
            agent_name: Name of the agent for the leaderboard
            visualize: Whether to show visualization of results
            **kwargs: Additional arguments to pass to run_full_benchmark_async
            
        Returns:
            Dictionary with benchmark results and submission status
        """
        # Run the full benchmark
        logger.info(f"Running full benchmark for agent: {agent_name}")
        results = await self.run_full_benchmark_async(
            agent_callable=agent_callable,
            **kwargs
        )
        
        # Check if benchmark was successful
        if "overall_average" not in results:
            logger.error("Benchmark failed")
            return {"status": "error", "message": "Benchmark failed", "results": results}
        
        # Submit score
        score = results["overall_average"]
        logger.info(f"Submitting score for {agent_name}: {score:.2f}%")
        submission = await self.submit_score(agent_name=agent_name, score=score)
        
        # Add submission status to results
        results["submission"] = submission
        
        # Visualize if requested
        if visualize:
            self.visualize_results(results)
        
        return results 