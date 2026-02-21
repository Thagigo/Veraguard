import asyncio
import json
from web3 import Web3
from websockets.exceptions import ConnectionClosedError
import websockets
import requests
from core.scout import scout

# Using a public wss endpoint for testing/simulation if no private RPC is available.
# In a real scenario, this should be configured in .env
WSS_ENDPOINT = "wss://ethereum-rpc.publicnode.com" 

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
                
                # We need a synchronous Web3 instance or AsyncWeb3 to fetch tx details
                w3 = Web3(Web3.HTTPProvider(WSS_ENDPOINT.replace("wss://", "https://")))
                
                while True:
                    message = await ws.recv()
                    data = json.loads(message)
                    
                    if "params" in data:
                        try:
                            tx_hash = data["params"]["result"]
                        except KeyError:
                            print("[CHAIN LISTENER] Node Lag: Malformed RPC payload, skipping block.")
                            continue
                        
                        try:
                            # Fetch transaction details
                            tx = w3.eth.get_transaction(tx_hash)
                            
                            # If 'to' is None, it's a contract deployment
                            if tx.get('to') is None:
                                # We can't know the exact deployment address before it's mined easily
                                # But for the sake of Veraguard's "triage", we simulate passing the tx_hash or a mock address
                                print(f"[CHAIN LISTENER] ⚡ Contract Deployment Detected! TX: {tx_hash}")
                                
                                # Push to Scout Filter
                                mock_address = f"0xDeployedFrom_{tx_hash[:6]}"
                                print(f"[CHAIN LISTENER] Pushing {mock_address} to Scout Triage...")
                                
                                scout.scan_contract(mock_address)
                                
                                try:
                                    requests.post("http://127.0.0.1:8000/api/internal/live_event", json={"event_type": "contract_detected", "data": {"address": mock_address}})
                                except Exception:
                                    pass
                                
                        except Exception as e:
                            # Transaction might not be available immediately in the mempool via HTTP yet
                            pass
                            
        except ConnectionClosedError:
            print("[CHAIN LISTENER] Connection dropped. Reconnecting in 5s...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"[CHAIN LISTENER] Error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(listen_for_pending_transactions())
    except KeyboardInterrupt:
        print("\n[CHAIN LISTENER] Shutting down.")
