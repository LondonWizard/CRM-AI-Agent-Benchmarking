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

# Import your chat function EXACTLY as your system is set up:
from chatgpt import chat

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
      - 4 deals in Negotiation => total 250K
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
            amount=500000,
            owner_id="EMP476bbd",
            lead_source="Webinar",
            close_date="2025-12-31",
            next_step="Phone follow-up"
        ),
        D1Deal(
            deal_name="Northstar",
            stage="Negotiation",
            amount=60000,
            owner_id="EMP111111",
            lead_source="Webinar",
            close_date="",  # Missing close date
            next_step="Needs next step"
        ),
        D1Deal(
            deal_name="Redline",
            stage="Negotiation",
            amount=40000,
            owner_id="EMP222222",
            lead_source="Trade Show",
            close_date="2025-09-10",
            next_step=""  # Missing next step
        ),
        D1Deal(
            deal_name="Stafford Ltd",
            stage="Negotiation",
            amount=50000,
            owner_id="EMP333333",
            lead_source="Referral",
            close_date="2025-10-01",
            next_step="Follow-up call"
        ),
        D1Deal(
            deal_name="King, Tucker & Rowe",
            stage="Negotiation",
            amount=100000,
            owner_id="EMP444444",
            lead_source="Webinar",
            close_date="2025-07-15",
            next_step="Send revised proposal"
        ),
        D1Deal(
            deal_name="Global Industries",
            stage="Qualification",
            amount=150000,
            owner_id="EMP555555",
            lead_source="Webinar",
            close_date="2025-06-30",
            next_step="Confirm details"
        ),
        D1Deal(
            deal_name="Global Ind.",
            stage="Qualification",
            amount=150000,
            owner_id="EMP666666",
            lead_source="Webinar",
            close_date="2025-06-29",
            next_step="Review next steps"
        ),
    ]

    stages = ["Prospecting", "Qualification", "Proposal", "Negotiation", "Closed Won", "Closed Lost"]
    lead_sources = ["Webinar", "Referral", "Cold Call", "Trade Show", "Partner"]
    extra_records = []

    # Generate many random deals
    for _ in range(200):
        deal = D1Deal(
            deal_name=fake.company(),
            stage=random.choice(stages),
            amount=float(random.randint(10000, 200000)),
            owner_id=f"EMP{random.randint(100000,999999)}",
            lead_source=random.choice(lead_sources),
            close_date=(datetime.now() + timedelta(days=random.randint(1, 400))).strftime("%Y-%m-%d"),
            next_step=random.choice([
                "Schedule demo",
                "Email follow-up",
                "Call next week",
                "",
                "Arrange site visit"
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
    sentiments = ["Positive","Neutral","Negative"]
    stage_guesses = ["Qualification","Proposal","Negotiation","Closed Won","Closed Lost","Unknown"]
    possible_objections = ["Price","Timeline","Features","Implementation","Budget","", "Support"]

    additional_threads = []
    for i in range(300):
        # We'll ask ChatGPT to generate a short email about sales or product queries
        # in plain text (no JSON). We'll store that in the "content" field.
        prompt = (
            "Please write a short email excerpt for a sales conversation. "
            "Include a random mention of budget, timeline, or features. "
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
    D3: general sales knowledge, includes:
      - 'XYZ Opportunity' (Proposal, $50k, Prob=60)
      - 'Northbound' (Qualification, $150k, Prob=80)
      - 'DeltaOne' (Negotiation, $150k, Prob=75)
      - 'Optima' (Proposal, $80k, 50%, no update 90 days)
      - 'RoverTech' (Qualification, $70k, 40%, no update 90 days)
      - 10 leads with some success markers
      - 1 meeting transcript
      - 1 lost deal (MavTech)
      Then random expansions + saving CSV.
    """
    signature_records = [
        D3Record(
            record_type="Opportunity",
            name="XYZ Opportunity",
            stage="Proposal",
            amount=50000,
            probability=60,
            last_activity_days=5,
            notes="Ready to close soon"
        ),
        D3Record(
            record_type="Opportunity",
            name="Northbound",
            stage="Qualification",
            amount=150000,
            probability=80,
            last_activity_days=10,
            notes="High confidence"
        ),
        D3Record(
            record_type="Opportunity",
            name="DeltaOne",
            stage="Negotiation",
            amount=150000,
            probability=75,
            last_activity_days=8,
            notes="Also high confidence"
        ),
        D3Record(
            record_type="Opportunity",
            name="Optima",
            stage="Proposal",
            amount=80000,
            probability=50,
            last_activity_days=91,
            notes="No updates in over 90 days"
        ),
        D3Record(
            record_type="Opportunity",
            name="RoverTech",
            stage="Qualification",
            amount=70000,
            probability=40,
            last_activity_days=95,
            notes="No updates in over 90 days"
        ),
    ]

    # Add 10 leads
    leads = ["TechAlpha","BizSolutions","StartupX","EnterpriseY","RetailZ",
             "AutoMates","FoodServ","LogiTech","EduServe","FinGroup"]
    for lead in leads:
        signature_records.append(
            D3Record(
                record_type="Lead",
                name=lead,
                stage="",
                amount=0,
                probability=0,
                last_activity_days=random.randint(1,30),
                notes=f"{random.randint(1,4)} success markers"
            )
        )

    # Add 1 meeting transcript
    signature_records.append(
        D3Record(
            record_type="Meeting",
            name="Sales Team Sync",
            stage="",
            amount=0,
            probability=0,
            last_activity_days=0,
            notes="Discussed synergy, timeline extended 2 weeks, rep A clarifies features, rep B confirms budget"
        )
    )

    # Lost deal
    signature_records.append(
        D3Record(
            record_type="Opportunity",
            name="MavTech",
            stage="Closed Lost",
            amount=120000,
            probability=0,
            last_activity_days=0,
            notes="Lost in final stage to competitor"
        )
    )

    # Random expansions
    record_types = ["Opportunity", "Lead", "Meeting"]
    opp_stages = ["Qualification","Proposal","Negotiation","Closed Won","Closed Lost",""]
    extra_records = []
    for _ in range(200):
        rt = random.choice(record_types)
        st = random.choice(opp_stages) if rt == "Opportunity" else ""
        amt = random.uniform(10000, 150000) if rt == "Opportunity" else 0
        prob = random.randint(10,90) if rt == "Opportunity" else 0
        rec = D3Record(
            record_type=rt,
            name=fake.company(),
            stage=st,
            amount=round(amt,2),
            probability=prob,
            last_activity_days=random.randint(0,120),
            notes="Additional record from random generation"
        )
        extra_records.append(rec)

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
    D4: sales rules compliance
    1) Follow up in 3 days
    2) Personalize => +20% revenue
    3) Close deals older than 30 days
    4) <=10% discount
    5) max free training hours
    We'll create ~100 random reps, with some compliance flags,
    then compute total revenue. Save to CSV.
    """
    data = []
    for _ in range(100):
        rep_id = f"EMP{fake.random_number(digits=4)}"
        follow3 = bool(random.getrandbits(1))
        personal = bool(random.getrandbits(1))
        stale = bool(random.getrandbits(1))
        discount_ok = bool(random.getrandbits(1))
        r5 = bool(random.getrandbits(1))

        base_revenue = random.randint(20000, 100000)
        if personal:
            base_revenue *= 1.2  # +20% if personalized

        rec = D4RepCompliance(
            rep_id=rep_id,
            follow_up_3days=follow3,
            personalized_followup=personal,
            close_stale_deals=stale,
            discount_under_10pct=discount_ok,
            rule5_compliant=r5,
            total_revenue_this_quarter=round(base_revenue,2)
        )
        data.append(rec)

    df = pd.DataFrame([r.dict() for r in data])
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
    D5: employee performance
    - 8 'core' reps + 10 extra
    - 2 years, 4 quarters each
    - volume up each quarter, win rate down
    - store in CSV
    """
    core_reps = ["EMP111","EMP222","EMP333","EMP444","EMP555","EMP666","EMP777","EMPxyz"]
    extra_reps = [f"EMP{fake.random_number(digits=4)}" for _ in range(10)]
    all_reps = core_reps + extra_reps

    data = []
    for rep in all_reps:
        for year in [2024, 2025]:
            for q_idx, qtr in enumerate(["Q1","Q2","Q3","Q4"]):
                base_deals = 20 + q_idx*5
                deals_variation = random.randint(-3,3)
                total_deals = base_deals + deals_variation

                # baseline ~40%, drops 5% each quarter
                base_win_rate = 0.40 - 0.05 * q_idx
                actual_win_rate = base_win_rate + random.uniform(-0.03, 0.03)
                actual_win_rate = max(0.1, min(0.9, actual_win_rate))
                closed_won = int(total_deals * actual_win_rate)

                # bigger factor for core reps
                big_factor = 2.0 if rep in core_reps[:5] else 1.0
                avg_deal = (2000 * big_factor) + random.randint(-500, 500)
                avg_deal = max(avg_deal, 500)
                total_rev = closed_won * avg_deal

                perf = D5Performance(
                    rep_id=rep,
                    year=year,
                    quarter=qtr,
                    total_deals=total_deals,
                    closed_won=closed_won,
                    total_revenue=round(total_rev,2),
                    avg_win_rate=round(actual_win_rate*100,2)
                )
                data.append(perf)

    df = pd.DataFrame([r.dict() for r in data])
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
