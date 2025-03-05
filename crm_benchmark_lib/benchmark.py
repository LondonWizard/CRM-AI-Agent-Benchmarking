# benchmark.py

"""
Main user-facing interface to run the benchmark.
"""

import time
import logging
from typing import Callable
import pandas as pd
from .evaluator import load_questions, evaluate_response_with_variants, compute_weighted_score

logger = logging.getLogger(__name__)
logger.setLevel(logging.CRITICAL)

def run_benchmark(
    agent_callable: Callable[[str, pd.DataFrame], str],
    questions_json_path: str,
    csv_data_path: str,
    optional_post_function: Callable[[dict], None] = None
):
    """
    - agent_callable: user-provided function that takes (question_text, dataframe) -> returns agent response str
    - questions_json_path: path to the question set JSON
    - csv_data_path: path to the CSV file that the agent might parse for context
    - optional_post_function: placeholder to send results to an external API, if desired

    Returns a dict with overall results, including question-by-question detail.
    """
    logger.info("=== Running benchmark ===")
    logger.info("Question Set JSON: %s", questions_json_path)
    logger.info("CSV Data: %s", csv_data_path)

    questions = load_questions(questions_json_path)
    df = pd.read_csv(csv_data_path)

    question_results = []
    total_time = 0.0

    for q in questions:
        question_id = q["question_id"]
        question_text = q["question_text"]
        category = q["category"]
        correct_answer = q["correct_answer"]

        logger.debug("Asking question: %s (%s)", question_id, category)

        start_time = time.time()
        # Call the user’s AI agent function
        agent_response = agent_callable(question_text, df)
        end_time = time.time()
        elapsed = end_time - start_time
        total_time += elapsed

        logger.debug("Agent response: %r", agent_response)

        # Evaluate response
        # Optionally pass the CSV text if you want the evaluator to see it
        # or you can do: csv_data=df.to_string() if you want the entire CSV in the prompt.
        score, debug_info = evaluate_response_with_variants(
            agent_response, correct_answer, csv_data=""
        )

        logger.debug("Score=%.2f, Debug=%s", score, debug_info)

        question_results.append({
            "question_id": question_id,
            "category": category,
            "question_text": question_text,
            "agent_response": agent_response,
            "score": score,
            "evaluation_debug": debug_info,
            "time_taken_seconds": round(elapsed, 3)
        })

    # Weighted final
    final_percentage = compute_weighted_score(question_results)

    results_obj = {
        "overall_weighted_score_percent": final_percentage,
        "total_time_seconds": round(total_time, 3),
        "question_details": question_results
    }

    logger.info("=== Final Weighted Score: %s ===", final_percentage)

    # If an optional function is provided, pass results
    if optional_post_function:
        optional_post_function(results_obj)

    return results_obj
