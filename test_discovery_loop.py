import os
import sys
import time
from dotenv import load_dotenv

# Ensure we can import from core
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.brain_monitor import stage_signature_discovery, verify_notebook_connection, DIGEST_PATH, STAGING_FILE

def test_visualize_discovery():
    load_dotenv(override=True)

    print("\n" + "="*60)
    print("### VERA_BRAIN: NEURAL DISCOVERY VISUALIZER ###")
    print("="*60 + "\n")

    # 1. Verify Cloud Notebook Bridge
    notebook_id = os.getenv("NOTEBOOK_ID")

    if not notebook_id:
        raise RuntimeError(
            "[FAIL] NOTEBOOK_ID is not set in .env.\n"
            "   Grounded Cloud is required. Set NOTEBOOK_ID and restart.\n"
            "   Per spec: 'the script should throw an error, not pretend to work.'"
        )

    print(f"[LINK] [MODE] Grounded Cloud: Using Notebook {notebook_id}")
    print()

    print("[STEP 0] Verifying Cloud Notebook Bridge...")
    report = verify_notebook_connection()
    if report:
        print(report)
        print("[PASS] Connection Verified. Intelligence Grounding Active.\n")
    else:
        raise RuntimeError("[FAIL] Cloud Notebook connection returned no data. Check NOTEBOOK_ID.")

    # 2. Check Digest
    if not os.path.exists(DIGEST_PATH):
        print(f"[FAIL] [ERROR] Brain Digest not found at {DIGEST_PATH}")
        print("   Please run a 'Bust' or test_brain_bridge.py first to generate a digest.")
        return

    print(f"[FILE] Accessing Intelligence Feed: {DIGEST_PATH}")

    root_dir = os.path.dirname(DIGEST_PATH)
    md_files = [f for f in os.listdir(root_dir) if f.endswith(".md") and f != "SIGNATURE_CANDIDATES.md"]

    for md in md_files:
        path = os.path.join(root_dir, md)
        size = os.path.getsize(path)
        print(f"   [LOADED] {md} ({size} bytes)")

    print(f"\n[SEND] Discovery Prompt (Slice: 100k chars) to Cloud Notebook {notebook_id}...")
    print("-" * 40)
    print("PROMPT: 'Analyze the 42 historical exploits in this notebook...'")
    print("-" * 40 + "\n")

    start_time = time.time()
    stage_signature_discovery()
    duration = time.time() - start_time

    print(f"\n[DONE] Discovery Cycle Complete ({duration:.2f}s)")

    # Verify duration criterion
    if duration > 3:
        print(f"[PASS] Duration {duration:.2f}s > 3s (Cloud synthesis confirmed)")
    else:
        print(f"[FAIL] Duration {duration:.2f}s is NOT > 3s")

    # 3. Show Result
    if os.path.exists(STAGING_FILE):
        print(f"\n[RECV] Intelligence Candidate Found:")
        print("-" * 40)
        with open(STAGING_FILE, "r", encoding="utf-8") as f:
            all_content = f.read().split("---")
            if len(all_content) > 1:
                last_discovery = all_content[-2].strip()
                print(last_discovery)
        print("-" * 40)
        print(f"\n[PASS] [PROOF] New signature candidate staged in {STAGING_FILE}")
    else:
        print("\n[FAIL] No discovery candidate was staged.")

    print("\n" + "="*60)
    print("VAULT: UNLOCKED | BRAIN: GROUNDED")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_visualize_discovery()

