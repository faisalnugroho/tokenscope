#!/usr/bin/env python3
"""Diagnose LLM classification wobble: run analyze() leader_only N times
against a live target and diff the canonical results. This samples the
same distribution the validators draw from — any capability that wobbles
across runs is a consensus hazard and needs a sharper taxonomy
definition in the prompt.
"""
import json
import sys
from pathlib import Path

from genlayer_py import create_client, create_account
from genlayer_py.chains import studionet
from genlayer_py.types import TransactionStatus

ROOT = Path(__file__).resolve().parents[1]

keyfile = Path(__file__).parent / ".deployer.json"
kd = json.loads(keyfile.read_text())
account = create_account(account_private_key=kd["private_key"])
client = create_client(chain=studionet, account=account)

CONTRACT = sys.argv[1] if len(sys.argv) > 1 else None
if not CONTRACT:
    log = json.loads((ROOT / "docs" / "deployment_log.json").read_text())
    CONTRACT = log["deploy"]["address"]
CHAIN = sys.argv[2] if len(sys.argv) > 2 else "1"
ADDR = sys.argv[3] if len(sys.argv) > 3 else \
    "0xdAC17F958D2ee523a2206206994597C13D831ec7"
N = int(sys.argv[4]) if len(sys.argv) > 4 else 3

print(f"contract {CONTRACT}\ntarget {CHAIN}:{ADDR}\nruns {N}\n")


def one_run(i):
    tx = client.write_contract(address=CONTRACT, function_name="analyze",
                               args=[CHAIN, ADDR], account=account,
                               leader_only=True)
    receipt = client.wait_for_transaction_receipt(
        transaction_hash=tx, status=TransactionStatus.FINALIZED,
        retries=100, interval=3000, full_transaction=True)
    lead = receipt["consensus_data"]["leader_receipt"][0]
    readable = lead["result"]["payload"]["readable"]
    # analyze returns report_id; but the eq_outputs[0] carries the
    # full canonical pipeline result
    eq = lead.get("eq_outputs", {}).get("0", {})
    full = eq.get("payload", {}).get("readable", "")
    rid = readable.strip('"')
    rep_raw = client.read_contract(address=CONTRACT,
                                   function_name="get_report",
                                   args=[rid])
    rep = json.loads(rep_raw if isinstance(rep_raw, str) else rep_raw[0])
    print(f"--- run {i}: report {rid}")
    return rep


reps = [one_run(i) for i in range(N)]

# diff capability statuses across runs
print("\n=== capability status across runs ===")
caps = reps[0]["capabilities"]
wobble = []
for cap in sorted(caps):
    sts = [r["capabilities"][cap]["status"] for r in reps]
    flag = "" if len(set(sts)) == 1 else "   <-- WOBBLE"
    if flag:
        wobble.append(cap)
    print(f"{cap:28s} {sts}{flag}")

print("\nsource_status:", [r["source_status"] for r in reps])
print("analysis_status:", [r["analysis_status"] for r in reps])
print("\nWOBBLING CAPS:", wobble if wobble else "none — stable")
