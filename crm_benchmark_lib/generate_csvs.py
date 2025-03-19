# generate_csvs.py
"""
This script generates 25 CSV files (5 for each set of questions: D1, D2, D3, D4, D5).
Each CSV is intended to contain relevant data that an AI agent might need to analyze
in order to answer the questions for that set.

We've minimized random clutter so the primary "trends" are obvious.
"""

import os
import random
import string
from data_generation import (
    generate_dataset_for_d1,
    generate_dataset_for_d2,
    generate_dataset_for_d3,
    generate_dataset_for_d4,
    generate_dataset_for_d5
)

# Determine the output folder relative to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FOLDER = os.path.join(SCRIPT_DIR, "generated_csvs")

def random_suffix(length=5):
    """Helper to generate a random string suffix for uniqueness."""
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))

def ensure_output_directory():
    """Create the output directory if it doesn't exist."""
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        print(f"Created directory: {OUTPUT_FOLDER}")

def main():
    """Generate 5 variations of each dataset (D1-D5)."""
    ensure_output_directory()
    
    # Generator functions for each dataset
    generators = {
        'D1': generate_dataset_for_d1,
        'D2': generate_dataset_for_d2,
        'D3': generate_dataset_for_d3,
        'D4': generate_dataset_for_d4,
        'D5': generate_dataset_for_d5
    }
    
    # Generate 5 variations for each dataset
    for dataset_name, generator_func in generators.items():
        for file_index in range(1, 6):
            # Create a unique filename with random suffix
            suffix = random_suffix()
            filename = f"{dataset_name}_file{file_index}_{suffix}.csv"
            filepath = os.path.join(OUTPUT_FOLDER, filename)
            
            try:
                # Generate the dataset with the specific output path
                df = generator_func(csv_path=filepath)
                print(f"Generated: {filepath}")
            except Exception as e:
                print(f"Error generating {dataset_name} dataset: {e}")
                continue

if __name__ == "__main__":
    main()
