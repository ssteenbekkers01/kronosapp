from src.utils.telegram import send_alert
import subprocess
import sys

steps = [
    ("Refresh stock data", "python src/test_portfolio_data.py"),
    ("Run predictions", "python src/run_predictions.py"),
    ("Update Database", "python src/update_db.py"),
    ("Evaluate predictions", "python -m src.evaluate_predictions"),
    ("Show summary stats", "python src/summary_stats.py"),
]

for step_name, command in steps:
    print(f"\n--- {step_name} ---")
    result = subprocess.run(command, shell=True)

    if result.returncode != 0:
        print(f"\nStep failed: {step_name}")
        sys.exit(1)

print("\nAll daily steps completed.")