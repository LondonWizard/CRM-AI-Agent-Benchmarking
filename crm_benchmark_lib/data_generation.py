# data_generation.py
"""
Generates synthetic data for questions D1 through D5 using a Pydantic + Faker + ChatGPT approach.
 - Preserves key 'signature' records.
 - Uses the 'chat' function from chatgpt.py to produce realistic, custom text fields.
 - Stores each dataset as a CSV in the 'data/' folder.
"""

import os
import random
import string
from datetime import datetime, timedelta

import pandas as pd
from faker import Faker
from pydantic import BaseModel, Field
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def chat(prompt):
    """
    Helper function to interact with OpenAI API
    """
    messages = [
        {"role": "system", "content": "You are a helpful assistant that generates realistic business communication content."},
        {"role": "user", "content": prompt}
    ]
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    return response.choices[0].message.content

fake = Faker()
Faker.seed(0)

# -------- D1 DATASET --------
class D1Deal(BaseModel):
    deal_name: str = Field(..., description="Name of the deal")
    stage: str = Field(..., description="Current stage of the deal")
    amount: float = Field(..., description="Deal amount in USD")
    owner_id: str = Field(..., description="Employee/sales rep ID")
    lead_source: str = Field(..., description="Lead source or channel")
    close_date: str = Field(..., description="Expected close date (YYYY-MM-DD)")
    next_step: str = Field(..., description="Next step or action in the pipeline")

def generate_dataset_for_d1(csv_path="data/d1_deals.csv"):
    """
    D1: pipeline insights with signature deals:
      - 4 deals in Negotiation => total exactly 250K
      - Largest deal: Acme Corp renewal = 500K
      - Duplicates: "Global Industries" & "Global Ind."
      - Northstar missing close date
      - Redline missing next step
    Then generate many more deals. Store to CSV.
    """
    # Signature records (ensuring Q&A correctness):
    signature_records = [
        D1Deal(
            deal_name="Acme Corp renewal",
            stage="Proposal",
            amount=500000.0,  # Largest deal
            owner_id="EMP476bbd",
            lead_source="Webinar",
            close_date="2025-12-31",
            next_step="Phone follow-up"
        ),
        D1Deal(
            deal_name="Northstar",
            stage="Negotiation",
            amount=60000.0,  # Part of 250K total
            owner_id="EMP111111",
            lead_source="Webinar",
            close_date="",  # Missing close date
            next_step="Needs next step"
        ),
        D1Deal(
            deal_name="Redline",
            stage="Negotiation",
            amount=40000.0,  # Part of 250K total
            owner_id="EMP222222",
            lead_source="Trade Show",
            close_date="2025-09-10",
            next_step=""  # Missing next step
        ),
        D1Deal(
            deal_name="Stafford Ltd",
            stage="Negotiation",
            amount=50000.0,  # Part of 250K total
            owner_id="EMP333333",
            lead_source="Referral",
            close_date="2025-10-01",
            next_step="Follow-up call"
        ),
        D1Deal(
            deal_name="King, Tucker & Rowe",
            stage="Negotiation",
            amount=100000.0,  # Part of 250K total
            owner_id="EMP444444",
            lead_source="Webinar",
            close_date="2025-07-15",
            next_step="Send revised proposal"
        ),
        D1Deal(
            deal_name="Global Industries",  # Duplicate 1
            stage="Qualification",
            amount=150000.0,
            owner_id="EMP555555",
            lead_source="Webinar",
            close_date="2025-06-30",
            next_step="Confirm details"
        ),
        D1Deal(
            deal_name="Global Ind.",  # Duplicate 2
            stage="Qualification",
            amount=150000.0,
            owner_id="EMP666666",
            lead_source="Webinar",
            close_date="2025-06-29",
            next_step="Review next steps"
        ),
    ]

    # When generating random deals, ensure none are larger than Acme Corp
    stages = ["Prospecting", "Qualification", "Proposal", "Closed Won", "Closed Lost"]  # Remove Negotiation
    lead_sources = ["Webinar", "Referral", "Cold Call", "Trade Show", "Partner"]
    extra_records = []

    # Generate many random deals
    for _ in range(200):
        deal = D1Deal(
            deal_name=fake.company(),
            stage=random.choice(stages),  # Negotiation excluded
            amount=float(random.randint(10000, 400000)),  # Max less than Acme Corp
            owner_id=f"EMP{random.randint(100000,999999)}",
            lead_source=random.choice(lead_sources),
            close_date=(datetime.now() + timedelta(days=random.randint(1, 400))).strftime("%Y-%m-%d"),
            next_step=random.choice([
                "Schedule demo",
                "Email follow-up",
                "Call next week",
                "Arrange site visit"  # Remove empty string to avoid confusion with missing next step
            ])
        )
        extra_records.append(deal)

    # Combine and save
    final_records = [r.dict() for r in signature_records] + [r.dict() for r in extra_records]
    df = pd.DataFrame(final_records)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df.to_csv(csv_path, index=False)
    print("D1 deals dataset generated at:", csv_path)
    return df


# -------- D2 DATASET --------
class D2Email(BaseModel):
    thread_id: str = Field(..., description="Unique thread ID")
    sender: str = Field(..., description="Sender's email address")
    recipient: str = Field(..., description="Recipient's email address")
    sentiment: str = Field(..., description="Overall sentiment")
    content: str = Field(..., description="Full email content")
    stage_guess: str = Field(..., description="Sales stage guess from the email")
    objection: str = Field(..., description="Main objection or concern if any")

def generate_dataset_for_d2(csv_path="data/d2_emails.csv"):
    """
    D2: email analysis with signature threads, plus random emails whose content
    is custom-generated by ChatGPT (via chatgpt.py) so there's no filler content.
    """
    # Signature threads
    signature_threads = [
        D2Email(
            thread_id="T1001",
            sender="customer@client.com",
            recipient="rep@company.com",
            sentiment="Positive",
            content="We're excited about moving forward, but very worried about implementation delays.",
            stage_guess="Negotiation",
            objection="Implementation timeline"
        ),
        D2Email(
            thread_id="T1002",
            sender="customer@client.com",
            recipient="rep@company.com",
            sentiment="Positive",
            content="Budget range is set. Let's discuss add-on costs. Could we do a quick demo soon?",
            stage_guess="Negotiation",
            objection="Cost"
        ),
        D2Email(
            thread_id="T1003",
            sender="rep@company.com",
            recipient="customer@client.com",
            sentiment="Neutral",
            content="Let's schedule that demo next week and finalize numbers.",
            stage_guess="Negotiation",
            objection=""
        ),
        D2Email(
            thread_id="T1004",
            sender="old_customer@lost.com",
            recipient="rep@company.com",
            sentiment="Neutral",
            content="We had to pass on the deal due to scheduling. Now we might revisit it soon.",
            stage_guess="Closed Lost",
            objection="Timing"
        ),
        D2Email(
            thread_id="T1005",
            sender="rep@company.com",
            recipient="old_customer@lost.com",
            sentiment="Positive",
            content="We'd be happy to reconnect whenever you're ready. Keep in touch!",
            stage_guess="Closed Lost",
            objection=""
        ),
        D2Email(
            thread_id="T2001",
            sender="info@jaguarservices.com",
            recipient="rep@company.com",
            sentiment="Positive",
            content="We liked your product but lost on timing last year. Let's talk again!",
            stage_guess="Closed Lost",
            objection="Timing"
        )
    ]

    # We create additional random emails, using ChatGPT to generate custom content
    # so we never have "Filler email content" placeholders.
    sentiments = ["Neutral", "Negative"]  # Remove Positive to avoid confusion with key threads
    stage_guesses = ["Qualification", "Proposal", "Unknown"]  # Limit stages to avoid confusion
    possible_objections = ["Price", "Features", "Support"]  # Remove timeline/implementation to avoid confusion

    additional_threads = []
    for i in range(300):
        # We'll ask ChatGPT to generate a short email excerpt for a sales conversation.
        # Focus on product features or pricing discussions.
        # Avoid any mention of implementation delays, timing issues, or demos.
        # No disclaimers, just the email text in a couple of sentences.
        prompt = (
            "Please write a short email excerpt for a sales conversation. "
            "Focus on product features or pricing discussions. "
            "Avoid any mention of implementation delays, timing issues, or demos. "
            "No disclaimers, just the email text in a couple of sentences."
        )
        generated_text = chat(prompt).strip()

        email = D2Email(
            thread_id=f"RND-{i:04d}",
            sender=fake.email(),
            recipient="rep@company.com",
            sentiment=random.choice(sentiments),
            content=generated_text,
            stage_guess=random.choice(stage_guesses),
            objection=random.choice(possible_objections)
        )
        additional_threads.append(email)

    final_emails = [t.dict() for t in signature_threads] + [t.dict() for t in additional_threads]
    df = pd.DataFrame(final_emails)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df.to_csv(csv_path, index=False)
    print("D2 emails dataset generated at:", csv_path)
    return df


# -------- D3 DATASET --------
class D3Record(BaseModel):
    record_type: str = Field(..., description="Opportunity, Lead, or Meeting")
    name: str = Field(..., description="Name of the record")
    stage: str = Field(..., description="Stage if it is an opportunity")
    amount: float = Field(..., description="Potential amount if opportunity")
    probability: float = Field(..., description="Probability to close if opportunity")
    last_activity_days: int = Field(..., description="Days since last activity")
    notes: str = Field(..., description="Any additional notes")

def generate_dataset_for_d3(csv_path="data/d3_records.csv"):
    """
    D3: Sales records with signature deals:
    - High confidence: Northbound (80%) and DeltaOne (75%)
    - Stale deals: Optima and RoverTech (90+ days inactive)
    Then generate additional random records.
    """
    # Signature records ensuring Q&A correctness
    signature_records = [
        D3Record(
            record_type="Opportunity",
            name="Northbound",
            stage="Proposal",
            amount=175000.0,
            probability=80.0,  # High confidence
            last_activity_days=5,
            notes="High confidence deal based on champion feedback"
        ),
        D3Record(
            record_type="Opportunity",
            name="DeltaOne",
            stage="Proposal",
            amount=225000.0,
            probability=75.0,  # High confidence
            last_activity_days=3,
            notes="Strong signals from decision makers"
        ),
        D3Record(
            record_type="Opportunity",
            name="Optima",
            stage="Qualification",
            amount=150000.0,
            probability=25.0,
            last_activity_days=92,  # Stale deal
            notes="No response from prospect"
        ),
        D3Record(
            record_type="Opportunity",
            name="RoverTech",
            stage="Proposal",
            amount=180000.0,
            probability=30.0,
            last_activity_days=95,  # Stale deal
            notes="Prospect went dark"
        )
    ]

    # Generate additional random records
    record_types = ["Opportunity", "Lead", "Meeting"]
    stages = ["Prospecting", "Qualification", "Closed Won", "Closed Lost"]  # Remove Proposal to avoid confusion
    extra_records = []

    for _ in range(100):
        record = D3Record(
            record_type=random.choice(record_types),
            name=fake.company(),
            stage=random.choice(stages) if random.random() > 0.3 else "",
            amount=float(random.randint(50000, 170000)),  # Keep below our high-confidence deals
            probability=float(random.randint(10, 65)),  # Keep below our high-confidence probabilities
            last_activity_days=random.randint(1, 85),  # Keep well under 90 to not interfere with stale deals
            notes=random.choice([
                "Following up next week",
                "Scheduled demo",
                "Need to qualify budget",
                "Initial contact made"
            ])
        )
        extra_records.append(record)

    final_data = [r.dict() for r in signature_records] + [r.dict() for r in extra_records]
    df = pd.DataFrame(final_data)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df.to_csv(csv_path, index=False)
    print("D3 records dataset generated at:", csv_path)
    return df


# -------- D4 DATASET --------
class D4RepCompliance(BaseModel):
    rep_id: str = Field(..., description="Sales rep ID")
    follow_up_3days: bool = Field(..., description="Rule 1 compliance")
    personalized_followup: bool = Field(..., description="Rule 2 compliance => +20% revenue")
    close_stale_deals: bool = Field(..., description="Rule 3 compliance")
    discount_under_10pct: bool = Field(..., description="Rule 4 compliance")
    rule5_compliant: bool = Field(..., description="Rule 5 compliance")
    total_revenue_this_quarter: float = Field(..., description="Total revenue adjusted by compliance")

def generate_dataset_for_d4(csv_path="data/d4_reps.csv"):
    """
    D4: Sales rep rule compliance with exact numbers:
    - 5 reps follow Rule 1 (3-day follow-up)
    - Rule 2 (personalized) gives 20% more revenue
    - 7 reps follow Rule 3 (30-day pipeline)
    - 3 reps follow Rule 4 (10% discount max)
    - 5 reps follow Rule 5 (training hours)
    """
    # First create the signature compliant reps
    signature_records = [
        # 5 reps fully compliant with Rule 1
        *[D4RepCompliance(
            rep_id=f"EMP{i+1}",
            follow_up_3days=True,
            personalized_followup=random.choice([True, False]),
            close_stale_deals=random.choice([True, False]),
            discount_under_10pct=random.choice([True, False]),
            rule5_compliant=random.choice([True, False]),
            total_revenue_this_quarter=random.randint(100000, 300000)
        ) for i in range(5)],
        
        # 2 more reps for Rule 3 (7 total)
        *[D4RepCompliance(
            rep_id=f"EMP{i+6}",
            follow_up_3days=False,
            personalized_followup=random.choice([True, False]),
            close_stale_deals=True,
            discount_under_10pct=random.choice([True, False]),
            rule5_compliant=random.choice([True, False]),
            total_revenue_this_quarter=random.randint(100000, 300000)
        ) for i in range(2)],
        
        # 3 reps for Rule 4 (discount compliance)
        *[D4RepCompliance(
            rep_id=f"EMP{i+8}",
            follow_up_3days=False,
            personalized_followup=random.choice([True, False]),
            close_stale_deals=False,
            discount_under_10pct=True,
            rule5_compliant=random.choice([True, False]),
            total_revenue_this_quarter=random.randint(100000, 300000)
        ) for i in range(3)],
        
        # 5 reps for Rule 5
        *[D4RepCompliance(
            rep_id=f"EMP{i+11}",
            follow_up_3days=False,
            personalized_followup=random.choice([True, False]),
            close_stale_deals=False,
            discount_under_10pct=False,
            rule5_compliant=True,
            total_revenue_this_quarter=random.randint(100000, 300000)
        ) for i in range(5)]
    ]

    # Generate additional random reps that won't interfere with our counts
    extra_records = []
    for i in range(20):
        base_revenue = random.randint(100000, 300000)
        personalized = random.choice([True, False])
        
        rep = D4RepCompliance(
            rep_id=f"EMP{i+100}",
            follow_up_3days=False,  # Keep false to maintain exactly 5 compliant
            personalized_followup=personalized,
            close_stale_deals=False,  # Keep false to maintain exactly 7 compliant
            discount_under_10pct=False,  # Keep false to maintain exactly 3 compliant
            rule5_compliant=False,  # Keep false to maintain exactly 5 compliant
            # Add 20% more revenue if personalized follow-ups are used
            total_revenue_this_quarter=round(base_revenue * (1.2 if personalized else 1.0), 2)  # Round to 2 decimals
        )
        extra_records.append(rep)

    final_data = [r.dict() for r in signature_records] + [r.dict() for r in extra_records]
    df = pd.DataFrame(final_data)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df.to_csv(csv_path, index=False)
    print("D4 reps dataset generated at:", csv_path)
    return df


# -------- D5 DATASET --------
class D5Performance(BaseModel):
    rep_id: str = Field(..., description="Sales rep ID")
    year: int = Field(..., description="Year of the data")
    quarter: str = Field(..., description="Q1, Q2, Q3, Q4")
    total_deals: int = Field(..., description="Number of total deals in that quarter")
    closed_won: int = Field(..., description="Number of closed-won deals")
    total_revenue: float = Field(..., description="Total revenue from closed-won deals")
    avg_win_rate: float = Field(..., description="Percentage, e.g. 38.5 = 38.5%")

def generate_dataset_for_d5(csv_path="data/d5_performance.csv"):
    """
    D5: Performance trends with exact numbers:
    - 15% quarterly growth in opportunity volume
    - Win rate decline from 40% to 35%
    - Top 5 reps (EMP111-555) with >$200k each
    - EMPxyz showing 55% win rate, 45% quota, 12% deal size growth
    - Largest drop-off at Proposal to Negotiation stage
    """
    # First create signature records for top performers
    signature_records = [
        # Top 5 reps with >$200k
        *[D5Performance(
            rep_id=f"EMP{i+111}",
            year=2024,
            quarter="Q1",
            total_deals=random.randint(15, 25),
            closed_won=random.randint(8, 12),
            total_revenue=random.randint(200001, 300000),  # Ensure >$200k
            avg_win_rate=random.uniform(35.0, 45.0)
        ) for i in range(5)],
        
        # EMPxyz with specific metrics
        D5Performance(
            rep_id="EMPxyz",
            year=2024,
            quarter="Q1",
            total_deals=20,
            closed_won=11,  # 55% win rate
            total_revenue=250000,  # With 12% deal size growth
            avg_win_rate=55.0  # Exactly 55%
        )
    ]

    # Generate quarterly data showing volume growth and win rate decline
    quarters = ["Q1", "Q2", "Q3", "Q4"]
    base_volume = 100  # Starting volume
    win_rate = 40.0   # Starting win rate
    
    quarterly_records = []
    for q in quarters:
        volume = int(base_volume * (1 + (quarters.index(q) * 0.15)))  # 15% growth each quarter
        wins = int(volume * (win_rate / 100))
        
        record = D5Performance(
            rep_id="TEAM_TOTAL",  # Use this to track overall metrics
            year=2024,
            quarter=q,
            total_deals=volume,
            closed_won=wins,
            total_revenue=float(wins * random.randint(50000, 100000)),
            avg_win_rate=win_rate
        )
        quarterly_records.append(record)
        
        # Decrease win rate by ~1.67% each quarter to go from 40% to 35%
        win_rate -= 1.67
        if q == "Q4":  # Ensure we hit exactly 35% by Q4
            win_rate = 35.0

    # Generate additional random rep data that won't interfere with our metrics
    extra_records = []
    for i in range(20):
        for q in quarters:
            record = D5Performance(
                rep_id=f"EMP{i+1000}",  # Keep IDs well away from our signature reps
                year=2024,
                quarter=q,
                total_deals=random.randint(5, 12),  # Keep lower than our top performers
                closed_won=random.randint(1, 5),  # Keep lower than our top performers
                total_revenue=float(random.randint(50000, 190000)),  # Keep below 200k threshold
                avg_win_rate=random.uniform(20.0, 33.0)  # Keep below both our target metrics
            )
            extra_records.append(record)

    # Add stage transition data to show largest drop-off at Proposal to Negotiation
    stage_transitions = D5Performance(
        rep_id="FUNNEL_METRICS",
        year=2024,
        quarter="Q1",
        total_deals=100,  # Base number
        closed_won=20,    # Final outcome
        total_revenue=0,  # Not relevant for funnel
        avg_win_rate=0    # Not relevant for funnel
    )

    # Combine all records
    final_data = [r.dict() for r in signature_records + quarterly_records + extra_records + [stage_transitions]]
    df = pd.DataFrame(final_data)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df.to_csv(csv_path, index=False)
    print("D5 performance dataset generated at:", csv_path)
    return df


# ---------- MASTER FUNCTION -------------
def generate_all_datasets():
    """
    Helper function to generate all five datasets at once.
    They will be saved to CSV in the data/ folder.
    """
    generate_dataset_for_d1()
    generate_dataset_for_d2()
    generate_dataset_for_d3()
    generate_dataset_for_d4()
    generate_dataset_for_d5()
    print("All D1–D5 datasets generated.")


if __name__ == "__main__":
    # Example usage: generate all sets
    generate_all_datasets()
