import csv
import random
from datetime import datetime, timedelta
import os

def random_date(start, end):
    """Generate a random datetime between `start` and `end`"""
    delta = end - start
    int_delta = int(delta.total_seconds())
    random_second = random.randint(0, int_delta)
    return start + timedelta(seconds=random_second)

def generate_transactions(num_transactions=20000):
    csv_path = os.path.join(os.path.dirname(__file__), "transactions.csv")
    start_date = datetime(2024, 1, 1, 0, 0, 0)
    end_date = datetime(2024, 12, 31, 23, 59, 59)
    
    with open(csv_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Timestamp', 'Amount (INR)'])
        
        # Generate normal transactions (97% of total)
        normal_count = int(num_transactions * 0.97)
        for _ in range(normal_count):
            dt = random_date(start_date, end_date)
            # Normal transactions: mostly between 100 and 5000 INR
            amount = round(random.normalvariate(2500, 1000), 2)
            amount = max(100, min(amount, 5000))  # Clip to reasonable range
            writer.writerow([dt.strftime('%Y-%m-%d %H:%M:%S'), amount])
        
        # Generate fraudulent transactions (3% of total)
        fraud_count = num_transactions - normal_count
        for _ in range(fraud_count):
            dt = random_date(start_date, end_date)
            # Fraudulent transactions: unusually high amounts
            amount = round(random.uniform(8000, 50000), 2)
            writer.writerow([dt.strftime('%Y-%m-%d %H:%M:%S'), amount])

    import pandas as pd
    return pd.read_csv(csv_path)

if __name__ == "__main__":
    generate_transactions()
