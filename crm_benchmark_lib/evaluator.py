# evaluator.py

"""
Contains logic to load the question set JSON, evaluate the agent's responses
against correct/acceptable/wrong variants, and compute final scores.

This revised version uses an OpenAI LLM (o3-mini) to provide a numeric score,
and logs intermediate steps for debugging.
"""

import json
import os
from openai import OpenAI
import logging
from .config import CATEGORY_SECTION_WEIGHTS
from dotenv import load_dotenv

load_dotenv()

# ------------------------------------------------------------------------
# Configure Logging
# ------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.CRITICAL)

# If you don't already have a root logger configured, you can use:
# logging.basicConfig(level=logging.DEBUG)
# or create a handler. For brevity, we'll trust an external config or basicConfig.

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_questions(json_path):
    logger.debug(f"Loading questions from: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def evaluate_response_with_variants(
    agent_response: str,
    correct_answer_data: dict,
    csv_data: str = ""
):
    """
    Evaluate an agent's response by passing the agent response, plus info about
    what is considered correct, acceptable, or wrong, to an OpenAI model (o3-mini).

    We ask the model to provide a single float between 0.0 and 1.0 (two decimals).
    If it fails to parse, we default to 0.0.

    Returns: (score: float, debug_info: str)
    """
    main_answer = correct_answer_data["main_answer"]
    acceptable = correct_answer_data.get("acceptable_variants", [])
    wrong = correct_answer_data.get("wrong_variants", [])

    # We pass the CSV data as well, in case the LLM wants additional context.
    # If the CSV is large, you may consider summarizing or chunking.

    prompt = f"""
You are an AI-based evaluator. You must read the following question's "correct" info,
the agent's response, and any relevant CSV data, then decide on a single numeric score
between 0.00 and 1.00 (inclusive). Output ONLY that float with two decimals, nothing else.

Scoring Guidelines:
- 1.00 means the agent's answer is fully correct (or acceptable).
- 0.00 means the agent is completely incorrect or contradicts known facts.
- A value between 0.00 and 1.00 is allowed if partially correct.

Question's Correct/Acceptable/Wrong Data:
- MAIN correct statement: {main_answer}
- ACCEPTABLE variants: {acceptable}
- WRONG variants: {wrong}

Agent's Response:
{agent_response}

CSV Data (for context):
{csv_data}

Return only the numeric score in the format: XX.XX (two decimals, e.g., 0.75).
"""

    logger.debug("=== EVALUATION PROMPT ===\n%s", prompt.strip())

    try:
        response = client.chat.completions.create(
            model="o3-mini",
            messages=[
                {"role": "system", "content": "You are a strict evaluator."},
                {"role": "user", "content": prompt.strip()},
            ]
        )
        content = response.choices[0].message.content.strip()
        logger.debug("LLM Raw Output: %r", content)
    except Exception as e:
        logger.error("OpenAI API error: %s", e, exc_info=True)
        return (0.0, f"OpenAI API error: {str(e)}")

    # Attempt to parse float
    try:
        score = float(content)
        # Clip between 0 and 1
        score = max(0.0, min(score, 1.0))
        # Round to two decimals
        score = round(score, 2)
        logger.debug("Parsed score: %s", score)
        return (score, f"LLM scored => {score}")
    except ValueError:
        logger.warning("Failed to parse float from LLM response: %r", content)
        return (0.0, f"Failed to parse float from: {content}")

def compute_weighted_score(question_results):
    """
    Weighted overall score (as a percentage) from individual question scores,
    using the category weights in config.
    """
    total_weight = 0.0
    weighted_sum = 0.0

    for result in question_results:
        category = result["category"]
        score = result["score"]
        weight = CATEGORY_SECTION_WEIGHTS.get(category, 0)
        weighted_sum += score * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0

    final_fraction = weighted_sum / total_weight
    final_percent = round(final_fraction * 100, 2)
    logger.debug("Computed Weighted Score (%%): %s", final_percent)
    return final_percent
