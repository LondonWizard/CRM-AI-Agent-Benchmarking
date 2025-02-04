import os
import pandas as pd
from dotenv import load_dotenv

from openai import OpenAI
# We keep the same usage of OpenAI client as before
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

from tests import compile_expected_conclusions, score_agent_response_extended

def run_benchmark(agent_responses, model="gpt-4o"):
    """
    Runs the benchmarking on a set of agent responses, 
    using the expected conclusions from the CRM data.
    """
    # Load the synthetic CSV data
    employees_df = pd.read_csv("employees.csv")
    deals_df = pd.read_csv("deals.csv")
    emails_df = pd.read_csv("emails.csv")  # Not used in tests, but available

    # Generate the expected conclusions from the tests
    expected_conclusions = compile_expected_conclusions(employees_df, deals_df)

    print("=== Expected Conclusions ===")
    for key, val in expected_conclusions.items():
        print(f"{key}: {val}")
    print("")

    # Evaluate each agent response
    results = {}
    for agent_name, text_response in agent_responses.items():
        print(f"Evaluating response from {agent_name}:\nAgent says:\n{text_response}\n")
        overall_score = 0
        details = []

        for conclusion_key, statement in expected_conclusions.items():
            category, score = score_agent_response_extended(
                text_response, statement, model=model
            )
            overall_score += score
            details.append((conclusion_key, statement, category, score))

        # Average across the number of tests
        final_score = overall_score / len(expected_conclusions) if expected_conclusions else 0
        results[agent_name] = {
            "final_score": final_score,
            "details": details
        }

    return results


if __name__ == "__main__":
    # Example usage with mock agent responses
    agent_responses = {
        "agent_perfect": (
            "Alice has the highest number of deals and total revenue. "
            "Bob has the best conversion rate, and Charlie has the fastest cycle. "
            "The region with the most employees is East."
        ),
        "agent_incorrect": (
            "I think Diana is the top for deals, Fiona leads revenue, "
            "Bob has the best conversion, and Irene is the fastest. "
            "It doesn't matter which region is largest."
        ),
        "agent_opposite_example": (
            "Alice definitely does NOT have the highest deals or revenue, "
            "Charlie has the worst conversion, etc."
        ),
        "agent_unrelated_example": (
            "I want to talk about the weather and completely ignore the CRM data!"
        ),
    }

    # Run the benchmark
    results = run_benchmark(agent_responses, model="gpt-4o")

    # Print summarized results
    print("\n=== Benchmark Results ===")
    for agent_name, info in results.items():
        print(f"\nAgent: {agent_name}")
        print(f"Final Score: {info['final_score']:.2f}")
        print("Details (test_key, expected, category, score):")
        for row in info["details"]:
            print(f"  - {row}")