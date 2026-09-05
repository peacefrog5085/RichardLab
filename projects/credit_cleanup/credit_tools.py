#!/usr/bin/env python3

import json
import sys
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent / "data" / "credit_data.json"

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def list_accounts():
    data = load_data()
    print("\n--- ACCOUNTS ---")
    print(f"{'Name':<30} | {'Status':<15} | {'Balance':<10}")
    print("-" * 60)
    for acc in data["accounts"]:
        print(f"{acc['name']:<30} | {acc['status']:<15} | ${acc['balance']:<10}")

def list_inquiries():
    data = load_data()
    print("\n--- INQUIRIES ---")
    print(f"{'Creditor':<30} | {'Date':<15}")
    print("-" * 50)
    for inq in data["inquiries"]:
        print(f"{inq['creditor']:<30} | {inq['date']:<15}")

def list_recovery_plan():
    PLAN_FILE = Path(__file__).resolve().parent / "data" / "recovery_plan.json"
    with open(PLAN_FILE, "r") as f:
        data = json.load(f)
    print("\n--- RECOVERY PLAN ---")
    print(f"{'Account':<30} | {'Status':<15} | {'Notes'}")
    print("-" * 80)
    for disp in data["disputes"]:
        print(f"{disp['account']:<30} | {disp['status']:<15} | {disp.get('notes', '')}")

def update_dispute(account_name, new_status, new_notes):
    from datetime import datetime
    PLAN_FILE = Path(__file__).resolve().parent / "data" / "recovery_plan.json"
    with open(PLAN_FILE, "r") as f:
        data = json.load(f)
    
    for disp in data["disputes"]:
        if disp["account"] == account_name:
            disp["status"] = new_status
            disp["notes"] = new_notes
            disp["last_updated"] = datetime.now().strftime("%Y-%m-%d")
            break
    
    with open(PLAN_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Updated {account_name}.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "accounts":
            list_accounts()
        elif sys.argv[1] == "inquiries":
            list_inquiries()
        elif sys.argv[1] == "recovery":
            list_recovery_plan()
        elif sys.argv[1] == "update":
            update_dispute(sys.argv[2], sys.argv[3], sys.argv[4])
