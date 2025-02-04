import json
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Example weighting scheme (adjust these percentages as needed):
CATEGORY_WEIGHTS = {
    "employee_performance": 0.35,
    "feedback_to_employees": 0.15,
    "email_analysis": 0.15,
    "improvement_recs": 0.15,
    "deal_insights": 0.20
}

def load_questions_from_json(json_path="questions.json"):
    """
    Reads a JSON file containing questions and their correct answer structures.
    Returns a list of dicts.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def evaluate_response_with_variants(agent_response, correct_answer_data, model="gpt-4o"):
    """
    We pass the main_answer, acceptable_variants, and wrong_variants to GPT.
    The system prompt instructs GPT to produce a single numeric rating from 0.000 to 1.000
    (with exactly three decimals) that reflects how correct the agent's response is.

    Returns: (score_from_model, raw_str_or_error)
        Where score_from_model is a float in [0.0 ... 1.0], truncated/rounded to 3 decimals.
        raw_str_or_error is the text for debugging or fallback.
    """
    main_answer = correct_answer_data["main_answer"]
    acceptable = correct_answer_data.get("acceptable_variants", [])
    wrong = correct_answer_data.get("wrong_variants", [])

    prompt = (
        "System:\n"
        "You are a strict evaluator of CRM insights. We have:\n\n"
        f"MAIN correct statement:\n{main_answer}\n\n"
        f"ACCEPTABLE variants:\n{'; '.join(acceptable)}\n\n"
        f"WRONG variants:\n{'; '.join(wrong)}\n\n"
        "Agent's response:\n"
        f"{agent_response}\n\n"
        "Please provide a single numeric rating from 0.000 to 1.000 (with exactly three decimals),\n"
        "where:\n"
        "  1.000 = the agent's response perfectly aligns with the main/acceptable statements without contradiction.\n"
        "  0.000 = the agent's response directly contradicts the correct statements or is entirely unrelated.\n"
        "Values in between represent partial correctness (e.g., 0.500 if partially correct, etc.).\n"
        "Output ONLY the numeric rating with three decimals (e.g., 0.750)."
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": prompt}],
            temperature=0
        )
        rating_str = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return 0.0, "Error in API call"

    # Attempt to parse rating_str as float
    # Must be in [0.0, 1.0], with up to 3 decimals
    try:
        raw_score = float(rating_str)
        # clamp to [0.0, 1.0] just in case
        if raw_score < 0:
            raw_score = 0.0
        elif raw_score > 1:
            raw_score = 1.0
        # round to 3 decimals
        raw_score = round(raw_score, 3)
        return raw_score, rating_str
    except ValueError:
        # If the model fails to produce a parseable float, default to 0
        return 0.0, rating_str

def compute_weighted_score(results):
    """
    Given a list of question results, each with (category, score),
    compute a weighted final. For each category, we average the scores
    of questions in that category, then multiply by the category weight,
    then sum across categories.
    """
    category_scores = {}
    category_counts = {}

    for r in results:
        cat = r["category"]
        sc = r["score"]
        if cat not in category_scores:
            category_scores[cat] = 0
            category_counts[cat] = 0
        category_scores[cat] += sc
        category_counts[cat] += 1

    final_weighted = 0.0
    for cat, total_score in category_scores.items():
        avg_score_cat = total_score / category_counts[cat] if category_counts[cat] else 0
        weight = CATEGORY_WEIGHTS.get(cat, 0)  # default 0 if not found
        final_weighted += avg_score_cat * weight

    return round(final_weighted, 3)

def run_benchmark(agent_responses, questions_json="questions.json", model="gpt-4o"):
    questions = load_questions_from_json(questions_json)
    results = {}

    for agent_name, text_response in agent_responses.items():
        question_results = []
        for q in questions:
            raw_score, rating_str = evaluate_response_with_variants(
                agent_response=text_response,
                correct_answer_data=q["correct_answer"],
                model=model
            )
            question_results.append({
                "question_id": q["question_id"],
                "category": q["category"],
                "question_text": q["question_text"],
                "score": raw_score,
                "model_raw_output": rating_str  # store exactly what the model returned (for debugging)
            })

        final_weighted = compute_weighted_score(question_results)
        results[agent_name] = {
            "weighted_score": final_weighted,
            "details": question_results
        }

    return results
