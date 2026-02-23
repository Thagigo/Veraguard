import sys
import os

# Mock the environment
os.environ["BOT_TOKEN"] = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
os.environ["ADMIN_TELEGRAM_ID"] = "7695994098"

# Add project root to sys.path
sys.path.append(os.getcwd())

try:
    from core import main, auth, scout, brain_sync
    import json

    def debug_status():
        print("Debugging get_brain_status logic...")
        
        # Mock user_data
        user_data = {"id": 7695994098, "first_name": "Admin"}
        
        # 1. auth.log_intrusion
        auth.log_intrusion(user_data)
        
        # 2. Signature count
        staged_count = 0
        try:
            print(f"Opening staging file: {brain_sync.brain.staging_file}")
            with open(brain_sync.brain.staging_file, "r") as f:
                content = f.read()
                staged_count = content.count("## [New Signature Candidate]")
            print(f"Staged count: {staged_count}")
        except FileNotFoundError:
            print("Staging file not found, count = 0")
            staged_count = 0
        except Exception as e:
            print(f"Error reading staging file: {e}")
            raise e

        # 3. Scout stats
        results = {
            "scout_budget": round(scout.scout.daily_budget, 2),
            "scout_spend": round(scout.scout.current_spend, 2),
            "staged_signatures": staged_count,
            "vault_solvency": "SOLVENT",
            "status": "OPERATIONAL",
            "admin_user": user_data.get("first_name", "Admin")
        }
        print(f"Success! Results: {results}")

    if __name__ == "__main__":
        debug_status()

except Exception as e:
    import traceback
    print("\n--- STACKTRACE ---")
    traceback.print_exc()
    sys.exit(1)
