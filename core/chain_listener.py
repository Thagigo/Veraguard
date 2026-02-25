"""
chain_listener.py — On-Chain Contract Deployment Monitor
==========================================================
Subscribes to Ethereum pending transactions via WebSockets.
Flags contract deployments and runs unified triage via audit_engine.
Persists initial suspicion score to the database when score >= 40.
"""
import asyncio
import json
import requests
from web3 import Web3
from websockets.exceptions import ConnectionClosedError
import websockets
import os

from core.audit_engine import triage_address
from core import database
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

WSS_ENDPOINT = os.getenv("RPC_WSS_ENDPOINT", "wss://ethereum-rpc.publicnode.com")
SUSPICION_PERSIST_THRESHOLD = 40   # Save to DB if auto-scan scores >= this


async def listen_for_pending_transactions():
    """
    Subscribes to pending transactions or newHeads to intercept contract creations.
    """
    print(f"[CHAIN LISTENER] Connecting to RPC WebSockets: {WSS_ENDPOINT}")

    while True:
        try:
            async with websockets.connect(WSS_ENDPOINT) as ws:
                # Subscribe to new pending transactions
                await ws.send(json.dumps({
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "eth_subscribe",
                    "params": ["newPendingTransactions"]
                }))

                response = await ws.recv()
                print(f"[CHAIN LISTENER] Subscribed: {response}")

                w3 = Web3(Web3.HTTPProvider(WSS_ENDPOINT.replace("wss://", "https://")))

                while True:
                    message = await ws.recv()
                    data = json.loads(message)

                    if "params" in data:
                        try:
                            tx_hash = data["params"]["result"]
                        except KeyError:
                            print("[CHAIN LISTENER] Node Lag: Malformed RPC payload, skipping.")
                            continue

                        try:
                            tx = w3.eth.get_transaction(tx_hash)

                            # If 'to' is None → contract deployment
                            if tx.get('to') is None:
                                print(f"[CHAIN LISTENER] ⚡ Contract Deployment Detected! TX: {tx_hash}")

                                # Build a representative address from the tx hash
                                mock_address = f"0x{tx_hash[2:42]}"

                                # ── Unified triage (same engine as vera_user) ──
                                result = triage_address(
                                    address=mock_address,
                                    context_text="",
                                    source="chain",
                                )
                                score = result["score"]

                                print(
                                    f"[CHAIN LISTENER] Triage → {score:.0f}% "
                                    f"| deployer_flag={result['deployer_flag']} "
                                    f"| zero_credit={result['zero_credit']}"
                                )

                                # ── Persist initial suspicion if above threshold ──
                                if score >= SUSPICION_PERSIST_THRESHOLD:
                                    saved = database.save_initial_suspicion(
                                        address=mock_address,
                                        score=score,
                                        source="chain",
                                    )
                                    if saved:
                                        print(
                                            f"[CHAIN LISTENER] 💾 Initial suspicion "
                                            f"{score:.0f}% saved for {mock_address[:12]}…"
                                        )

                                # ── Broadcast to Brain UI ──
                                try:
                                    requests.post(
                                        "http://127.0.0.1:8000/api/internal/live_event",
                                        json={
                                            "event_type": "contract_detected",
                                            "data": {
                                                "address":  mock_address,
                                                "score":    round(score),
                                                "source":   "chain",
                                            }
                                        },
                                        timeout=2,
                                    )
                                except Exception:
                                    pass

                        except Exception:
                            # Transaction may not be in pool yet — silently skip
                            pass

        except (ConnectionClosedError, OSError) as e:
            if "WinError 64" in str(e):
                print(f"[CHAIN LISTENER] Network reset (WinError 64) detected. Workspace/VPN likely killed the socket.")
            print(f"[CHAIN LISTENER] Connection error: {e}. Reconnecting in 5s…")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"[CHAIN LISTENER] Unexpected Error: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(listen_for_pending_transactions())
    except KeyboardInterrupt:
        print("\n[CHAIN LISTENER] Shutting down.")
