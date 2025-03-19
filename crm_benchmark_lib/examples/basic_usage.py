"""
Basic example of using the CRM Benchmark library.

This example shows how to create a simple agent and run it against the benchmark.
"""

import sys
import os
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

# Get the absolute path to the crm_benchmark_lib directory
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LIB_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add the repository root to Python path
sys.path.append(REPO_ROOT)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Import the library
from crm_benchmark_lib import BenchmarkClient

# Define a sample agent function
def my_agent_4o_mini(question: str, data: pd.DataFrame) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an AI Agent that specializes in CRM and Sales. You will be given a question and a dataframe. You will need to answer the question based on the data. Return only the answer, no other text."},
            {"role": "user", "content": f"Question: {question}\n\nData: {data.to_string()}"}
        ]
    )
    return response.choices[0].message.content.strip()

def my_agent_4o(question: str, data: pd.DataFrame) -> str:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an AI Agent that specializes in CRM and Sales. You will be given a question and a dataframe. You will need to answer the question based on the data. Return only the answer, no other text."},
            {"role": "user", "content": f"Question: {question}\n\nData: {data.to_string()}"}
        ]
    )
    return response.choices[0].message.content.strip()

def my_agent_o3_mini(question: str, data: pd.DataFrame) -> str:
    response = client.chat.completions.create(
        model="o3-mini",
        messages=[
            {"role": "system", "content": "You are an AI Agent that specializes in CRM and Sales. You will be given a question and a dataframe. You will need to answer the question based on the data. Return only the answer, no other text."},
            {"role": "user", "content": f"Question: {question}\n\nData: {data.to_string()}"}
        ]
    )
    return response.choices[0].message.content.strip()

def my_agent_o1(question: str, data: pd.DataFrame) -> str:
    response = client.chat.completions.create(
        model="o1",
        messages=[
            {"role": "system", "content": "You are an AI Agent that specializes in CRM and Sales. You will be given a question and a dataframe. You will need to answer the question based on the data. Return only the answer, no other text."},
            {"role": "user", "content": f"Question: {question}\n\nData: {data.to_string()}"}
        ]
    )
    return response.choices[0].message.content.strip()

def maxs_custom_agent(question: str, data: pd.DataFrame) -> str:
    response = client.chat.completions.create(
        model="o1",
        messages=[
            {"role" : "user", "content" : """Here are some instructions on how to answer incoming questions:
             Below is a consolidated set of best practices and general guidelines an AI agent can follow to respond effectively to a wide range of CRM-related questions—without citing any specific answer text, numeric values, or other data from a particular dataset. These guidelines focus on method, clarity, and consistency rather than referencing any single “correct” answer.

---

## 1. Determine the Question’s Category

Within CRM contexts, questions often fall into one of several categories. Before answering, identify which one the question belongs to. Common categories include:

- **Pipeline Insights** – Questions about deal stages, lead sources, largest deals, missing data, or duplicate records.
- **Email Analysis** – Questions analyzing email threads for sentiment, objections, or summarizing next steps.
- **General Sales Knowledge** – Questions about updating opportunity stages, calculating forecasts, identifying at-risk deals, ranking leads, drafting follow-up emails, or referencing sales best practices.
- **Employee Performance** – Questions about trends in sales performance, top performers, pipeline drop-off points, and strategic recommendations.

Knowing the category ensures the answer has the right level of detail and context.

---

## 2. Maintain Data Consistency and Accuracy

1. **Match Stated Details**: If a question references a specific metric (e.g., number of deals in a stage, conversion rates, or employee performance percentages), ensure that the response uses the same referenced details. Do not modify or replace them with different values.

2. **Preserve Unique Identifiers**: If the question mentions certain employee or opportunity IDs, keep them consistent. Maintain spelled-out names or short forms (e.g., “Global Industries” vs. “Global Ind.”) exactly as referenced.

3. **Avoid Contradiction**: Never state a piece of information in direct conflict with the question’s premise. For instance, if the question asserts there are missing data fields, do not claim there are none.

---

## 3. Acknowledge the Question’s Intent

Each question typically aims to accomplish a specific goal:

- **Quantify** (e.g., total number of deals or revenue).  
- **Identify** (e.g., largest deal, duplicate records, at-risk opportunities).  
- **Summarize** (e.g., summarize an email thread or meeting transcript).  
- **Recommend** (e.g., propose next steps, highlight strategic improvements).  
- **Assess** (e.g., compare performance metrics, categorize a deal stage).  

Always shape your response to fulfill the question’s intent. If the question wants a recommendation, do not simply provide raw data—give a clear “what to do next.”

---

## 4. Offer Clear, Concise Responses

1. **Stay on Topic**: Focus on the question without adding irrelevant information or speculation.  
2. **Use Direct Language**: Phrases like “Based on the data, we see…” or “The next step should be…” help keep the answer structured.  
3. **Keep It Brief**: If the question is straightforward, provide a succinct reply. If it requires detail (e.g., summarizing an email or meeting), structure the answer in bullet points or short paragraphs.

---

## 5. Address Recommendations and Action Items Thoughtfully

Many CRM questions ask for next steps or strategies to improve sales outcomes. Consider:

- **Training**: Suggest skill development (e.g., negotiation training).  
- **Process Changes**: For instance, refining qualification criteria or implementing pipeline reviews.  
- **Resource Allocation**: Mentioning where and when to realign the sales team or support resources.  
- **Pipeline Adjustments**: Identifying stages needing closer attention to improve conversion rates.  
- **Follow-up Procedures**: Encouraging a prompt response to potential issues or unanswered questions.

Ensure any recommendation aligns with typical CRM best practices and the context of the question.

---

## 6. Summarizing Conversations and Next Steps

When asked to analyze or summarize:

1. **Extract Main Points**: Budget concerns, timeline, key objections, etc.  
2. **Identify the Stage**: Indicate if the conversation suggests negotiation, prospecting, or final stages.  
3. **Propose a Follow-Up**: If relevant, outline a logical next step (e.g., schedule a demo, finalize a quote, provide missing documentation).

---

## 7. Handling Employee Performance Inquiries

For performance-related questions:

- **Look for Key Indicators**: E.g., win rates, quota attainment, deal sizes, pipeline drop-off.  
- **Focus on Trends**: Year-over-year, quarter-over-quarter.  
- **Highlight Top Performers**: If asked, identify them based on recognized metrics (like revenue or attainment).  
- **Suggest Improvements**: Typically revolve around training, coaching, or resource shifts to address any identified weaknesses (e.g., a drop-off at a certain funnel stage).

---

## 8. Managing “Rules” and Compliance

Occasionally, questions revolve around internal policies or “rules” such as:
- Follow-up windows
- Personalization requirements
- Pipeline closure after a certain duration
- Discount limits
- Provision of free training or additional services

To address these:

1. **Identify the Rule Clearly**: State the gist of the requirement (e.g., “Do not exceed X% discount”).  
2. **Check Compliance**: If the question wants to know who adheres, be precise and consistent with data.  
3. **Quantify the Impact**: If relevant, show how compliance (or lack thereof) affects revenue, success rates, or other metrics.

---

## 9. Avoiding Incorrect or Irrelevant Details

1. **Stay Within Scope**: Only answer what is asked. If the question references a specific dataset (deals, employees, rules), confine your response to that dataset’s context.  
2. **Omit “Wrong Variants”**: If you sense certain claims contradict the established data or premises (e.g., giving a different number than the data suggests), exclude them.  
3. **Check Overlaps**: Some questions might combine multiple aspects (like performance plus pipeline analysis). Combine relevant info appropriately without introducing errors.

---

## 10. Maintaining Professional and Helpful Tone

- Keep the tone informative, helpful, and neutral.  
- If the question requires empathy or a polite response (e.g., a follow-up email after losing a deal), maintain courtesy and professionalism.  
- Acknowledge the data or feedback given (e.g., a competitor was chosen) and offer to remain available for future needs.

---

## 11. Final Check Before Providing the Answer

1. **Is the question’s main topic addressed clearly?**  
2. **Are all numerical references or facts aligned with the context given (if any)?**  
3. **Have you avoided introducing contradictions or irrelevant data?**  
4. **Is the tone professional, concise, and on-topic?**

By applying these general practices—verifying the question’s category, maintaining data consistency, providing actionable insights, and aligning with standard CRM protocols—the AI agent can produce accurate, context-appropriate responses without needing to reference exact data points or specific question-by-question correct answers."""},
            {"role": "system", "content": "You are an AI Agent that specializes in CRM and Sales. You will be given a question and a dataframe. You will need to answer the question based on the data. Return only the answer, no other text."},
            {"role": "user", "content": f"Question: {question}\n\nData: {data.to_string()}"}
        ]
    )
    return response.choices[0].message.content.strip()

def main():
    # Get API key from environment variable
    API_KEY = os.getenv("API_KEY")
    if not API_KEY:
        print("Warning: API_KEY environment variable not set.")
        print("Please register at http://localhost:5000/register to get an API key")
        print("Then set it in your .env file as API_KEY=your_key_here")
        print("For testing, using a temporary key...")
        # This should match a key in your Flask server's database
        API_KEY = "crm-a9c0d68ef00df832fad3159a6befa7ccc92c1551fe1b2699"
    
    print("CRM Benchmark Example")
    print("=====================")
    
    # Create a client
    client = BenchmarkClient(
        api_key=API_KEY,
        server_url="http://localhost:5000",
        show_progress=True
    )
    
    # Run the benchmark and submit results
    print("\nRunning benchmark with parallel processing...")
    try:
        results = client.run_and_submit(
            agent_callable=my_agent_4o_mini,
            agent_name="ChatGPT-4o-mini",
            parallel=True,
            visualize=True
        )
        
        # Handle results
        if isinstance(results, dict):
            if "status" in results and results["status"] == "error":
                print(f"\nError: {results.get('message', 'Unknown error')}")
            else:
                score = results.get('overall_average', 0)
                print(f"\nFinal Score: {score:.2f}%")
                
                # Check submission status
                submission = results.get('submission', {})
                if submission.get('status') == 'success':
                    print(f"Score successfully submitted for: {submission.get('username', 'Unknown')}")
                else:
                    print(f"Failed to submit score: {submission.get('message', 'Unknown error')}")
                    if 'request_payload' in submission:
                        print(f"Submission payload: {submission['request_payload']}")
        else:
            print(f"Unexpected results format: {results}")
            
    except Exception as e:
        print(f"Error running benchmark: {e}")
        raise
    try:
        results = client.run_and_submit(
            agent_callable=my_agent_4o,
            agent_name="ChatGPT-4o",
            parallel=True,
            visualize=True
        )
        
        # Handle results
        if isinstance(results, dict):
            if "status" in results and results["status"] == "error":
                print(f"\nError: {results.get('message', 'Unknown error')}")
            else:
                score = results.get('overall_average', 0)
                print(f"\nFinal Score: {score:.2f}%")
                
                # Check submission status
                submission = results.get('submission', {})
                if submission.get('status') == 'success':
                    print(f"Score successfully submitted for: {submission.get('username', 'Unknown')}")
                else:
                    print(f"Failed to submit score: {submission.get('message', 'Unknown error')}")
                    if 'request_payload' in submission:
                        print(f"Submission payload: {submission['request_payload']}")
        else:
            print(f"Unexpected results format: {results}")
            
    except Exception as e:
        print(f"Error running benchmark: {e}")
        raise

    try:
        results = client.run_and_submit(
            agent_callable=my_agent_o3_mini,
            agent_name="ChatGPT-o3-mini",
            parallel=True,
            visualize=True
        )
        
        # Handle results
        if isinstance(results, dict):
            if "status" in results and results["status"] == "error":
                print(f"\nError: {results.get('message', 'Unknown error')}")
            else:
                score = results.get('overall_average', 0)
                print(f"\nFinal Score: {score:.2f}%")
                
                # Check submission status
                submission = results.get('submission', {})
                if submission.get('status') == 'success':
                    print(f"Score successfully submitted for: {submission.get('username', 'Unknown')}")
                else:
                    print(f"Failed to submit score: {submission.get('message', 'Unknown error')}")
                    if 'request_payload' in submission:
                        print(f"Submission payload: {submission['request_payload']}")
        else:
            print(f"Unexpected results format: {results}")
            
    except Exception as e:
        print(f"Error running benchmark: {e}")
        raise

    try:
        results = client.run_and_submit(
            agent_callable=maxs_custom_agent,
            agent_name="Trained CRM Agent",
            parallel=True,
            visualize=True
        )
        
        # Handle results
        if isinstance(results, dict):
            if "status" in results and results["status"] == "error":
                print(f"\nError: {results.get('message', 'Unknown error')}")
            else:
                score = results.get('overall_average', 0)
                print(f"\nFinal Score: {score:.2f}%")
                
                # Check submission status
                submission = results.get('submission', {})
                if submission.get('status') == 'success':
                    print(f"Score successfully submitted for: {submission.get('username', 'Unknown')}")
                else:
                    print(f"Failed to submit score: {submission.get('message', 'Unknown error')}")
                    if 'request_payload' in submission:
                        print(f"Submission payload: {submission['request_payload']}")
        else:
            print(f"Unexpected results format: {results}")
            
    except Exception as e:
        print(f"Error running benchmark: {e}")
        raise

if __name__ == "__main__":
    main() 