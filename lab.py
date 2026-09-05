#!/usr/bin/env python3
import sys
import subprocess
import json
from pathlib import Path

# Add RichardLab root to sys.path so absolute imports work from anywhere
LAB_ROOT = Path(__file__).resolve().parent
sys.path.append(str(LAB_ROOT))

from ai.gateway import load_config, ask_model

def main():
    print("╔══════════════════════════════════════════════════════╗")
    print("║                   RICHARDLAB GATEWAY                 ║")
    print("╚══════════════════════════════════════════════════════╝")
    intent = input("\nWhat is our goal today? ")
    
    if not intent.strip():
        print("No intent provided. Exiting.")
        return

    print(f"\nProcessing intent: '{intent}'...")
    
    # 1. Use AI to categorize the intent
    config = load_config()
    prompt = f"""
Analyze the user's intent: '{intent}'
Respond ONLY with one of these keywords: 'credit_cleanup', 'system_status', 'forensics', 'experiment', 'unknown'.
"""
    result, _ = ask_model(config, prompt)
    category = result.get("response", "").strip().lower()

    print(f"Routing to: {category}")

    # 2. Route to the appropriate tool or project
    try:
        if "credit_cleanup" in category:
            subprocess.run([str(LAB_ROOT / "projects" / "credit_cleanup" / "control.sh")])
        elif "system_status" in category:
            subprocess.run([str(LAB_ROOT / "dashboard" / "lab.sh")])
        elif "experiment" in category:
            subprocess.run([str(LAB_ROOT / "mission_control" / "experiment_center.sh")])
        elif "forensics" in category:
            # Forensics is currently inside lab.sh, could be refactored later
            subprocess.run([str(LAB_ROOT / "dashboard" / "lab.sh")])
        else:
            print(f"I'm not sure how to handle '{category}' yet.")
    except Exception as e:
        print(f"Error executing module: {e}")

if __name__ == "__main__":
    main()
