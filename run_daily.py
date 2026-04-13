from src.utils.telegram import send_alert
import subprocess
import sys

steps = [
    ("Refresh stock data", f"{sys.executable} src/test_portfolio_data.py"),
    ("Run predictions", f"{sys.executable} src/run_predictions.py"),
    ("Update Database", f"{sys.executable} src/update_db.py"),
    ("Evaluate predictions", f"{sys.executable} src/evaluate_predictions.py"),
    ("Show summary stats", f"{sys.executable} src/summary_stats.py"),
]
]

for step_name, command in steps:
    print(f"\n--- {step_name} ---")
    result = subprocess.run(command, shell=True)

    if result.returncode != 0:
        print(f"\nStep failed: {step_name}")
        sys.exit(1)

print("\nAll daily steps completed.")