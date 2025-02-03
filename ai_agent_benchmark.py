from openai import OpenAI
import pandas as pd
import random
import numpy as np
from dotenv import load_dotenv
import os

# --------------------------------------------------------------------------------
# 1. SYNTHETIC DATA GENERATION
# --------------------------------------------------------------------------------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_synthetic_crm_data(num_employees=5, seed=42):
    """
    Generates a synthetic CRM dataset with clear, unambiguous patterns.
    Returns a pandas DataFrame.
    """
    random.seed(seed)
    np.random.seed(seed)
    
    employees = [
        "Alice", "Bob", "Charlie", "Diana", "Ethan", 
        "Fiona", "George", "Hannah", "Irene", "Jack"
    ]
    
    # Just pick a subset of employees for this run
    selected_employees = random.sample(employees, num_employees)
    
    # For demonstration, we create a few columns:
    # - employee_name
    # - total_deals (clear top performer pattern: one employee has significantly higher deals)
    # - total_revenue (similar pattern)
    # - conversion_rate (one distinct top performer here)
    # - average_sale_cycle_days (one distinct minimal cycle here)
    #
    # We'll impose patterns:
    #   * The first employee in the sorted selection will have the highest deals & revenue
    #   * The second employee will have the best conversion rate
    #   * The third will have the fastest sales cycle
    #   * The rest will have intermediate values
    
    # random baseline values
    base_deals = np.random.randint(10, 40, size=num_employees)
    base_revenue = np.random.randint(10000, 90000, size=num_employees)
    base_conversion = np.random.uniform(0.10, 0.40, size=num_employees)
    base_cycle = np.random.randint(20, 50, size=num_employees)
    
    # Sort for reproducibility and “assign” patterns to positions 0/1/2
    # (So that the same employees always get the pattern.)
    selected_employees.sort()  # sorting by name for consistency
    
    # Force unambiguous patterns:
    # Top deals & revenue
    base_deals[0] = max(base_deals) + 20     # clearly highest
    base_revenue[0] = max(base_revenue) + 30000  # clearly highest
    
    # Best conversion
    base_conversion[1] = max(base_conversion) + 0.10
    
    # Fastest cycle
    base_cycle[2] = min(base_cycle) - 10
    if base_cycle[2] < 1:
        base_cycle[2] = 1  # to avoid zero or negative
    
    data = {
        "employee_name": selected_employees,
        "total_deals": base_deals,
        "total_revenue": base_revenue,
        "conversion_rate": base_conversion,
        "average_sale_cycle_days": base_cycle
    }
    
    df = pd.DataFrame(data)
    return df


# --------------------------------------------------------------------------------
# 2. EXPECTED CONCLUSIONS
# --------------------------------------------------------------------------------
def get_expected_conclusions(df):
    """
    Return a dictionary of the unambiguous conclusions we expect the AI to draw.
    
    For simplicity, we craft a textual (natural language) description of 
    the main patterns in the dataset that any AI agent should ideally detect.
    """
    # Sort the DF to identify the actual "top" employees for each metric
    deals_top = df.loc[df['total_deals'].idxmax(), 'employee_name']
    revenue_top = df.loc[df['total_revenue'].idxmax(), 'employee_name']
    conversion_top = df.loc[df['conversion_rate'].idxmax(), 'employee_name']
    fastest_cycle = df.loc[df['average_sale_cycle_days'].idxmin(), 'employee_name']
    
    # We can combine them in a single textual statement or keep them separate
    expected = {
        "deals_conclusion": f"The employee with the highest total deals is {deals_top}.",
        "revenue_conclusion": f"The employee with the highest total revenue is {revenue_top}.",
        "conversion_conclusion": f"The employee with the best (highest) conversion rate is {conversion_top}.",
        "cycle_conclusion": f"The employee with the fastest (lowest) average sale cycle is {fastest_cycle}."
    }
    return expected


# --------------------------------------------------------------------------------
# 3. MOCK AI AGENT RESPONSES
# --------------------------------------------------------------------------------
def get_mock_agent_responses():
    """
    Here we simulate raw textual answers from different AI agents,
    which we'll evaluate against the expected conclusions.
    
    In a real setup, these would come from different AI systems or
    from multiple runs of the same system with variations.
    """
    mock_responses = {
        # Let's provide a "perfect" response
        "agent_perfect": (
            "Alice has the highest number of deals and also leads "
            "in total revenue. Bob has the best conversion rate. "
            "Charlie has the fastest sales cycle."
        ),
        # Let's provide an "incorrect" response to show scoring differences
        "agent_incorrect": (
            "Diana is the top performer in terms of deals, while Bob "
            "leads in total revenue. Charlie has the best conversion rate, "
            "and Alice has the shortest cycle."
        )
    }
    return mock_responses


# --------------------------------------------------------------------------------
# 4. SCORING FUNCTION USING OPENAI
# --------------------------------------------------------------------------------
# NOTE: You must set your openai.api_key before calling these functions.

def score_agent_response(agent_response, expected_conclusions, model="gpt-4o"):
    """
    Evaluate how well the agent_response text matches the expected conclusions
    for both:
      - keyword & semantic similarity
      - numerical correctness (in a simple, partial manner)
      
    This uses the OpenAI API for semantic similarity checks on a per-conclusion basis.
    
    Returns an overall score or a breakdown.
    """
    
    # Quick way: for each conclusion, we ask the model to check 
    # if the agent_response text is consistent with the statement.
    # Another approach is embeddings-based similarity, etc.
    
    # We'll do a simple approach: for each expected statement, we create a short system/prompt:
    # "Is the following statement supported by the agent's text? Return yes or no."
    
    # Then we parse the answer and compute a score. 
    # This is a naive example, and can be improved with more robust prompt engineering.
    
    scores = {}
    
    for key, statement in expected_conclusions.items():
        prompt = (
            f"System:\n"
            f"You are a strict evaluator. We have an expected conclusion:\n"
            f"'{statement}'\n"
            f"Determine if the agent's response below supports this conclusion.\n"
            f"Answer ONLY with 'yes' or 'no'.\n\n"
            f"Agent's response:\n"
            f"{agent_response}"
        )
        
        # Make an OpenAI call in chat completion style:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": prompt}],
                temperature=0
            )
            reply = response.choices[0].message.content.lower().strip()
            # We interpret 'yes' or 'no'
            if reply.startswith("yes"):
                scores[key] = 1
            else:
                scores[key] = 0
        except Exception as e:
            # If there's an error with the API call, handle gracefully
            print(f"OpenAI API error: {e}")
            scores[key] = 0
    
    # Overall score: sum / # of conclusions
    overall_score = sum(scores.values()) / len(scores)
    return overall_score, scores


# --------------------------------------------------------------------------------
# MAIN EXECUTION: EXAMPLE WORKFLOW
# --------------------------------------------------------------------------------
if __name__ == "__main__":
    # 1. Generate data
    df = generate_synthetic_crm_data(num_employees=5, seed=42)
    print("Synthetic CRM Data:\n", df, "\n")
    
    # 2. Gather expected conclusions
    expected = get_expected_conclusions(df)
    print("Expected Conclusions:\n", expected, "\n")
    
    # 3. Mock AI responses
    mock_responses = get_mock_agent_responses()
    
    # 4. Evaluate each agent response
    # (In a real scenario, set openai.api_key = "YOUR_API_KEY" before calling)
    
    # Example – obviously, if you have not set up your API key and usage, 
    # these calls will fail or you'll have to mock them. 
    
    for agent_name, text_response in mock_responses.items():
        print(f"Evaluating response from {agent_name}:")
        #Score the agent’s answer
        overall_score, per_conclusion_score = score_agent_response(
            text_response,
            expected,
            model="gpt-4o"
        )
        print("Overall Score:", overall_score)
        print("Detailed Scores:", per_conclusion_score)
        
        # For demonstration, we'll just print the response:
        #print("Agent Response:", text_response, "\n")