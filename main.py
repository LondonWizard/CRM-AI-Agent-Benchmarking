# main.py
import os
from dotenv import load_dotenv
from tests import run_benchmark

load_dotenv()

if __name__ == "__main__":
    # Two mock "agents" with aggregated answers:
    #  - agent_perfect: Correct for all 10 questions in questions.json.
    #  - agent_incorrect: Wrong for all 10 questions in questions.json.

    agent_responses = {
        "agent_perfect": (
            # This is a unified text that correctly answers each question
            # from questions.json (the original 10 questions set).
            "Looking at the dataset, there are three opportunities in the Qualification stage: "
            "Stafford Ltd, King, Tucker and Rowe, and Cunningham-Hendricks. "

            "The sales rep who manages only one opportunity are EMPed896d30 (Clark, Erickson and Sullivan) "
            "and EMP5a65638f (Cunningham-Hendricks); each handles only one. "

            "The opportunity with the earliest close date is Clark, Erickson and Sullivan with a close date of 2023-12-10. "

            "For the email communications of Mccall, Jackson and Carey, Xavier Ortiz requested "
            "further clarification on the integration timeline and associated costs. "

            "All opportunities in the Proposal stage add up to 126,412.61 (Mccall, Jackson and Carey) plus 67,825.64 (Hunter Group) "
            "for a total of 194,238.25. "

            "The typical duration between close date and renewal date for most opportunities is 1 year. "

            "In the sales process depicted, the Proposal stage typically follows the Qualification stage. "

            "Sales rep EMP5a65638f manages the Cunningham-Hendricks opportunity, which is in the Qualification stage. "

            "The Hunter Group email thread focused on the implementation timeline, scalability, and customization. "
            "Jennifer Murphy committed to sending the final documentation on customization options. "

            "Finally, the Cunningham-Hendricks opportunity has the highest potential revenue at 146,114.39 "
            "and is in the Qualification stage."
        ),
        "agent_incorrect": (
            # This text contradicts every question’s correct answer.
            "Actually, there are only two opportunities in Qualification: Stafford Ltd and King, Tucker and Rowe. "

            "The only sales rep with one deal is EMP76730cb2 managing Stafford Ltd. "

            "The earliest close date is for Hunter Group on 2023-12-17. "

            "Xavier Ortiz asked only about scalability features, not integration timeline or costs. "

            "For the Proposal stage, the total potential amount is around 150,000. "

            "Also, the gap between close and renewal dates is 2 years, not 1 year. "

            "After Qualification, Negotiation follows—definitely not Proposal. "

            "And EMP5a65638f actually manages King, Tucker and Rowe in the Proposal stage, not Cunningham-Hendricks. "

            "The Hunter Group emails were solely about pricing. "

            "Finally, the highest potential revenue is for Hunter Group at 200,000 in Proposal."
        )
    }
    
    # Run the benchmark with the updated logic from tests.py, using the older questions.json (10 questions).
    # The 'model="o1"' is just a placeholder referencing your snippet;
    # replace with your actual model if needed (e.g., "gpt-4" or "gpt-3.5-turbo").
    results = run_benchmark(agent_responses, dataset_json_path="questions.json", model="o3-mini")
    
    print("\n=== Benchmark Results ===")
    for agent_name, info in results.items():
        print(f"\nAgent: {agent_name}")
        print(f"Weighted Score Percentage: {info['weighted_score_percentage']}%")
        
        for qdetail in info["details"]:
            print(f"  - {qdetail['question_id']} ({qdetail['category']}) => Score: {qdetail['score']:.3f}")
            print(f"    Model raw output: {qdetail['model_raw_output']}")
