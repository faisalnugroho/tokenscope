#!/usr/bin/env python3
"""Verify the dApp write-path tx (submitted from browser burner wallet)
using genlayer_py — full receipt with consensus_data, then read back
on-chain state to prove the report landed."""
import json
import sys
import time
from pathlib import Path

from genlayer_py import create_client, create_account
from genlayer_py.chains import studionet
from genlayer_py.types import TransactionStatus

kd = json.loads((Path(__file__).parent / ".deployer.json").read_text())
account = create_account(account_private_key=kd["private_key"])
client = create_client(chain=studionet, account=account)

TX = "0x95c703a332c3f1333d0e14956956dd77c25c16aaa7ece8687be0cd0a171e0df1"
CONTRACT_ADDR = "0xb99689391dEC3322911cf06aE2697D7047D42bF6"
USDT = ("1", "0xdAC17F958D2ee523a2206206994597C13D831ec7")

receipt = None
for attempt in range(6):
    receipt = client.wait_for_transaction_receipt(
        transaction_hash=TX,
        status=TransactionStatus.FINALIZED,
        retries=30, interval=2000, full_transaction=True)
    if receipt:
        break
    time.sleep(5)

if not receipt:
    print("NO RECEIPT — tx not finalized or not found")
    sys.exit(1)

print("== receipt keys:", sorted(receipt.keys()))
vote = receipt.get("result_name")
print("result_name:", vote)
cd = receipt.get("consensus_data") or {}
votes = cd.get("votes")
print("votes:", votes)
lr = (cd.get("leader_receipt") or [{}])[0]
print("leader execution_result:", lr.get("execution_result"))
eq = cd.get("equivalence_principle")
if eq:
    print("equivalence:", json.dumps(eq)[:400])

# read back on-chain state: latest USDT report
raw = client.read_contract(address=CONTRACT_ADDR,
                          function_name="get_latest_for", args=list(USDT))
d = json.loads(raw if isinstance(raw, str) else raw[0])
print("\n== latest USDT report:", json.dumps(d, indent=1)[:800])

count = client.read_contract(address=CONTRACT_ADDR,
                             function_name="get_analysis_count")
print("analysis_count:", count)
