# test.py (in crm_benchmark_lib)
import os
import re
import logging
import pandas as pd
import matplotlib.pyplot as plt
from .benchmark import run_benchmark
from .evaluator import load_questions
from typing import Callable

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def run_tests_on_all_csvs(agent_callable: Callable[[str, pd.DataFrame], str]) -> float:
    """
    Scans 'generated_csvs/' for CSV files named like D1_xxx.csv, D2_xxx.csv, etc.
    Then runs the agent on each file for the matching question set JSON
    (e.g., 'dataset_1_questions.json' for D1, etc.).

    Collects the weighted final score for each CSV. 
    Averages them by dataset, plots them, and then returns
    the overall average score across all CSVs.
    """
    folder = "generated_csvs"
    if not os.path.exists(folder):
        logger.error("No generated_csvs folder found.")
        return 0.0

    dataset_to_json_map = {
        "D1": "dataset_1_questions.json",
        "D2": "dataset_2_questions.json",
        "D3": "dataset_3_questions.json",
        "D4": "dataset_4_questions.json",
        "D5": "dataset_5_questions.json",
    }

    scores_by_dataset = { "D1": [], "D2": [], "D3": [], "D4": [], "D5": [] }
    all_scores = []  # keep track of all final scores (across all datasets)

    for fname in os.listdir(folder):
        if not fname.lower().endswith(".csv"):
            continue
        match = re.match(r"^(D[1-5])_.*\.csv", fname)
        if not match:
            logger.debug("Skipping non-dataset file: %s", fname)
            continue

        dataset_prefix = match.group(1)
        csv_path = os.path.join(folder, fname)

        qjson = dataset_to_json_map.get(dataset_prefix)
        if not qjson or not os.path.exists(qjson):
            logger.warning("No matching question set JSON found for %s", fname)
            continue

        # Run the benchmark on this CSV
        results = run_benchmark(
            agent_callable=agent_callable,
            questions_json_path=qjson,
            csv_data_path=csv_path
        )
        final_score = results["overall_weighted_score_percent"]

        # Store the per-CSV final score
        scores_by_dataset[dataset_prefix].append(final_score)
        all_scores.append(final_score)
        logger.info("%s => Weighted Score: %s", fname, final_score)

    # Compute average for each dataset
    avg_scores = {}
    for ds_prefix, sc_list in scores_by_dataset.items():
        if len(sc_list) > 0:
            avg = sum(sc_list) / len(sc_list)
        else:
            avg = 0.0
        avg_scores[ds_prefix] = round(avg, 2)

    # Compute overall average across all CSVs
    if len(all_scores) > 0:
        overall_avg = sum(all_scores) / len(all_scores)
    else:
        overall_avg = 0.0
    overall_avg = round(overall_avg, 2)

    logger.info("\n=== Average Scores by Dataset ===")
    for ds_prefix in ["D1","D2","D3","D4","D5"]:
        logger.info("%s: %s", ds_prefix, avg_scores[ds_prefix])

    logger.info("Overall average across all CSV files: %.2f", overall_avg)

    # Plot the bar chart of per-dataset averages
    labels = list(avg_scores.keys())
    values = [avg_scores[k] for k in labels]

    plt.figure(figsize=(6,4))
    plt.bar(labels, values, color='skyblue')
    plt.ylim(0,100)
    plt.title("Average Weighted Scores by Dataset")
    plt.xlabel("Dataset")
    plt.ylabel("Score (%)")
    for i, v in enumerate(values):
        plt.text(i, v+1, str(v), ha='center')
    plt.tight_layout()
    plt.show()

    # Return the overall average
    return overall_avg
