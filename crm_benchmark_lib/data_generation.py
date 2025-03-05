# data_generation.py
"""
Functions that generate data for each question set (D1, D2, D3, D4, D5).
We've minimized the random generation so that the main trends are unmistakable.
"""

import pandas as pd
import random
import string

def _create_random_string(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def generate_dataset_for_d1():
    """
    D1: pipeline insights, includes:
    - 4 deals in Negotiation => total 250K
    - Largest deal: Acme Corp renewal = 500K, Owner EMP476bbd
    - Duplicates: "Global Industries" & "Global Ind."
    - Northstar missing close date
    - Redline missing next step
    """
    data = [
        {
            "DealName": "Acme Corp renewal",
            "Stage": "Proposal",  # Not in negotiation
            "Amount": 500000,  # largest deal
            "OwnerID": "EMP476bbd",
            "LeadSource": "Webinar",
            "CloseDate": "2025-12-31",
            "NextStep": "Phone follow-up"
        },
        {
            "DealName": "Northstar",
            "Stage": "Negotiation",
            "Amount": 60000,
            "OwnerID": "EMP111111",
            "LeadSource": "Webinar",
            "CloseDate": None,  # missing close date
            "NextStep": "Needs next step"
        },
        {
            "DealName": "Redline",
            "Stage": "Negotiation",
            "Amount": 40000,
            "OwnerID": "EMP222222",
            "LeadSource": "Trade Show",
            "CloseDate": "2025-09-10",
            "NextStep": None  # missing next step
        },
        {
            "DealName": "Stafford Ltd",
            "Stage": "Negotiation",
            "Amount": 50000,
            "OwnerID": "EMP333333",
            "LeadSource": "Referral",
            "CloseDate": "2025-10-01",
            "NextStep": "Follow-up call"
        },
        {
            "DealName": "King, Tucker & Rowe",
            "Stage": "Negotiation",
            "Amount": 100000,
            "OwnerID": "EMP444444",
            "LeadSource": "Webinar",
            "CloseDate": "2025-07-15",
            "NextStep": "Send revised proposal"
        },
        {
            "DealName": "Global Industries",
            "Stage": "Qualification",
            "Amount": 150000,
            "OwnerID": "EMP555555",
            "LeadSource": "Webinar",
            "CloseDate": "2025-06-30",
            "NextStep": "Confirm details"
        },
        {
            "DealName": "Global Ind.",
            "Stage": "Qualification",
            "Amount": 150000,
            "OwnerID": "EMP666666",
            "LeadSource": "Webinar",
            "CloseDate": "2025-06-29",
            "NextStep": "Review next steps"
        }
    ]
    # 4 deals in Negotiation => 60k + 40k + 50k + 100k = 250k total

    # Add a couple random deals in random stages, just to flesh it out
    for _ in range(2):
        data.append({
            "DealName": _create_random_string(),
            "Stage": random.choice(["Closed Won", "Closed Lost", "Proposal"]),
            "Amount": random.randint(20000, 80000),
            "OwnerID": "EMP"+str(random.randint(100000,999999)),
            "LeadSource": random.choice(["Cold Call", "Referral", "Webinar"]),
            "CloseDate": f"2025-0{random.randint(1,9)}-{random.randint(1,28):02d}",
            "NextStep": random.choice(["", "Schedule demo", "Phone meeting"])
        })

    df = pd.DataFrame(data)
    return df


def generate_dataset_for_d2():
    """
    D2: email analysis:
    - Positive sentiment, but concern about implementation delays
    - Negotiation stage, cost objections
    - Possibly re-engaging a closed lost (Jaguar Services)
    """
    data = [
        {
            "ThreadID": "T1001",
            "Sender": "customer@client.com",
            "Recipient": "rep@company.com",
            "Sentiment": "Positive",
            "Content": "We're excited about moving forward, but very worried about implementation delays.",
            "StageGuess": "Negotiation",
            "Objection": "Implementation timeline"
        },
        {
            "ThreadID": "T1002",
            "Sender": "customer@client.com",
            "Recipient": "rep@company.com",
            "Sentiment": "Positive",
            "Content": "Budget range is set. Let's discuss add-on costs. Could we do a quick demo soon?",
            "StageGuess": "Negotiation",
            "Objection": "Cost"
        },
        {
            "ThreadID": "T1003",
            "Sender": "rep@company.com",
            "Recipient": "customer@client.com",
            "Sentiment": "Neutral",
            "Content": "Let's schedule that demo next week and finalize numbers.",
            "StageGuess": "Negotiation",
            "Objection": None
        },
        {
            "ThreadID": "T1004",
            "Sender": "old_customer@lost.com",
            "Recipient": "rep@company.com",
            "Sentiment": "Neutral",
            "Content": "We had to pass on the deal due to scheduling. Now we might revisit it soon.",
            "StageGuess": "Closed Lost",
            "Objection": "Timing"
        },
        {
            "ThreadID": "T1005",
            "Sender": "rep@company.com",
            "Recipient": "old_customer@lost.com",
            "Sentiment": "Positive",
            "Content": "We'd be happy to reconnect whenever you're ready. Keep in touch!",
            "StageGuess": "Closed Lost",
            "Objection": None
        },
        {
            "ThreadID": "T2001",
            "Sender": "info@jaguarservices.com",
            "Recipient": "rep@company.com",
            "Sentiment": "Positive",
            "Content": "We liked your product but lost on timing last year. Let's talk again!",
            "StageGuess": "Closed Lost",
            "Objection": "Timing"
        }
    ]

    # Add a few random filler threads
    for i in range(5):
        data.append({
            "ThreadID": f"FILLER{i}",
            "Sender": f"random{i}@client.com",
            "Recipient": "rep@company.com",
            "Sentiment": random.choice(["Positive","Neutral","Negative"]),
            "Content": "Random filler email content, might not be relevant.",
            "StageGuess": random.choice(["Qualification","Proposal","Negotiation","Closed Won","Closed Lost"]),
            "Objection": random.choice(["Price","Timeline","Features",None])
        })

    df = pd.DataFrame(data)
    return df


def generate_dataset_for_d3():
    """
    D3: general sales knowledge
    - XYZ => stage => now Closed Won
    - forecasted revenue => sum
    - at-risk deals => 90+ days
    - ranking leads
    - meeting transcripts
    - lost deal => follow-up email
    """
    data = []

    # Key opportunities:
    data.extend([
        {
            "RecordType": "Opportunity",
            "Name": "XYZ Opportunity",
            "Stage": "Proposal",   # might be changed to 'Closed Won'
            "Amount": 50000,
            "Probability": 60,
            "LastActivityDays": 5,
            "Notes": "Ready to close soon"
        },
        {
            "RecordType": "Opportunity",
            "Name": "Northbound",
            "Stage": "Qualification",
            "Amount": 150000,
            "Probability": 80,
            "LastActivityDays": 10,
            "Notes": "High confidence"
        },
        {
            "RecordType": "Opportunity",
            "Name": "DeltaOne",
            "Stage": "Negotiation",
            "Amount": 150000,
            "Probability": 75,
            "LastActivityDays": 8,
            "Notes": "Also high confidence"
        },
        {
            "RecordType": "Opportunity",
            "Name": "Optima",
            "Stage": "Proposal",
            "Amount": 80000,
            "Probability": 50,
            "LastActivityDays": 91,
            "Notes": "No updates in over 90 days"
        },
        {
            "RecordType": "Opportunity",
            "Name": "RoverTech",
            "Stage": "Qualification",
            "Amount": 70000,
            "Probability": 40,
            "LastActivityDays": 95,
            "Notes": "No updates in over 90 days"
        }
    ])

    # Some leads
    leads = ["TechAlpha","BizSolutions","StartupX","EnterpriseY","RetailZ",
             "AutoMates","FoodServ","LogiTech","EduServe","FinGroup"]
    for lead in leads:
        data.append({
            "RecordType": "Lead",
            "Name": lead,
            "Stage": None,
            "Amount": None,
            "Probability": None,
            "LastActivityDays": random.randint(1,30),
            "Notes": f"{random.randint(1,4)} success markers"
        })

    # A meeting transcript
    data.append({
        "RecordType": "Meeting",
        "Name": "Sales Team Sync",
        "Stage": None,
        "Amount": None,
        "Probability": None,
        "LastActivityDays": None,
        "Notes": "Discussed synergy, timeline extended 2 weeks, rep A clarifies features, rep B confirms budget"
    })

    # A lost deal to do a follow-up email
    data.append({
        "RecordType": "Opportunity",
        "Name": "MavTech",
        "Stage": "Closed Lost",
        "Amount": 120000,
        "Probability": 0,
        "LastActivityDays": 0,
        "Notes": "Lost in final stage to competitor"
    })

    # A few random fillers
    for i in range(3):
        data.append({
            "RecordType": random.choice(["Opportunity","Lead","Meeting"]),
            "Name": f"Random{i}",
            "Stage": random.choice([None, "Qualification","Proposal","Negotiation","Closed Won","Closed Lost"]),
            "Amount": random.randint(30000, 100000) if random.random()<0.6 else None,
            "Probability": random.randint(10,90) if random.random()<0.6 else None,
            "LastActivityDays": random.randint(0,120),
            "Notes": "Filler data"
        })

    df = pd.DataFrame(data)
    return df


def generate_dataset_for_d4():
    """
    D4: sales rules compliance
    - 1) Follow-up in 3 days
    - 2) Personalize => +20% revenue
    - 3) Close deals older than 30
    - 4) <=10% discount
    - 5) Max free training hours
    We'll keep only 6 reps so it's easy to see who complies or not.
    """
    reps = [f"EMP{i}" for i in range(123,129)]  # 6 reps
    data = []

    for r in reps:
        # We'll systematically set their booleans so the pattern is clear
        followed_3day = random.choice([True, False])
        personalized = random.choice([True, False])
        closed_30 = random.choice([True, False])
        discount_ok = random.choice([True, False])
        rule5_comply = random.choice([True, False])

        base_revenue = random.randint(20000, 40000)
        if personalized:
            base_revenue = int(base_revenue * 1.2)  # +20%

        data.append({
            "RepID": r,
            "FollowUp3Days": followed_3day,
            "PersonalizedFollowUp": personalized,
            "CloseStaleDeals": closed_30,
            "DiscountUnder10pct": discount_ok,
            "Rule5Compliant": rule5_comply,
            "TotalRevenueThisQuarter": base_revenue
        })

    df = pd.DataFrame(data)
    return df


def generate_dataset_for_d5():
    """
    D5: employee performance
    - 8 reps total (5 big earners + 3 normal)
    - Each has 4 quarters
    - Opportunity volume grows each quarter
    - Win rate drops each quarter
    - 5 big earners: EMP111..EMP555
    - 3 normal: EMP666, EMP777, EMPxyz
    """
    data = []
    reps = ["EMP111","EMP222","EMP333","EMP444","EMP555","EMP666","EMP777","EMPxyz"]

    # We'll keep it simpler with no random variation except small increments
    for rep in reps:
        for q_idx, qtr in enumerate(["Q1","Q2","Q3","Q4"]):
            # baseline deals
            base_deals = 20 + q_idx*5  # Q1=20, Q2=25, Q3=30, Q4=35
            # Win rate from 40% => 35% => 30% => 25%
            base_win_rate = 0.40 - 0.05*q_idx
            closed_won = int(base_deals * base_win_rate)

            # big earners => double revenue
            big_earner_factor = 2.0 if rep in ["EMP111","EMP222","EMP333","EMP444","EMP555"] else 1.0
            total_revenue = int(closed_won * 2000 * big_earner_factor)

            data.append({
                "RepID": rep,
                "Quarter": qtr,
                "TotalDeals": base_deals,
                "ClosedWon": closed_won,
                "TotalRevenue": total_revenue,
                "AvgWinRate": round(base_win_rate*100,2)
            })

    df = pd.DataFrame(data)
    return df
