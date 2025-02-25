import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from http import client as http_client

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Adjust as needed if you add or rename categories
CATEGORY_SECTION_WEIGHTS = {
    "pipeline_insights": 0.75,
    "email_analysis": 0.75,
    "general_sales_knowledge": 0.50,
    "employee_performance": 0.25
}

def load_dataset_json(json_path):
    """
    Loads a dataset JSON file that contains either:
      - A dict with keys "dataset_description", "crm_data", "questions"
      OR
      - A list of question objects (like the original questions.json).
    Returns the entire JSON.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def evaluate_response_with_variants(agent_response, correct_answer_data, model="gpt-4"):
    """
    Uses the OpenAI API to evaluate an agent's response compared to the correct answer,
    acceptable variants, and wrong variants.

    Returns:
        (score, raw_output): score is a float [0.0, 1.0]
    """
    main_answer = correct_answer_data["main_answer"]
    acceptable = correct_answer_data.get("acceptable_variants", [])
    wrong = correct_answer_data.get("wrong_variants", [])

    prompt = (
        "You are a strict evaluator of CRM insights. Evaluate the following agent's response "
        "against the correct answer criteria.\n\n"
        f"MAIN correct statement:\n{main_answer}\n\n"
        f"ACCEPTABLE variants:\n{'; '.join(acceptable)}\n\n"
        f"WRONG variants:\n{'; '.join(wrong)}\n\n"
        "Agent's response:\n"
        f"{agent_response}\n\n"
        "Please provide a single numeric rating from 0.000 to 1.000 (with exactly three decimals), "
        "where 1.000 means perfect alignment and 0.000 means complete mismatch. Output ONLY the numeric rating."
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": prompt}],
        )
        rating_str = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return 0.0, "Error in API call"

    try:
        raw_score = float(rating_str)
        raw_score = max(0.0, min(raw_score, 1.0))
        raw_score = round(raw_score, 3)
        return raw_score, rating_str
    except ValueError:
        # If GPT returns something not parseable as float
        return 0.0, rating_str

def compute_weighted_score(question_results):
    """
    Computes a weighted overall score (as a percentage) from individual question scores.
    Weighted by the category weights in CATEGORY_SECTION_WEIGHTS.
    """
    total_weight = 0.0
    weighted_sum = 0.0

    for result in question_results:
        category = result["category"]
        weight = CATEGORY_SECTION_WEIGHTS.get(category, 0)
        weighted_sum += result["score"] * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0

    final_fraction = weighted_sum / total_weight
    return round(final_fraction * 100, 2)

def run_benchmark(agent_responses, dataset_json_path, model="gpt-4"):
    """
    Runs the benchmark by evaluating multiple agent responses against
    the question set from a single dataset JSON.
    Supports both JSON files that are lists of questions and those wrapped in a dict.
    """
    dataset = load_dataset_json(dataset_json_path)
    
    if isinstance(dataset, list):
        # File is a list of question objects (e.g., original questions.json)
        questions = dataset
        dataset_description = ""
    else:
        questions = dataset.get("questions", [])
        dataset_description = dataset.get("dataset_description", "")
    
    results = {}

    for agent_name, text_response in agent_responses.items():
        question_results = []
        for q in questions:
            score, raw_output = evaluate_response_with_variants(
                agent_response=text_response,
                correct_answer_data=q["correct_answer"],
                model=model
            )
            question_results.append({
                "question_id": q["question_id"],
                "category": q["category"],
                "question_text": q["question_text"],
                "score": score,
                "model_raw_output": raw_output
            })

        weighted_score = compute_weighted_score(question_results)
        results[agent_name] = {
            "dataset_description": dataset_description,
            "weighted_score_percentage": weighted_score,
            "details": question_results
        }

    return results

if __name__ == "__main__":
    # Example usage with dummy agent responses
    # You can test with real or mock responses that attempt to answer the dataset questions.
    dummy_agent_responses = {
        "AgentA": "Dummy response that might be partially correct.",
        "AgentB": "Another dummy answer with different details."
    }

    # Evaluate a single dataset (e.g., Dataset 1)
    ds1_results = run_benchmark(
        agent_responses=dummy_agent_responses,
        dataset_json_path="dataset_1_questions.json",
        model="o1"  # Replace with your model, e.g., "gpt-4"
    )
    print("Results on Dataset 1:")
    print(json.dumps(ds1_results, indent=2))

    # Optionally, loop through multiple dataset files:
    dataset_files = [
        "dataset_1_questions.json",
        "dataset_2_questions.json",
        "dataset_3_questions.json",
        "dataset_4_questions.json",
        "dataset_5_questions.json"
    ]

    for ds_file in dataset_files:
        print(f"\nEvaluating {ds_file}...")
        results = run_benchmark(
            agent_responses=dummy_agent_responses,
            dataset_json_path=ds_file,
            model="o1"
        )
        print(json.dumps(results, indent=2))
