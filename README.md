# CRM AI Agent Benchmark

This repository provides a simple benchmark framework for AI agents that analyze synthetic CRM data. It includes:

- **data_generation.py**  
  Generates synthetic CSV files containing:
    1. Employee info (employees.csv)  
    2. Deal info (deals.csv)  
    3. Email threads (emails.csv)  

- **tests.py**  
  Defines multiple test functions that produce "expected conclusions" from the CRM data. It also defines a scoring function (`score_agent_response_extended`) that uses the OpenAI API to categorize the agent's response as `correct`, `opposite`, `unrelated`, or `partially correct`.  

- **main.py**  
  Loads the CSV files, gathers the expected conclusions, and compares them against actual agent responses.  
  You can define any number of agent responses (strings) in a Python dictionary and then run the `run_benchmark` function to see how well each agent’s response aligns with the expected conclusions.  

## Installation and Setup

1. **Clone this repo** (or download the files).
2. **Create a virtual environment** (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
Install dependencies:
bash
Copy
pip install -r requirements.txt
(If you need to create a requirements.txt, it might include packages like pandas, openai, python-dotenv, numpy. For example:
nginx
Copy
openai
python-dotenv
pandas
numpy
)
Set your OpenAI API key. Create a file named .env in the same directory, with:
ini
Copy
OPENAI_API_KEY=sk-...
Generate synthetic data:
bash
Copy
python data_generation.py
This creates three CSV files in your working directory:
employees.csv
deals.csv
emails.csv
Run the main benchmark:
bash
Copy
python main.py
This will:
Load the CSV data
Compile multiple test conclusions
Evaluate the sample (mock) agent responses
Print each agent’s final score and details
Customizing
Modify or add new test functions in tests.py to expand the range of CRM insights you want to evaluate (e.g., top performer in certain regions, analysis of email contents, etc.).
Add additional synthetic columns or data in data_generation.py.
In main.py, change or add your own agent responses (or integrate a real AI model’s output) for benchmarking.