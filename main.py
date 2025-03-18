# main.py
import logging
import os
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
from crm_benchmark_lib.test import run_tests_on_all_csvs
import requests
from website.app import app
api_endpoint = "http://127.0.0.1:5000/submit_agent_score_api"
# Example: configure root logger with DEBUG level
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

logging.basicConfig(level=logging.DEBUG)

def my_agent_callable(question_text: str, df: pd.DataFrame) -> str:
    resp = client.chat.completions.create(
        model="o3-mini",
        messages=[
            {"role": "system", "content": "You are an agent designed to analyze CRM data."},
            {"role": "system", "content": df.to_string()},
            {"role": "user", "content": question_text},
        ]
    )
    return resp.choices[0].message.content

if __name__ == "__main__":
    score = run_tests_on_all_csvs(my_agent_callable)
    app.run(debug=True)
    payload = {
    "api_key": "mmeyer",
    "agent_name": "MyCRMAgent",
    "score": score}
    response = requests.post(api_endpoint, data=payload)
    print(response.json())
    
