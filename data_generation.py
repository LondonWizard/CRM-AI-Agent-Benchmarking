from dotenv import load_dotenv
import os
import random
import numpy as np
import pandas as pd

def generate_synthetic_crm_data(seed=42):
    """
    Generates a synthetic CRM dataset with clear, unambiguous patterns
    for 10 employees. Also generates some simple example email threads.

    Writes data to:
      - employees.csv    (employee-specific info)
      - deals.csv        (deal-specific CRM metrics)
      - emails.csv       (simple synthetic email threads)
    """
    random.seed(seed)
    np.random.seed(seed)

    # Ten employees (exactly 10)
    employees = [
        "Alice", "Bob", "Charlie", "Diana", "Ethan", 
        "Fiona", "George", "Hannah", "Irene", "Jack"
    ]
    employees.sort()  # consistent ordering

    # Generate random data for deals
    num_employees = 10
    
    base_deals = np.random.randint(10, 40, size=num_employees)
    base_revenue = np.random.randint(10000, 90000, size=num_employees)
    base_conversion = np.random.uniform(0.10, 0.40, size=num_employees)
    base_cycle = np.random.randint(20, 50, size=num_employees)
    
    # Force unambiguous patterns (like the original concept):
    # - The first employee gets the highest deals & revenue
    # - The second employee has the best conversion
    # - The third has the fastest sales cycle
    base_deals[0] = max(base_deals) + 20
    base_revenue[0] = max(base_revenue) + 30000
    base_conversion[1] = max(base_conversion) + 0.10
    base_cycle[2] = min(base_cycle) - 10
    if base_cycle[2] < 1:
        base_cycle[2] = 1
    
    # Some extra columns for demonstration
    regions = ["North", "South", "East", "West"]
    # Assign each employee a region and maybe a department
    departments = ["Sales", "Marketing", "Support"]
    assigned_regions = [random.choice(regions) for _ in employees]
    assigned_departments = [random.choice(departments) for _ in employees]

    # Create employees dataframe
    df_employees = pd.DataFrame({
        "employee_name": employees,
        "region": assigned_regions,
        "department": assigned_departments
    })

    # Create deals dataframe
    df_deals = pd.DataFrame({
        "employee_name": employees,
        "total_deals": base_deals,
        "total_revenue": base_revenue,
        "conversion_rate": base_conversion,
        "average_sale_cycle_days": base_cycle
    })

    # Generate synthetic emails: for demonstration,
    # each employee has 1-2 "threads" with random content
    email_rows = []
    subjects = [
        "Follow-up on Q3 report",
        "Status update on leads",
        "Meeting schedule",
        "Budget discussion",
        "Client Onboarding"
    ]
    for emp in employees:
        num_threads = np.random.randint(1, 3)
        for i in range(num_threads):
            subj = random.choice(subjects)
            body = (
                f"Hello team,\n\n"
                f"This is a synthetic email thread about '{subj}'. "
                f"Employee {emp} is discussing possible actions.\n\n"
                f"Best regards,\nSynthetic System"
            )
            email_rows.append({
                "employee_name": emp,
                "email_subject": subj,
                "email_body": body
            })
    df_emails = pd.DataFrame(email_rows)

    # Write CSVs
    df_employees.to_csv("employees.csv", index=False)
    df_deals.to_csv("deals.csv", index=False)
    df_emails.to_csv("emails.csv", index=False)

if __name__ == "__main__":
    load_dotenv()
    # Generate the CSV files
    generate_synthetic_crm_data()
    print("Synthetic CSV files generated: employees.csv, deals.csv, emails.csv.")
