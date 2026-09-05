#!/usr/bin/env python3
import json
import sys
from pathlib import Path

# Add the root directory to the path so we can import from ai/
LAB_ROOT = Path.home() / "RichardLab"
sys.path.append(str(LAB_ROOT))

from ai.gateway import load_config, ask_model

def analyze_credit_status():
    data_path = LAB_ROOT / "projects" / "credit_cleanup" / "data"
    
    with open(data_path / "credit_data.json", "r") as f:
        credit_data = json.load(f)
    with open(data_path / "recovery_plan.json", "r") as f:
        recovery_plan = json.load(f)
    
    config = load_config()
    
    prompt = f"""
You are the RichardLab AI Analyst.
Analyze the following credit cleanup data and provide a proactive recommendation for the next step.

CREDIT DATA:
{json.dumps(credit_data, indent=2)}

RECOVERY PLAN STATUS:
{json.dumps(recovery_plan, indent=2)}

Provide a concise, numbered list of actionable recommendations. 
Focus on accounts with "Not Started" status, prioritizing Collections over Charge-offs.
"""
    
    print("AI Analyst: Processing...")
    result, elapsed = ask_model(config, prompt)
    
    print("\n--- AI RECOMMENDATION ---")
    print(result.get("response", "").strip())
    print("\n(Processing time: {:.2f}s)".format(elapsed))

if __name__ == "__main__":
    analyze_credit_status()
