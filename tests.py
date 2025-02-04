import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def test_top_deals(deals_df):
    """
    Return an expected conclusion about who has the highest deals.
    """
    deals_top = deals_df.loc[deals_df['total_deals'].idxmax(), 'employee_name']
    return f"The employee with the highest total deals is {deals_top}."

def test_top_revenue(deals_df):
    """
    Return an expected conclusion about who has the highest revenue.
    """
    revenue_top = deals_df.loc[deals_df['total_revenue'].idxmax(), 'employee_name']
    return f"The employee with the highest total revenue is {revenue_top}."

def test_top_conversion(deals_df):
    """
    Return an expected conclusion about who has the best (highest) conversion rate.
    """
    conversion_top = deals_df.loc[deals_df['conversion_rate'].idxmax(), 'employee_name']
    return f"The employee with the best (highest) conversion rate is {conversion_top}."

def test_fastest_cycle(deals_df):
    """
    Return an expected conclusion about who has the fastest (lowest) average sale cycle.
    """
    fastest_cycle = deals_df.loc[deals_df['average_sale_cycle_days'].idxmin(), 'employee_name']
    return f"The employee with the fastest (lowest) average sale cycle is {fastest_cycle}."

def test_region_mention(employees_df):
    """
    Example: check which region has the most employees, just to create a conclusion.
    """
    region_counts = employees_df['region'].value_counts()
    top_region = region_counts.idxmax()
    count = region_counts.max()
    return f"The region with the most employees is {top_region} with {count} employee(s)."

def compile_expected_conclusions(employees_df, deals_df):
    """
    Gathers all test conclusions into a dictionary for easy evaluation.
    """
    conclusions = {}
    conclusions["top_deals"] = test_top_deals(deals_df)
    conclusions["top_revenue"] = test_top_revenue(deals_df)
    conclusions["top_conversion"] = test_top_conversion(deals_df)
    conclusions["fastest_cycle"] = test_fastest_cycle(deals_df)
    conclusions["top_region"] = test_region_mention(employees_df)
    return conclusions


def score_agent_response_extended(agent_response, expected_statement, model="gpt-4o"):
    """
    Classify the agent's response into one of the following categories:
      - correct: if it fully aligns with the expected statement
      - opposite: if it contradicts the statement
      - unrelated: if it does not address the statement at all
      - partially correct: if it addresses the statement but is only partially aligned

    We then map those categories to numeric scores, for instance:
      correct = 1.0
      partially correct = 0.5
      opposite = 0.0
      unrelated = 0.0

    Return both the string category and the numeric score.
    """

    # We'll do a short system prompt that instructs GPT to categorize.
    # NOTE: We do not alter the "client" usage or object. We keep the same pattern.
    prompt = (
        f"System:\n"
        f"You are a strict evaluator of CRM insights.\n"
        f"Expected conclusion:\n{expected_statement}\n\n"
        f"Agent's response:\n{agent_response}\n\n"
        f"Classify the agent's response into exactly one of these categories:\n"
        f"- correct\n"
        f"- opposite\n"
        f"- unrelated\n"
        f"- partially correct\n\n"
        f"Output ONLY the single category name."
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": prompt}],
            temperature=0
        )
        category = response.choices[0].message.content.lower().strip()
    except Exception as e:
        print(f"OpenAI API error: {e}")
        # If there's an error, default to 'unrelated'
        category = "unrelated"

    # Map to numeric
    if category.startswith("correct"):
        score = 1.0
    elif category.startswith("partially"):
        score = 0.5
    elif category.startswith("opposite"):
        score = 0.0
    else:
        # Treat all else as 'unrelated'
        score = 0.0
        category = "unrelated"

    return category, score