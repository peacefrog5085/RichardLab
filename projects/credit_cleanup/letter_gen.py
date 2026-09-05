import json
from pathlib import Path

def generate_validation_letter(account_name):
    # Load profile and account data
    profile = json.loads(Path("projects/credit_cleanup/data/profile.json").read_text())
    data = json.loads(Path("projects/credit_cleanup/data/credit_data.json").read_text())
    
    # Find account details
    account = next((a for a in data["accounts"] if a["name"] == account_name), None)
    if not account:
        return "Account not found."

    # Letter template
    letter = f"""
From:
{profile['full_name']}
{profile['address']}
Phone: {profile['phone']}

Date: [Insert Date]

To:
[Insert Collection Agency Address]

RE: Debt Validation for Account: {account['name']}
Account Reference: [Insert Reference Number if known]

To Whom It May Concern,

I am writing to formally request validation of the alleged debt listed above, pursuant to the Fair Debt Collection Practices Act (FDCPA), 15 U.S.C. § 1692g.

Please provide the following information:
1. Proof that I have a contractual obligation to pay this alleged debt.
2. A detailed breakdown of the alleged debt, including the original creditor and the calculation of the current balance.
3. Proof that you are licensed to collect debts in my state of residence.

If you cannot provide this information, I request that you immediately remove this entry from my credit report and cease all collection attempts.

Sincerely,

{profile['full_name']}
"""
    return letter

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(generate_validation_letter(sys.argv[1]))
    else:
        print("Usage: python3 projects/credit_cleanup/letter_gen.py '<account_name>'")
