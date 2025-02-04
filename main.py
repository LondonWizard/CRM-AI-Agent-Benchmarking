# main.py
import os
from dotenv import load_dotenv
from tests import run_benchmark

load_dotenv()

if __name__ == "__main__":
    # Two mock "agents" with aggregated answers
    agent_responses = {
    "agent_perfect": (
        "The largest Qualification deal is OPPae1eb29a-60e0-4a5e-b1dd-e5cbafe5797e for Cunningham-Hendricks. "
        "Clark, Erickson and Sullivan (OPP5f29e438-1160-4dbb-8d93-c7121ddf71ed) is assigned to EMPed896d30. "
        "Hunter Group (OPP71ce8161-7802-4aff-94a8-e69f06058551) is in the Proposal stage with a 2023 close date. "
        "The negotiation for Clark, Erickson and Sullivan references final scalability and support terms. "
        "Mccall, Jackson and Carey’s proposal is the highest-value in that stage, at 126,412.61. "
        "Stafford Ltd and Cunningham-Hendricks are the two companies in Qualification. "
        "Qualification is where you gather initial requirements and assess fit. "
        "EMPa9a28170 handles King, Tucker and Rowe (Qualification) and Hunter Group (Proposal). "
        "Cunningham-Hendricks specifically asked about integration capabilities. "
        "Mccall, Jackson and Carey (OPP02519fbe-e3da-4d20-849d-cb75e0c01b3a) is in Proposal and assigned to EMP76730cb2."
    ),
    "agent_incorrect": (
        "Stafford Ltd is the biggest deal in Proposal. "
        "EMPed896d30 actually works with Hunter Group. "
        "The client with a 2023 close date in Proposal is Clark, Erickson and Sullivan. "
        "King, Tucker and Rowe is in Negotiation talking about support. "
        "Hunter Group has the highest proposal at 200,000. "
        "Every company is in the Qualification stage. "
        "Negotiation is the stage for initial requirement gathering. "
        "EMPa9a28170 does not handle any deals in Qualification. "
        "Cunningham-Hendricks asked for budget approvals, not integration. "
        "Stafford Ltd is assigned to EMP76730cb2 and is in the Proposal stage."
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
