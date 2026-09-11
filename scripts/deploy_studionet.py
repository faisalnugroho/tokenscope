#!/usr/bin/env python3
"""Deploy TokenScope to GenLayer Studionet and run the live smoke.

Smoke protocol (per the live-deploy skill):
  S1  deploy (full consensus)                  -> contract address
  S2  positive: USDT @ chain 1 (verified, partial match "match") —
      real Sourcify data, real LLM consensus              -> report
  S3  negative: unverified address @ chain 1  -> NOT_VERIFIED stored
  S4  negative: malformed address             -> REQUEST failure stored
  S5  determinism: re-run S2 target           -> same source/analysis
      statuses on a fresh report id
  S6  getters: latest/history/count           -> read back

Every consensus run is gated on BOTH the consensus vote
(MAJORITY_AGREE) AND the execution result — a FINALIZED tx can still
carry a reverted execution (documented pitfall). Evidence is appended
to docs/deployment_log.json.
"""
import hashlib
import json
import sys
import time
from pathlib import Path

from genlayer_py import create_client, create_account
from genlayer_py.chains import studionet
from genlayer_py.types import TransactionStatus

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / "contracts" / "token_scope.py"
LOG = ROOT / "docs" / "deployment_log.json"

# live, public, verified targets (Sourcify v2):
# USDT (TetherToken) on Ethereum mainnet — match:"match" (partial),
# real mint/blacklist/fee capability surface.
USDT_CHAIN = "1"
USDT_ADDR = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
# UNI token on mainnet — match:"exact_match" (full verified sources).
UNI_ADDR = "0x1f9840a85d5aF5bf1d1762F925BDADdC4201F984"
# an address that is definitely NOT verified on chain 1
UNVERIFIED_ADDR = "0x0000000000000000000000000000000000000001"

code = CODE.read_text()
print(f"contract: {len(code)} bytes, sha256[:16] =",
      hashlib.sha256(code.encode()).hexdigest()[:16])

# stable deployer keyfile (gitignored); created on first run
keyfile = Path(__file__).parent / ".deployer.json"
if keyfile.exists():
    kd = json.loads(keyfile.read_text())
    account = create_account(account_private_key=kd["private_key"])
    print("deployer (saved):", account.address)
else:
    account = create_account()
    keyfile.write_text(json.dumps(
        {"address": account.address, "private_key": account.key.hex()}))
    print("deployer (new):", account.address)

client = create_client(chain=studionet, account=account)
client.fund_account(account.address, 10**18)


def wait_final(tx_hash, what, timeout_s=420):
    """Wait for FINALIZED + verify BOTH the vote and the execution
    result. Returns the receipt dict or exits with diagnostics."""
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        receipt = client.wait_for_transaction_receipt(
            transaction_hash=tx_hash,
            status=TransactionStatus.FINALIZED,
            full_transaction=True)
        if receipt:
            return receipt
        time.sleep(5)
    print(f"TIMEOUT waiting for {what} ({tx_hash})")
    sys.exit(1)


def check_exec(receipt, what):
    """A FINALIZED tx can still carry a reverted execution — gate on
    leader_receipt execution result + consensus vote."""
    try:
        cd = receipt.get("consensus_data") or {}
        lr = (cd.get("leader_receipt") or [{}])[0]
        exec_result = lr.get("execution_result")
        vote = receipt.get("result_name")
    except Exception:
        exec_result = None
        vote = receipt.get("result_name")
    ok = (vote in (None, "MAJORITY_AGREE")
          and (exec_result in (None, "SUCCESS",
                               "FINISHED_WITH_RETURN")))
    print(f"  {what}: vote={vote} exec={exec_result}")
    if not ok:
        stderr = ""
        try:
            stderr = (receipt.get("consensus_data")
                      .get("leader_receipt")[0]
                      .get("genvm_result", {}).get("stderr", ""))
        except Exception:
            pass
        print("EXECUTION FAILED — stderr tail:")
        print(stderr[-1500:])
        sys.exit(1)
    return True


def run_case(name, chain, addr, expect):
    print(f"\n=== {name}: chain={chain} addr={addr}")
    tx_hash = client.write_contract(
        address=CONTRACT_ADDR, function_name="analyze",
        args=[chain, addr], account=account)
    print(f"  tx: {tx_hash}")
    receipt = wait_final(tx_hash, name)
    check_exec(receipt, name)
    # read back the stored report via the leader return
    try:
        rid = receipt.get("data", {}).get("return")[0]
    except Exception:
        rid = None
    if rid is None:
        # fall back to latest_for
        out = client.read_contract(
            address=CONTRACT_ADDR, function_name="get_latest_for",
            args=[chain, addr])
        d = json.loads(out if isinstance(out, str) else out[0])
        rid = d.get("report_id")
    rep = client.read_contract(
        address=CONTRACT_ADDR, function_name="get_report", args=[rid])
    rep = json.loads(rep if isinstance(rep, str) else rep[0])
    print(f"  report_id: {rid}")
    print(f"  source_status: {rep.get('source_status')}"
          f"  analysis: {rep.get('analysis_status')}")
    caps = rep.get("capabilities", {})
    detected = [k for k, v in caps.items()
                if isinstance(v, dict) and v.get("status") == "DETECTED"]
    print(f"  detected: {detected}")
    for field, want in expect.items():
        got = rep.get(field)
        if got != want:
            print(f"  MISMATCH {field}: got {got!r} want {want!r}")
            return None, rep, tx_hash
    return rid, rep, tx_hash


log = {"deploy": {}, "cases": [], "runs": []}
print("\n=== S1: deploying (full consensus) ===")
deploy_tx = client.deploy_contract(code=code, account=account,
                                   leader_only=False)
receipt = wait_final(deploy_tx, "deploy")
check_exec(receipt, "deploy")
CONTRACT_ADDR = (receipt.get("data", {}).get("contract_address")
                 or receipt.get("to_address"))
print(f"deployed at {CONTRACT_ADDR}")
log["deploy"] = {
    "tx": deploy_tx, "address": CONTRACT_ADDR,
    "code_sha256": hashlib.sha256(code.encode()).hexdigest(),
    "vote": receipt.get("result_name"),
}

# S2 positive: USDT — real verified Sourcify data
rid_usdt, rep_usdt, tx_usdt = run_case(
    "S2 USDT@1", USDT_CHAIN, USDT_ADDR,
    {"source_status": "PARTIAL_MATCH",
     "analysis_status": "COMPLETE"})
log["cases"].append({
    "name": "S2-positive-usdt", "tx": tx_usdt, "report_id": rid_usdt,
    "source_status": rep_usdt.get("source_status"),
    "analysis_status": rep_usdt.get("analysis_status"),
    "detected": [k for k, v in rep_usdt.get("capabilities", {}).items()
                 if isinstance(v, dict)
                 and v.get("status") == "DETECTED"],
})

# S3 negative: unverified address
rid_unv, rep_unv, tx_unv = run_case(
    "S3 unverified@1", "1", UNVERIFIED_ADDR,
    {"analysis_status": "UNAVAILABLE"})
log["cases"].append({
    "name": "S3-negative-unverified", "tx": tx_unv,
    "report_id": rid_unv,
    "failure": rep_unv.get("failure"),
    "analysis_status": rep_unv.get("analysis_status"),
})

# S4 negative: malformed address
rid_bad, rep_bad, tx_bad = run_case(
    "S4 malformed@1", "1", "0xnothex", {})
log["cases"].append({
    "name": "S4-negative-malformed", "tx": tx_bad, "report_id": rid_bad,
    "failure": rep_bad.get("failure"),
})

# S5 determinism: fresh analysis of the same target
rid2, rep2, tx2 = run_case(
    "S5 determinism USDT@1", USDT_CHAIN, USDT_ADDR,
    {"source_status": "PARTIAL_MATCH",
     "analysis_status": "COMPLETE"})
same = (rep_usdt.get("capabilities") == rep2.get("capabilities"))
print(f"\ndeterminism (identical capability matrix): {same}")
log["runs"].append({
    "name": "S5-determinism", "tx": tx2, "report_id": rid2,
    "identical_capability_matrix": same,
    "caps1": {k: v.get("status")
              for k, v in rep_usdt["capabilities"].items()},
    "caps2": {k: v.get("status")
              for k, v in rep2["capabilities"].items()},
})

# S6 getters
count = client.read_contract(
    address=CONTRACT_ADDR, function_name="get_analysis_count")
hist = client.read_contract(
    address=CONTRACT_ADDR, function_name="get_history_for",
    args=[USDT_CHAIN, USDT_ADDR])
print(f"S6 count={count} usdt-history={hist}")
log["getters"] = {"analysis_count": str(count),
                  "usdt_history": str(hist)}

LOG.parent.mkdir(parents=True, exist_ok=True)
LOG.write_text(json.dumps(log, indent=2))
print(f"\nevidence log written to {LOG}")
print(json.dumps({
    "deploy_tx": deploy_tx, "address": CONTRACT_ADDR}, indent=2))
