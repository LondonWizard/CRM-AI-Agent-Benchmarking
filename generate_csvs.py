# generate_csvs.py
"""
This script generates 25 CSV files (5 for each set of questions: D1, D2, D3, D4, D5).
Each CSV is intended to contain relevant data that an AI agent might need to analyze
in order to answer the questions for that set.

We've minimized random clutter so the primary "trends" are obvious.
"""

import os
import pandas as pd
import random
import string

from crm_benchmark_lib.data_generation import (
    generate_dataset_for_d1,
    generate_dataset_for_d2,
    generate_dataset_for_d3,
    generate_dataset_for_d4,
    generate_dataset_for_d5
)

OUTPUT_FOLDER = "generated_csvs"

def random_suffix(length=5):
    """Helper to generate a random string suffix for uniqueness."""
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))

def main():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    # For each dataset (D1..D5), generate 5 CSVs with random variations
    for i in range(1, 6):
        for file_index in range(1, 6):
            if i == 1:
                df = generate_dataset_for_d1()
                prefix = "D1"
            elif i == 2:
                df = generate_dataset_for_d2()
                prefix = "D2"
            elif i == 3:
                df = generate_dataset_for_d3()
                prefix = "D3"
            elif i == 4:
                df = generate_dataset_for_d4()
                prefix = "D4"
            else:
                df = generate_dataset_for_d5()
                prefix = "D5"

            # Optionally, add a small “twist” of random variation in the data
            # so each file isn’t identical. For example, shuffle rows or
            # add a minor change in a numeric field.

            suffix = random_suffix()
            filename = f"{prefix}_file{file_index}_{suffix}.csv"
            filepath = os.path.join(OUTPUT_FOLDER, filename)
            df.to_csv(filepath, index=False)
            print(f"Generated: {filepath}")

if __name__ == "__main__":
    main()
