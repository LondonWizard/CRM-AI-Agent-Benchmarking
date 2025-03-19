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
from .evaluator import load_questions, evaluate_response_with_variants
from .config import CATEGORY_SECTION_WEIGHTS
import glob
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

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
        try:
            # Your existing agent code here
            answer = ...
            
            # Add validation
            if not isinstance(answer, str):
                logger.warning(f"Agent returned non-string answer: {type(answer)}")
                answer = str(answer)
            
            return answer
            
        except Exception as e:
            logger.error(f"Agent error: {str(e)}")
            return "Error processing question"
    
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
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        retry_statuses: Optional[list] = None,
        max_workers: int = 4,
        show_progress: bool = True,
        log_level: int = logging.INFO
    ):
        """
        Initialize the benchmark client.
        
        Args:
            api_key: Your API key from the CRM Benchmark website
            server_url: URL of the leaderboard server
            max_retries: Maximum number of retries for failed requests
            backoff_factor: Factor to determine wait time between retries
            retry_statuses: List of HTTP status codes to retry on
            max_workers: Maximum number of parallel workers for batch processing
            show_progress: Whether to show progress bars
            log_level: Logging level (default: INFO)
        """
        self.api_key = api_key
        self.server_url = server_url.rstrip("/")
        
        # Set up retry strategy
        if retry_statuses is None:
            retry_statuses = [408, 429, 500, 502, 503, 504]
        
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=retry_statuses,
            allowed_methods=["POST", "GET"]  # Allow retries on POST requests
        )
        
        # Create session with retry adapter
        self.session = requests.Session()
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Validate API key
        if not self._validate_api_key_format(api_key):
            logger.warning("API key format appears invalid. API keys should start with 'crm-' followed by 48 hex characters.")
        
        self.max_workers = max_workers
        self.show_progress = show_progress
        
        # Set up logging
        logger.setLevel(log_level)
    
    def _validate_api_key_format(self, api_key: str) -> bool:
        """Perform basic validation on API key format."""
        # Check if the API key starts with "crm-" and is followed by 48 hex characters
        if not isinstance(api_key, str):
            return False
        
        if not api_key.startswith("crm-"):
            return False
        
        hex_part = api_key[4:]  # Get the part after "crm-"
        return len(hex_part) == 48 and all(c in "0123456789abcdef" for c in hex_part.lower())
    
    def run_benchmark(
        self,
        agent_callable: Callable[[str, pd.DataFrame], str],
        questions_json_path: str,
        csv_data_path: str
    ) -> Dict[str, Any]:
        """Run a single benchmark with proper evaluation and retry logic."""
        try:
            logger.info(f"Starting benchmark with {questions_json_path} and {csv_data_path}")
            
            # Use the benchmark module's run_benchmark function
            results = run_benchmark(
                agent_callable=agent_callable,
                questions_json_path=questions_json_path,
                csv_data_path=csv_data_path
            )
            
            # Ensure the result has the structure expected by the rest of the client code
            if isinstance(results, dict):
                # Convert score from 0-100 to 0.0-1.0 if needed
                if "overall_weighted_score_percent" in results:
                    # Ensure score is in percentage format (0-100)
                    score = results["overall_weighted_score_percent"]
                    if isinstance(score, float) and 0 <= score <= 1:
                        # Convert from 0.0-1.0 to 0-100
                        results["overall_weighted_score_percent"] = score * 100
                
                # Convert results to expected format if needed
                if "overall_weighted_score_percent" not in results and "question_details" in results:
                    # This is the format from benchmark.py
                    question_details = results.get("question_details", [])
                    
                    # Convert scores from 0.0-1.0 to 0-100 if needed
                    for question in question_details:
                        if "score" in question and isinstance(question["score"], float) and 0 <= question["score"] <= 1:
                            question["score"] = question["score"] * 100
                    
                    # Calculate weighted final score
                    final_score = 0
                    total_weight = 0
                    
                    for question in question_details:
                        score = question.get("score", 0)
                        category = question.get("category", "")
                        weight = CATEGORY_SECTION_WEIGHTS.get(category, 1)
                        
                        final_score += score * weight
                        total_weight += weight
                    
                    if total_weight > 0:
                        final_score = final_score / total_weight
                    
                    # Calculate metadata that's expected by other client methods
                    questions_processed = len(question_details)
                    questions_failed = sum(1 for q in question_details if q.get("score", 0) <= 10)
                    
                    # Return in the expected format
                    return {
                        "overall_weighted_score_percent": final_score,
                        "results": question_details,
                        "error": None,
                        "metadata": {
                            "questions_processed": questions_processed,
                            "questions_failed": questions_failed,
                            "total_score": sum(q.get("score", 0) for q in question_details),
                            "total_weight": total_weight
                        }
                    }
            
            return results
            
        except Exception as e:
            logger.error(f"Critical benchmark error: {str(e)}")
            return {
                "overall_weighted_score_percent": 0,
                "results": [],
                "error": str(e),
                "metadata": {
                    "questions_processed": 0,
                    "questions_failed": 0,
                    "total_score": 0,
                    "total_weight": 0
                }
            }
    
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
                try:
                    result = self.run_benchmark(
                        agent_callable=agent_callable,
                        questions_json_path=questions_json_paths[i],
                        csv_data_path=csv_data_paths[i]
                    )
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error in benchmark {i}: {str(e)}")
                    results.append({"error": str(e), "overall_weighted_score_percent": 0})
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
                        results.append((idx, result))
                    except Exception as e:
                        logger.error(f"Error in benchmark {idx}: {str(e)}")
                        results.append((idx, {"error": str(e), "overall_weighted_score_percent": 0}))
                    if progress_bar:
                        progress_bar.update(1)
                
                # Sort results by original index
                results.sort(key=lambda x: x[0])
                results = [r[1] for r in results]
        
        if progress_bar:
            progress_bar.close()
            
        return results
    
    def submit_score(self, agent_name: str, score: float, dataset_scores: Dict[str, float] = None) -> Dict[str, Any]:
        """Submit a score to the leaderboard with retry logic."""
        url = f"{self.server_url}/submit_agent_score_api"
        
        # Ensure score is a valid number
        try:
            score = float(score)
        except (TypeError, ValueError):
            score = 0.0
        
        # Ensure agent_name is a string
        agent_name = str(agent_name) if agent_name else "Unknown Agent"
        
        # Prepare payload
        payload = {
            "api_key": str(self.api_key).strip(),
            "agent_name": agent_name,
            "score": score,  # Use score instead of overall_score
            "dataset_scores": dataset_scores or {}
        }
        
        try:
            # Make POST request with retry logic handled by the session
            response = self.session.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )
            
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = {"raw_response": response.text}
            
            if response.status_code == 200:
                logger.info(f"Score submitted successfully: {score}")
                return response_data
            else:
                error_msg = f"Error submitting score: {response.status_code} - {response_data}"
                logger.error(error_msg)
                return {
                    "status": "error",
                    "message": error_msg,
                    "http_status": response.status_code,
                    "response": response_data
                }
                
        except Exception as e:
            error_msg = f"Exception when submitting score: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg
            }
    
    def locate_question_jsons(self, base_dir=None):
        """Locate all question JSON files."""
        if base_dir is None:
            # Try multiple possible locations
            possible_dirs = [
                "dataset_questions",
                "crm_benchmark_lib/dataset_questions",
                os.path.join(os.path.dirname(__file__), "dataset_questions")
            ]
            
            for dir_path in possible_dirs:
                if os.path.exists(dir_path):
                    base_dir = dir_path
                    break
            
        if base_dir is None:
                raise FileNotFoundError("Cannot find dataset_questions directory")
        
        logger.info(f"Looking for question JSONs in: {base_dir}")
        
        # Find all JSON files that match the pattern dataset_X_questions.json
        json_files = []
        for i in range(1, 6):
            json_path = os.path.join(base_dir, f"dataset_{i}_questions.json")
            if os.path.exists(json_path):
                json_files.append(json_path)
            else:
                logger.warning(f"Could not find {json_path}")
        
        if not json_files:
            raise FileNotFoundError("No question JSON files found")
        
        return json_files

    def locate_csv_files(self, csv_dir=None):
        """Locate all CSV files for benchmarking."""
        if csv_dir is None:
            # Try multiple possible locations
            possible_dirs = [
                "generated_csvs",
                "crm_benchmark_lib/generated_csvs",
                os.path.join(os.path.dirname(__file__), "generated_csvs")
            ]
            
            for dir_path in possible_dirs:
                if os.path.exists(dir_path):
                    csv_dir = dir_path
                    break
            
            if csv_dir is None:
                # Generate the CSV files if they don't exist
                logger.info("CSV directory not found. Generating CSV files...")
                from .generate_csvs import main as generate_csvs
                generate_csvs()
                
                # Try the locations again
                for dir_path in possible_dirs:
                    if os.path.exists(dir_path):
                        csv_dir = dir_path
                        break
                
                if csv_dir is None:
                    raise FileNotFoundError("Cannot find generated_csvs directory")
        
        logger.info(f"Looking for CSV files in: {csv_dir}")
        
        # Find all CSV files that match the pattern D[1-5]_*.csv
        csv_files = []
        for i in range(1, 6):
            pattern = f"D{i}_*.csv"
            matching_files = glob.glob(os.path.join(csv_dir, pattern))
            if matching_files:
                csv_files.extend(matching_files)
            else:
                logger.warning(f"No CSV files found matching {pattern}")
        
        if not csv_files:
            raise FileNotFoundError("No CSV files found")
        
        return csv_files
    
    def run_full_benchmark(
        self,
        agent_callable: Callable[[str, pd.DataFrame], str],
        parallel: bool = True,
        base_dir: Optional[str] = None,
        csv_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run the full benchmark suite."""
        try:
            logger.info("\nStarting full benchmark suite")
            
            # Find CSV files first
            all_csv_files = self.locate_csv_files(csv_dir)
            logger.info(f"Found {len(all_csv_files)} CSV files")
            
            # Organize CSV files by dataset prefix
            dataset_csvs = {}
            for csv_file in all_csv_files:
                filename = os.path.basename(csv_file)
                if filename.startswith('D'):
                    prefix = filename[:2]  # Get D1, D2, etc.
                    if prefix not in dataset_csvs:
                        dataset_csvs[prefix] = []
                    dataset_csvs[prefix].append(csv_file)
            
            logger.info(f"Dataset distribution: {', '.join(f'{k}: {len(v)}' for k, v in dataset_csvs.items())}")
            
            # Find question files
            if base_dir is None:
                base_dir = os.path.join(os.path.dirname(__file__), "dataset_questions")
            
            # Prepare batch run parameters
            questions_json_paths = []
            csv_data_paths = []
            dataset_mapping = {}
            
            for dataset_num in range(1, 6):
                dataset_prefix = f"D{dataset_num}"
                json_path = os.path.join(base_dir, f"dataset_{dataset_num}_questions.json")
                
                if os.path.exists(json_path) and dataset_prefix in dataset_csvs:
                    logger.info(f"Found question set for {dataset_prefix}: {json_path}")
                    for csv_file in dataset_csvs[dataset_prefix]:
                        questions_json_paths.append(json_path)
                        csv_data_paths.append(csv_file)
                        dataset_mapping[csv_file] = dataset_prefix
            
            if not questions_json_paths:
                logger.error("No valid CSV files or question sets found")
                return {"status": "error", "message": "No valid CSV files or question sets found"}
            
            logger.info(f"Running {len(questions_json_paths)} total benchmarks")
            
            # Run the benchmarks
            results = self.run_batch(
                agent_callable=agent_callable,
                questions_json_paths=questions_json_paths,
                csv_data_paths=csv_data_paths,
                parallel=parallel
            )
            
            # Process results by dataset
            dataset_scores = {f"D{i}": [] for i in range(1, 6)}
            all_scores = []
            total_processed = 0
            total_failed = 0
            
            for i, result in enumerate(results):
                if result is None:
                    logger.error(f"Benchmark {i} returned None result")
                    continue
                
                if isinstance(result, dict):
                    if result.get("error"):
                        logger.error(f"Benchmark {i} error: {result['error']}")
                        continue
                    
                    score = result.get("overall_weighted_score_percent", 0)
                    metadata = result.get("metadata", {})
                    
                    total_processed += metadata.get("questions_processed", 0)
                    total_failed += metadata.get("questions_failed", 0)
                    
                    if score is not None:
                        csv_path = csv_data_paths[i]
                        dataset = dataset_mapping[csv_path]
                        dataset_scores[dataset].append(score)
                        all_scores.append(score)
                        logger.info(f"Dataset {dataset} benchmark {i} score: {score:.2f}%")
            
            logger.info(f"\nProcessing Summary:")
            logger.info(f"Total questions processed: {total_processed}")
            logger.info(f"Total questions failed: {total_failed}")
            logger.info(f"Valid scores collected: {len(all_scores)}")
            
            if not all_scores:
                logger.error("No valid scores were calculated")
                return {"status": "error", "message": "No valid scores were calculated"}
            
            # Calculate averages
            dataset_averages = {}
            for dataset, scores in dataset_scores.items():
                if scores:
                    avg = sum(scores) / len(scores)
                    dataset_averages[dataset] = avg
                    logger.info(f"Average score for {dataset}: {avg:.2f}%")
            
            # Calculate overall average
            overall_average = sum(all_scores) / len(all_scores)
            logger.info(f"Overall average score: {overall_average:.2f}%")
            
            return {
                "overall_average": overall_average,
                "dataset_averages": dataset_averages,
                "individual_results": results,
                "metadata": {
                    "total_questions_processed": total_processed,
                    "total_questions_failed": total_failed,
                    "total_benchmarks": len(questions_json_paths),
                    "valid_scores": len(all_scores)
                }
            }
            
        except Exception as e:
            logger.error(f"Benchmark suite error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
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
        """Run benchmarks and submit results."""
        try:
            # Run the full benchmark
            results = self.run_full_benchmark(
                agent_callable=agent_callable,
                parallel=parallel,
                **kwargs
            )
            
            if "status" in results and results["status"] == "error":
                logger.error(f"Benchmark failed: {results['message']}")
                return results
            
            # Get the overall score and dataset averages
            overall_score = results.get("overall_average", 0)
            dataset_scores = results.get("dataset_averages", {})
            
            if overall_score == 0 and not dataset_scores:
                logger.error("No valid scores were calculated")
                return {
                    "status": "error",
                    "message": "No valid scores were calculated",
                    "results": results
                }
            
            # Log scores before submission
            logger.info(f"Submitting scores for {agent_name}:")
            logger.info(f"Overall score: {overall_score}")
            logger.info(f"Dataset scores: {dataset_scores}")
            
            # Submit the score with dataset details
            submission = self.submit_score(
                agent_name=agent_name,
                score=overall_score,
                dataset_scores=dataset_scores
            )
            
            # Check submission result
            if submission.get("status") == "error":
                logger.error(f"Score submission failed: {submission.get('message')}")
                results["submission_error"] = submission.get("message")
            else:
                logger.info("Score submitted successfully")
            
            # Add submission result to results
            results["submission"] = submission
            
            # Visualize if requested
            if visualize:
                self.visualize_results(results)
            
            return results
            
        except Exception as e:
            error_msg = f"Error in run_and_submit: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg
            }


class AsyncBenchmarkClient:
    """
    Asynchronous version of the benchmark client that uses aiohttp for API calls
    and asyncio for concurrent execution.
    """
    
    def __init__(
        self, 
        api_key: str, 
        server_url: str = DEFAULT_SERVER_URL,
        max_concurrency: int = 4,
        show_progress: bool = True,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        retry_statuses: Optional[list] = None,
        **kwargs
    ):
        """
        Initialize the async benchmark client.
        
        Args:
            api_key: Your API key from the CRM Benchmark website
            server_url: URL of the leaderboard server
            max_concurrency: Maximum number of concurrent tasks
            show_progress: Whether to show progress bars
            max_retries: Maximum number of retries for failed requests
            backoff_factor: Factor to determine wait time between retries
            retry_statuses: List of HTTP status codes to retry on
        """
        self.api_key = api_key
        self.server_url = server_url.rstrip("/")
        self.max_concurrency = max_concurrency
        self.show_progress = show_progress
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        
        if retry_statuses is None:
            retry_statuses = [408, 429, 500, 502, 503, 504]
        self.retry_statuses = retry_statuses
        
        # Initialize semaphore for concurrency control
        self._semaphore = None  # Will be created in async context
        
        # Validate API key
        if not self._validate_api_key_format(api_key):
            logger.warning("API key format appears invalid")
    
    def _validate_api_key_format(self, api_key: str) -> bool:
        """Perform basic validation on API key format."""
        if not isinstance(api_key, str):
            return False
        
        if not api_key.startswith("crm-"):
            return False
        
        hex_part = api_key[4:]
        return len(hex_part) == 48 and all(c in "0123456789abcdef" for c in hex_part.lower())
    
    async def _ensure_semaphore(self):
        """Ensure semaphore is initialized in async context."""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.max_concurrency)
    
    async def submit_score(self, agent_name: str, score: float, dataset_scores: Dict[str, float] = None) -> Dict[str, Any]:
        """Submit a score to the leaderboard."""
        await self._ensure_semaphore()
        
        url = f"{self.server_url}/submit_agent_score_api"
        payload = {
            "api_key": self.api_key,
            "agent_name": agent_name,
            "score": score,
            "dataset_scores": dataset_scores or {}
        }
        
        async with self._semaphore:
            try:
                async with aiohttp.ClientSession() as session:
                    for attempt in range(self.max_retries + 1):
                        try:
                            async with session.post(url, json=payload) as response:
                                if response.status in self.retry_statuses and attempt < self.max_retries:
                                    wait_time = self.backoff_factor * (2 ** attempt)
                                    logger.warning(f"Request failed with status {response.status}. Retrying in {wait_time:.1f} seconds...")
                                    await asyncio.sleep(wait_time)
                                    continue
                                
                                response_data = await response.json()
                                if response.status == 200:
                                    return response_data
                                else:
                                    return {
                                        "status": "error",
                                        "message": f"Request failed with status {response.status}",
                                        "response": response_data
                                    }
                        except Exception as e:
                            if attempt < self.max_retries:
                                wait_time = self.backoff_factor * (2 ** attempt)
                                logger.warning(f"Request failed with error: {str(e)}. Retrying in {wait_time:.1f} seconds...")
                                await asyncio.sleep(wait_time)
                                continue
                            raise
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Failed to submit score: {str(e)}"
                }
    
    async def run_benchmark_async(
        self,
        agent_callable: Callable[[str, pd.DataFrame], str],
        questions_json_path: str,
        csv_data_path: str
    ) -> Dict[str, Any]:
        """Run a single benchmark asynchronously."""
        await self._ensure_semaphore()
        
        async with self._semaphore:
            try:
                # Use the benchmark module's run_benchmark function
                # Since run_benchmark is synchronous, we'll run it in a thread pool
                loop = asyncio.get_event_loop()
                results = await loop.run_in_executor(
                    None,  # Use default executor
                    run_benchmark,
                    agent_callable,
                    questions_json_path,
                    csv_data_path
                )
                
                # Ensure the result has the structure expected by the rest of the client code
                if isinstance(results, dict):
                    # Convert score from 0-100 to 0.0-1.0 if needed
                    if "overall_weighted_score_percent" in results:
                        # Ensure score is in percentage format (0-100)
                        score = results["overall_weighted_score_percent"]
                        if isinstance(score, float) and 0 <= score <= 1:
                            # Convert from 0.0-1.0 to 0-100
                            results["overall_weighted_score_percent"] = score * 100
                    
                    # Convert results to expected format if needed
                    if "overall_weighted_score_percent" not in results and "question_details" in results:
                        # This is the format from benchmark.py
                        question_details = results.get("question_details", [])
                        
                        # Convert scores from 0.0-1.0 to 0-100 if needed
                        for question in question_details:
                            if "score" in question and isinstance(question["score"], float) and 0 <= question["score"] <= 1:
                                question["score"] = question["score"] * 100
                        
                        # Calculate weighted final score
                        final_score = 0
                        total_weight = 0
                        
                        for question in question_details:
                            score = question.get("score", 0)
                            category = question.get("category", "")
                            weight = CATEGORY_SECTION_WEIGHTS.get(category, 1)
                            
                            final_score += score * weight
                            total_weight += weight
                        
                        if total_weight > 0:
                            final_score = final_score / total_weight
                        
                        # Calculate metadata that's expected by other client methods
                        questions_processed = len(question_details)
                        questions_failed = sum(1 for q in question_details if q.get("score", 0) <= 10)
                        
                        # Return in the expected format
                        return {
                            "overall_weighted_score_percent": final_score,
                            "results": question_details,
                            "error": None,
                            "metadata": {
                                "questions_processed": questions_processed,
                                "questions_failed": questions_failed,
                                "total_score": sum(q.get("score", 0) for q in question_details),
                                "total_weight": total_weight
                            }
                        }
                
                return results
                
            except Exception as e:
                logger.error(f"Benchmark error: {str(e)}")
                return {
                    "overall_weighted_score_percent": 0,
                    "results": [],
                    "error": str(e)
                }
    
    def _evaluate_response(self, response: str, correct_answer: Dict[str, Any]) -> float:
        """Evaluate a response against the correct answer and its variants."""
        # Use the evaluator module's function
        score, _ = evaluate_response_with_variants(response, correct_answer)
        return score
    
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
        
        # Create tasks for all benchmarks
        tasks = []
        for i in range(total_benchmarks):
            task = asyncio.create_task(
                self.run_benchmark_async(
                    agent_callable=agent_callable,
                    questions_json_path=questions_json_paths[i],
                    csv_data_path=csv_data_paths[i]
                )
            )
            tasks.append(task)
        
        # Run all tasks concurrently with semaphore control
        completed_tasks = await asyncio.gather(*tasks)
        
        # Process results
        for i, result in enumerate(completed_tasks):
            results[i] = result
            if progress_bar:
                progress_bar.update(1)
        
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