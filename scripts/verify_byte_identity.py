#!/usr/bin/env python3
"""Verify deployed==repo byte-identity for the FINAL TokenScope
contract from the deploy tx's contract_code (base64 of the entire
deployed source). One-call proof:

    sha256(b64decode(contract_code)) == sha256(contracts/token_scope.py)

Usage: python scripts/verify_byte_identity.py <deploy_tx_hash>
"""
import base64
import hashlib
import json
import sys
import urllib.request

RPC = "https://studio.genlayer.com/api"
CONTRACT = "0xb99689391dEC3322911cf06aE2697D7047D42bF6"
LOCAL = "contracts/token_scope.py"


def rpc(method, params):
    body = json.dumps({"method": method, "params": params,
                       "jsonrpc": "2.0", "id": 1}).encode()
    req = urllib.request.Request(
        RPC, data=body,
        headers={"Content-Type": "application/json",
                 "User-Agent": "curl/8.5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def main():
    tx_hash = sys.argv[1] if len(sys.argv) > 1 else None
    local = open(LOCAL, "rb").read()
    local_sha = hashlib.sha256(local).hexdigest()
    print(f"local  sha256: {local_sha}  ({len(local)} bytes)")

    if tx_hash is None:
        # list txs to the contract, find the type-1 deploy
        print("no tx hash given; scanning contract txs for deploy…")
        found = False
        for h in recent_tx_hashes(CONTRACT):
            res = rpc("eth_getTransactionByHash", [h]).get("result") or {}
            if res.get("to_address") and str(
                    res.get("to_address")).lower() == "null":
                found = True
                tx_hash = h
                break
        if not found:
            print("deploy tx not found; pass the deploy tx hash")
            sys.exit(2)

    res = rpc("eth_getTransactionByHash", [tx_hash]).get("result")
    if isinstance(res, str):
        print("tx not found:", tx_hash)
        sys.exit(2)
    b64 = (res.get("data", {}) or {}).get("contract_code")
    if not b64:
        print("no contract_code on this tx")
        sys.exit(2)
    deployed = base64.b64decode(b64)
    deployed_sha = hashlib.sha256(deployed).hexdigest()
    print(f"deploy sha256: {deployed_sha}  ({len(deployed)} bytes)")
    if deployed == local:
        print("BYTE-IDENTITY: VERIFIED")
        return
    print("MISMATCH — deployed code differs from contracts/token_scope.py")
    sys.exit(1)


def recent_tx_hashes(addr):
    body = json.dumps({"method": "eth_getTransactionsByAddress",
                       "params": [addr, ""], "jsonrpc": "2.0",
                       "id": 1}).encode()
    req = urllib.request.Request(
        RPC, data=body,
        headers={"Content-Type": "application/json",
                 "User-Agent": "curl/8.5.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            out = json.loads(r.read().decode())
        res = out.get("result", [])
        return [t.get("hash") or t.get("tx_id") for t in res
                if isinstance(t, dict)]
    except Exception:
        return []


if __name__ == "__main__":
    main()
