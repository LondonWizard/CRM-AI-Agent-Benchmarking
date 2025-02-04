
# CRM AI Agent Benchmark (Continuous Scoring)

This repository provides a **benchmark framework** for AI agents that analyze synthetic Salesforce-like CRM data, then answer specific **JSON-based** questions. Each question is scored with a **0.000–1.000** numeric rating (3 decimal places), allowing for more nuanced partial correctness.

## Data Files

We supply **three CSV files** representing typical Salesforce exports:

1. **`users.csv`**: Basic user information (ID, name, department, active status).  
2. **`opportunities.csv`**: Deal records (ID, name, stage, amount, owner, etc.).  
3. **`emailmessages.csv`**: Email messages referencing deals (subject, from/to addresses, text body, etc.).

There are **no aggregated columns** in these CSVs. The AI must interpret raw data—like summing amounts or calculating close times—if it needs to answer deeper questions about top performers, close ratios, etc.

## Questions File

- **`questions.json`**: Contains a set of **10** example questions. Each question has:
  - A **`question_id`**  
  - A **`question_text`**  
  - A **`category`** (e.g., `employee_performance`, `feedback_to_employees`, etc.)  
  - A **`correct_answer`** object with:
    - **`main_answer`**  
    - **`acceptable_variants`** (phrases also considered correct)  
    - **`wrong_variants`** (explicitly incorrect statements)

**Example** of one question entry:

```json
{
  "question_id": "Q1",
  "question_text": "Which user has the highest total closed-won amount?",
  "category": "employee_performance",
  "correct_answer": {
    "main_answer": "Margaret Carter has the highest total closed-won opportunity amount.",
    "acceptable_variants": [
      "Margaret Carter is the top performer by closed-won revenue",
      "Margaret Carter leads all users in closed-won deals by amount"
    ],
    "wrong_variants": [
      "John Roberts has the highest total closed-won amount",
      "Anyone else is the top for closed-won"
    ]
  }
}
```

## Code Structure

1. **`tests.py`**  
   - **`evaluate_response_with_variants`**: Sends a prompt to GPT instructing it to produce a single **numeric rating** in `[0.000...1.000]`.  
   - **`compute_weighted_score`**: Averages question scores by category and applies custom weighting (e.g., `employee_performance` = 35%, `feedback_to_employees` = 15%, etc.).  
   - **`run_benchmark`**: Loads the questions, evaluates each agent’s entire response, and compiles a final **weighted** score.

2. **`main.py`**  
   - Demonstrates how to call `run_benchmark` with multiple “mock” agent responses.  
   - Prints final results, including a **weighted score** and a breakdown per question.

3. **CSV Files**  
   - `users.csv`, `opportunities.csv`, `emailmessages.csv` (see `data/` folder, for instance).  
   - These contain realistic examples but **no** aggregated fields.

4. **`questions.json`**  
   - Where each question and correct/acceptable/wrong answers are stored.

## Installation and Setup

1. **Clone** this repo or download the files.  
2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   # or
   venv\Scripts\activate  # Windows
   ```
3. **Install dependencies**, typically including:
   ```bash
   pip install openai python-dotenv pandas
   ```
4. **Set your OpenAI API key**. Create a file named `.env` in the project root with:
   ```
   OPENAI_API_KEY=sk-...
   ```
5. **Make sure** the CSV files (`users.csv`, `opportunities.csv`, `emailmessages.csv`) and `questions.json` are in the correct location so the scripts can find them.

## Running the Benchmark

1. **Edit** or **create** new “mock” agent responses in `main.py`.  
2. **Run**:
   ```bash
   python main.py
   ```
3. **Observe** the output. Each agent will have a **weighted_score** between `0.000` and `1.000`. For each question, a separate rating is printed, along with the raw text from the model (e.g. `0.750`).

## Understanding the Scoring

- The prompt **instructs** GPT to produce a numeric rating from **`0.000` to `1.000`**.  
- **`1.000`** means the response **perfectly** aligns with the **main** or **acceptable** statements, no contradictions.  
- **`0.000`** means the response contradicts or is entirely irrelevant.  
- Values **in-between** (like `0.350`, `0.750`) indicate partially correct or incomplete.

### Weighted Final Score

The benchmark groups questions by category (e.g., `employee_performance`, `feedback_to_employees`, `email_analysis`, `improvement_recs`, `deal_insights`) and:

1. **Averages** the scores of all questions in that category.  
2. **Multiplies** by the category’s weight (defined in `tests.py`’s `CATEGORY_WEIGHTS`).  
3. **Sums** across all categories => final weighted score.  

Example weighting:

- `employee_performance`: 0.35  
- `feedback_to_employees`: 0.15  
- `email_analysis`: 0.15  
- `improvement_recs`: 0.15  
- `deal_insights`: 0.20  

These can be changed if you want a different weighting scheme.

## Example Output

A typical run might produce:

```
=== Benchmark Results ===

Agent: agent_perfect
Weighted Score: 0.964
  - QQ1 (employee_performance) => Score: 1.000
    Model raw output: 1.000
  - QQ2 (employee_performance) => Score: 0.950
    Model raw output: 0.950
  - QQ3 (employee_performance) => Score: 1.000
    ...
  (etc.)

Agent: agent_incorrect
Weighted Score: 0.000
  - QQ1 (employee_performance) => Score: 0.000
    ...
  (etc.)
```

Here, **`agent_perfect`** is near-perfect, while **`agent_incorrect`** fails the test. The exact numeric values will vary depending on how GPT interprets partial correctness.

## Customization

- **Add or remove** questions in `questions.json`. The scoring logic automatically picks them up.  
- **Adjust** the system prompt in `evaluate_response_with_variants` if you want different instructions or scoring scale.  
- **Integrate** your real AI agent output by collecting its responses to each question, then pass them into `run_benchmark`.  
