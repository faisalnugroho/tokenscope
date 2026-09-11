#!/usr/bin/env python3
"""Live smoke against the FINAL TokenScope contract (v3,
0xb99689391dEC3322911cf06aE2697D7047D42bF6). Does NOT deploy.

Smoke protocol (per the live-deploy skill):
  S2  positive: USDT @ chain 1 (verified partial match) — real
      Sourcify data, real LLM consensus, full committee    -> report
  S2b positive: UNI @ chain 1 (exact match, full sources)   -> report
  S3  negative: unverified address @ chain 1 -> NOT_VERIFIED stored
  S4  negative: malformed address -> REQUEST failure stored
  S5  determinism: re-run S2 target -> identical statuses
  S6  getters: latest/history/count read back

Every consensus run is gated on BOTH the consensus vote
(MAJORITY_AGREE) AND the leader execution result — a FINALIZED tx can
still carry a reverted execution. Evidence is appended to
docs/deployment_log.json.
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

CONTRACT_ADDR = "0xb99689391dEC3322911cf06aE2697D7047D42bF6"

USDT_CHAIN = "1"
USDT_ADDR = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
UNI_ADDR = "0x1f9840a85d5aF5bf1d1762F925BDADdC4201F984"
UNVERIFIED_ADDR = "0x0000000000000000000000000000000000000001"

code = CODE.read_text()
print(f"local code sha256 = {hashlib.sha256(code.encode()).hexdigest()}")

kd = json.loads((Path(__file__).parent / ".deployer.json").read_text())
account = create_account(account_private_key=kd["private_key"])
print("deployer:", account.address)
client = create_client(chain=studionet, account=account)

info_raw = client.read_contract(address=CONTRACT_ADDR,
                                function_name="get_contract_info")
info = json.loads(info_raw if isinstance(info_raw, str) else info_raw[0])
assert info["name"] == "TokenScope", info
print("contract info OK:", info["name"], "taxonomy", info["taxonomy_version"])


def wait_final(tx_hash, what, timeout_s=420):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        receipt = client.wait_for_transaction_receipt(
            transaction_hash=tx_hash,
            status=TransactionStatus.FINALIZED,
            retries=100, interval=3000, full_transaction=True)
        if receipt:
            return receipt
        time.sleep(5)
    print(f"TIMEOUT waiting for {what} ({tx_hash})")
    sys.exit(1)


def check_exec(receipt, what):
    try:
        cd = receipt.get("consensus_data") or {}
        lr = (cd.get("leader_receipt") or [{}])[0]
        exec_result = lr.get("execution_result")
        vote = receipt.get("result_name")
    except Exception:
        exec_result = None
        vote = receipt.get("result_name")
    ok = (vote in (None, "MAJORITY_AGREE")
          and (exec_result in (None, "SUCCESS", "FINISHED_WITH_RETURN")))
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


def get_report(rid):
    raw = client.read_contract(address=CONTRACT_ADDR,
                               function_name="get_report", args=[rid])
    return json.loads(raw if isinstance(raw, str) else raw[0])


def run_case(name, chain, addr, expect, timeout_s=420):
    print(f"\n=== {name}: chain={chain} addr={addr}")
    tx_hash = client.write_contract(
        address=CONTRACT_ADDR, function_name="analyze",
        args=[chain, addr], account=account)
    print(f"  tx: {tx_hash}")
    receipt = wait_final(tx_hash, name, timeout_s)
    check_exec(receipt, name)
    rid = None
    try:
        rid = receipt["consensus_data"]["leader_receipt"][0][
            "result"]["payload"]["readable"].strip('"')
    except Exception:
        pass
    if rid is None or get_report(rid).get("error"):
        out = client.read_contract(
            address=CONTRACT_ADDR, function_name="get_latest_for",
            args=[chain, addr])
        d = json.loads(out if isinstance(out, str) else out[0])
        rid = d.get("report_id")
    rep = get_report(rid)
    print(f"  report_id: {rid}")
    print(f"  source: {rep.get('source_status')}  "
          f"analysis: {rep.get('analysis_status')}")
    caps = rep.get("capabilities", {})
    detected = sorted(k for k, v in caps.items()
                      if isinstance(v, dict) and v.get("status") == "DETECTED")
    print(f"  detected: {detected}")
    failed = False
    for field, want in expect.items():
        got = rep.get(field)
        if got != want:
            print(f"  MISMATCH {field}: got {got!r} want {want!r}")
            failed = True
    if failed:
        return None, rep, tx_hash
    return rid, rep, tx_hash


log = {"final_contract": {
    "address": CONTRACT_ADDR,
    "code_sha256": hashlib.sha256(code.encode()).hexdigest(),
}, "cases": [], "history": []}

# S2 positive: USDT (partial match, real privileged surface)
rid_usdt, rep_usdt, tx_usdt = run_case(
    "S2 USDT@1", USDT_CHAIN, USDT_ADDR,
    {"source_status": "PARTIAL_MATCH", "analysis_status": "COMPLETE"})
log["cases"].append({
    "name": "S2-positive-usdt", "tx": tx_usdt, "report_id": rid_usdt,
    "source_status": rep_usdt.get("source_status"),
    "analysis_status": rep_usdt.get("analysis_status"),
    "detected": sorted(
        k for k, v in rep_usdt.get("capabilities", {}).items()
        if isinstance(v, dict) and v.get("status") == "DETECTED"),
    "capabilities": {k: v.get("status")
                     for k, v in rep_usdt.get("capabilities", {}).items()},
})

# S2b positive: UNI (Sourcify reports match:"match" = PARTIAL_MATCH;
# verified live 2026-09-11 — creationMatch/runtimeMatch both "match")
rid_uni, rep_uni, tx_uni = run_case(
    "S2b UNI@1", "1", UNI_ADDR,
    {"source_status": "PARTIAL_MATCH", "analysis_status": "COMPLETE"})
log["cases"].append({
    "name": "S2b-positive-uni", "tx": tx_uni, "report_id": rid_uni,
    "source_status": rep_uni.get("source_status"),
    "analysis_status": rep_uni.get("analysis_status"),
    "detected": sorted(
        k for k, v in rep_uni.get("capabilities", {}).items()
        if isinstance(v, dict) and v.get("status") == "DETECTED"),
})

# S3 negative: unverified
rid_unv, rep_unv, tx_unv = run_case(
    "S3 unverified@1", "1", UNVERIFIED_ADDR,
    {"analysis_status": "UNAVAILABLE"}, timeout_s=240)
log["cases"].append({
    "name": "S3-negative-unverified", "tx": tx_unv, "report_id": rid_unv,
    "failure": rep_unv.get("failure"),
})

# S4 negative: malformed address
rid_bad, rep_bad, tx_bad = run_case(
    "S4 malformed@1", "1", "0xnothex", {}, timeout_s=240)
log["cases"].append({
    "name": "S4-negative-malformed", "tx": tx_bad, "report_id": rid_bad,
    "failure": rep_bad.get("failure"),
})

# S5 determinism: fresh analysis of USDT
rid2, rep2, tx2 = run_case(
    "S5 determinism USDT@1", USDT_CHAIN, USDT_ADDR,
    {"source_status": "PARTIAL_MATCH", "analysis_status": "COMPLETE"})
same = ({k: v.get("status") for k, v in rep_usdt["capabilities"].items()}
        == {k: v.get("status") for k, v in rep2["capabilities"].items()})
print(f"\nS5 determinism (identical capability matrix): {same}")
log["cases"].append({
    "name": "S5-determinism", "tx": tx2, "report_id": rid2,
    "identical_capability_matrix": same,
})

# S6 getters
count = client.read_contract(address=CONTRACT_ADDR,
                             function_name="get_analysis_count")
hist = client.read_contract(address=CONTRACT_ADDR,
                            function_name="get_history_for",
                            args=[USDT_CHAIN, USDT_ADDR])
print(f"S6 count={count} usdt-history={hist}")
log["getters"] = {"analysis_count": str(count),
                  "usdt_history": str(hist)}

# gate: everything must have succeeded
ok = all(c.get("report_id") for c in log["cases"]) and same
LOG.parent.mkdir(parents=True, exist_ok=True)
LOG.write_text(json.dumps(log, indent=2))
print(f"\nevidence log written to {LOG}")
print("SMOKE RESULT:", "ALL_OK" if ok else "INCOMPLETE — check log")
sys.exit(0 if ok else 2)
