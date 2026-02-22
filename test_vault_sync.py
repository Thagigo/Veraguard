import sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from core import database as db
from core.synapse_worker import generate_neuron_packet, push_to_brain

db.init_db()

pending = db.get_pending_synapse_syncs()
print(f"\n[VAULT TEST] {len(pending)} reports queued for synapse sync.")

if not pending:
    print("[OK] Nothing pending - all synced already.")
    sys.exit(0)

BATCH = min(5, len(pending))
print(f"[VAULT TEST] Processing first {BATCH} reports...\n")

for r in pending[:BATCH]:
    packet = generate_neuron_packet(r)
    push_to_brain(packet)          # writes to NotebookLM/The_Vault/
    db.mark_synapse_synced(r[0])   # marks DB as synced
    db.increment_neurons_active()  # bumps Neurons Active counter on dashboard
    print(f"  [OK] {packet['synapse_id']}  |  exploit={packet['exploit_vector']}  |  score={packet['vera_score']}")

vault = os.path.join("NotebookLM", "The_Vault")
files = [f for f in os.listdir(vault) if f.startswith("Neuron_Packet")]
print(f"\n[VAULT TEST] Done. {len(files)} Neuron Packet(s) now in {vault}/")
for f in sorted(files):
    print(f"  {f}")
