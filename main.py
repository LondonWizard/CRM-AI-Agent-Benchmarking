# main.py
import os
from dotenv import load_dotenv
from tests import run_benchmark

load_dotenv()

if __name__ == "__main__":
    # Two mock "agents" with aggregated answers
    agent_responses = {
        "agent_perfect": (
            "Margaret Carter has the highest total closed-won opportunity amount. "
            "John Roberts has the best conversion rate. "
            "Michael Brown has the fastest average close time. "
            "Rachel Adams has the most email activity. "
            "James Wilson is inactive in the system. "
            "Patricia Nguyen is in the Marketing department. "
            "I would praise John Roberts for his strong conversion ratio and recommend sharing tips. "
            "Regarding the 'Discussion about Enterprise Deal A' email, Margaret is awaiting questions; I'd follow up promptly. "
            "To improve closed-won deals, let's hire more Sales Reps, replicate Margaret's best practices, and do negotiation training. "
            "Looking at Q1 Upsell for John Roberts, he closed a 50k upsell fast, showing strong upsell skills."
        ),
        "agent_incorrect": (
            "John Roberts is top for closed-won. "
            "Margaret Carter has the best conversion rate. "
            "Susan Davis closes deals the fastest. "
            "Kevin Lee has the most email activity. "
            "Rachel Adams is inactive. "
            "James Wilson is in Marketing. "
            "We should fire John for poor performance. "
            "The 'Discussion about Enterprise Deal A' email indicates the deal won't proceed. "
            "To improve deals, I'd remove training budget. "
            "Q1 Upsell was lost at 15,000 so it's a failure."
        )
    }

    results = run_benchmark(agent_responses, questions_json="questions.json", model="gpt-4o")

    print("\n=== Benchmark Results ===")
    for agent_name, info in results.items():
        print(f"\nAgent: {agent_name}")
        print(f"Weighted Score: {info['weighted_score']:.3f}")
        for qdetail in info["details"]:
            print(f"  - Q{qdetail['question_id']} ({qdetail['category']}) => Score: {qdetail['score']:.3f}")
            print(f"    Model raw output: {qdetail['model_raw_output']}")
