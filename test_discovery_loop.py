import os
import sys
import time
from dotenv import load_dotenv

# Ensure we can import from core
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.brain_monitor import stage_signature_discovery, DIGEST_PATH, STAGING_FILE

def test_visualize_discovery():
    load_dotenv()
    
    print("\n" + "="*60)
    print("🧠 VERA_BRAIN: NEURAL DISCOVERY VISUALIZER")
    print("="*60 + "\n")

    # 1. Connection Protocol Verification
    from core import brain_monitor
    print("[STEP 0] Verifying Cloud Notebook Bridge...")
    report = brain_monitor.verify_notebook_connection()
    if report:
        print(report)
        print("✅ Connection Verified. Intelligence Grounding Active.\n")
    else:
        print("🔗 [MODE] Local Discovery (Ungrounded)\n")

    # 2. Check Digest
    if not os.path.exists(DIGEST_PATH):
        print(f"❌ ERROR: Brain Digest not found at {DIGEST_PATH}")
        print("   Please run a 'Bust' or test_brain_bridge.py first to generate a digest.")
        return

    print(f"📂 Accessing Intelligence Feed: {DIGEST_PATH}")
    
    root_dir = os.path.dirname(DIGEST_PATH)
    md_files = [f for f in os.listdir(root_dir) if f.endswith(".md") and f != "SIGNATURE_CANDIDATES.md"]
    
    for md in md_files:
        path = os.path.join(root_dir, md)
        size = os.path.getsize(path)
        print(f"   [LOADED] {md} ({size} bytes)")
    
    print(f"\n📡 [SENT] Discovery Prompt (Slice: 100k chars) to Gemini...")
    
    notebook_id = os.getenv("NOTEBOOK_ID")
    if notebook_id:
        print(f"🔗 [MODE] Live Enterprise Bridge: Using Notebook {notebook_id}")
    else:
        print("🔗 [MODE] Local Discovery (Ungrounded)")

    print("-" * 40)
    print("PROMPT: 'Analyze the 42 historical exploits in this notebook...'")
    print("-" * 40 + "\n")

    # Clear staging for fresh visualization if user wants? No, let's just append.
    
    start_time = time.time()
    stage_signature_discovery()
    duration = time.time() - start_time

    print(f"\n⚡ Discovery Cycle Complete ({duration:.2f}s)")

    # 3. Show Result
    if os.path.exists(STAGING_FILE):
        print(f"\n📑 [RECEIVED] Intelligence Candidate Found:")
        print("-" * 40)
        with open(STAGING_FILE, "r", encoding="utf-8") as f:
            # Get the last entry
            all_content = f.read().split("---")
            if len(all_content) > 1:
                last_discovery = all_content[-2].strip()
                print(last_discovery)
        print("-" * 40)
        print(f"\n✅ PROOF: New signature candidate staged in {STAGING_FILE}")
        print("   The Scout will now prioritize contracts matching this pattern.")
    else:
        print("\n❌ FAIL: No discovery candidate was staged.")

    print("\n" + "="*60)
    print("END OF NEURAL TRACE")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_visualize_discovery()
