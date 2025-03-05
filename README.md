
################################################################################
# README.md
################################################################################
"""
# CRM AI Agent Benchmark System

This project provides a minimal viable product for benchmarking AI-based CRM agents
against a set of standardized questions and correct answers. It includes:

1. **CSV Data Generation** – Creates CSVs that contain relevant data for each question set.
2. **Benchmark Library** – Contains code to:
   - Ask each question to your AI Agent,
   - Capture the response and timing,
   - Evaluate the correctness of the agent’s answer,
   - Produce a final numeric score.
3. **Flask Website** – A simple user registration, login, and leaderboard to store and
   display agent performance. Each user receives an API key upon registration.

## Installation

1. Clone or download this repository.
2. Make sure you have Python 3.8+ installed.
3. Install required libraries:

```bash
pip install -r requirements.txt
```

## Setup

1. **Generate the CSV data** for each question set by running:
   ```bash
   python generate_csvs.py
   ```
   This will create 5 CSV files per question set (total 25 CSVs) in a `generated_csvs/`
   folder (created automatically).

2. **Run the Flask website** (for user signup and leaderboard):
   ```bash
   cd website
   flask run
   ```
   By default, it runs on http://127.0.0.1:5000.

3. **Using the Benchmark Library**:
   - See `main.py` for an example. In short:
     - You provide a function that calls your AI agent:
       ```python
       def my_agent_function(input_text: str, dataframe) -> str:
           # 1) Possibly parse the CSV data (in 'dataframe') if needed
           # 2) Send 'input_text' to your AI model (not shown here)
           # 3) Return the model's response as a string
           return "Agent's best guess."
       ```
     - Then pass it to `run_benchmark()` in `benchmark.py` to evaluate your agent
       on any question dataset JSON file.

## Future Extensions

- Integrate an API endpoint to submit results automatically to the website's
  leaderboard (by implementing the placeholder function inside the library).
- Expand question sets, CSV generation logic, or scoring logic as needed.

Enjoy benchmarking your CRM AI agent!