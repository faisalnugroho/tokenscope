"""Shared direct-mode test helpers and fixture content for TokenScope.

  - mock_body(): dict-format web mock (string bodies fetch EMPTY —
    verified gltest pitfall)
  - sourcify_body(): builds a realistic Sourcify v2 response envelope
    from an ABI + sources dict
  - llm_result(): builds a well-formed LLM classification payload
  - deploy/analyze wrappers

Target: a fixed chain (1) and a fixed address per fixture; every fixture
lives at its own deterministic URL so web mocks are per-fixture.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "fixtures"

CONTRACT = str(ROOT / "contracts" / "token_scope.py")

CHAIN = "1"
# a real-ish verified target address (fixture-controlled)
ADDR = "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984"


def _u256(v):
    # Lazy: `genlayer` only lands on sys.path once gltest's loader has
    # resolved the SDK (first direct_deploy call).
    from genlayer import u256
    return u256(v)


def mock_body(vm, url, body, status=200):
    # DICT format is mandatory — string bodies fetch EMPTY.
    # The URL is escaped: '?' and '.' in URLs are regex metachars and a
    # literal URL pattern silently never matches (verified pitfall).
    vm.mock_web(re.escape(url), {"status": status, "body": body})


def sourcify_url(chain, addr):
    return ("https://sourcify.dev/server/v2/contract/"
            + chain + "/" + addr + "?fields=abi,sources")


def sourcify_body(match="exact_match", abi=None, sources=None,
                  chain_id=CHAIN, address=ADDR, verified_at=None,
                  extra=None):
    """Sourcify v2 contract response envelope (verified live
    2026-09-11: fields=abi,sources keeps the default verification
    fields match/chainId/address/verifiedAt)."""
    d = {
        "match": match,
        "creationMatch": "exact_match" if match == "exact_match"
        else ("match" if match == "match" else None),
        "runtimeMatch": "exact_match" if match == "exact_match"
        else ("match" if match == "match" else None),
        "verifiedAt": verified_at or "2026-01-01T00:00:00Z",
        "chainId": str(chain_id),
        "address": address,
        "abi": abi if abi is not None else [],
        "sources": sources if sources is not None else {},
    }
    if extra:
        d.update(extra)
    return json.dumps(d)


def deploy(vm, contract_path=CONTRACT):
    from gltest.direct.loader import deploy_contract
    return deploy_contract(contract_path, vm)


def make_llm_answer(status_map, analysis_status="COMPLETE",
                    evidence_map=None, conf="HIGH"):
    """Build a well-formed LLM classification JSON for mock_llm.

    status_map: {cap_id: "DETECTED"|"NOT_DETECTED"|"UNCERTAIN"}
    evidence_map: optional {cap_id: ["funcName", ...]} (default: the
      functions present in the fixture ABI for DETECTED caps)
    """
    caps = {}
    for cap, st in status_map.items():
        ev = []
        if evidence_map and cap in evidence_map:
            for fn in evidence_map[cap]:
                ev.append({"func": fn, "ref": "sources"})
        caps[cap] = {
            "status": st,
            "confidence": conf,
            "reason": "fixture reason",
            "evidence": ev,
        }
    out = {"schema_version": "1.0", "capabilities": caps}
    if analysis_status:
        out["analysis_status"] = analysis_status
    return json.dumps(out)


def all_caps_answer(status, evidence_map=None):
    status_map = {}
    for cap in load_taxonomy():
        status_map[cap] = status
    return make_llm_answer(status_map, evidence_map=evidence_map)


_TAXONOMY = None


def load_taxonomy():
    global _TAXONOMY
    if _TAXONOMY is None:
        # Lazy: needs the gltest SDK resolved (conftest pins it) and
        # the contract module loaded (bootstrap below).
        m = _load_contract_module()
        _TAXONOMY = list(m.TAXONOMY)
    return _TAXONOMY


_M = None


def _load_contract_module():
    """Load the contract module ONCE for pure-function unit tests.

    Reuses the loader under the same activate() protocol the pytest
    fixtures use; the captured module reference keeps pure functions
    alive even after cleanup evicts _contract_* from sys.modules.
    """
    global _M
    if _M is not None:
        return _M
    for name, mod in list(sys.modules.items()):
        if name.startswith("_contract_token_scope") and \
                hasattr(mod, "TAXONOMY"):
            _M = mod
            return _M
    from gltest.direct.vm import VMContext
    from gltest.direct.loader import create_address, load_contract_class
    vm = VMContext()
    vm.sender = create_address("unit-bootstrap")
    with vm.activate():
        load_contract_class(Path(CONTRACT), vm)
        for name, mod in list(sys.modules.items()):
            if name.startswith("_contract_token_scope") and \
                    hasattr(mod, "TAXONOMY"):
                _M = mod
                break
    assert _M is not None, "contract module did not load"
    return _M


def load_contract_module():
    return _load_contract_module()


def parse_report(raw):
    """Parse a report JSON string from get_report/get_latest_for."""
    return json.loads(raw)


# ---------------------------------------------------------------------------
# ABI fragment builder — makes realistic Sourcify-shaped ABI arrays
# ---------------------------------------------------------------------------


def fn(name, inputs=None, mutability="nonpayable", outputs=None):
    return {"type": "function", "name": name,
            "inputs": [{"name": n, "type": t} for n, t in (inputs or [])],
            "outputs": [{"name": "", "type": t} for t in (outputs or [])],
            "stateMutability": mutability}


def ev(name, inputs=None):
    return {"type": "event", "name": name, "anonymous": False,
            "inputs": [{"name": n, "type": t, "indexed": bool(ix)}
                       for (n, t, ix) in (inputs or [])]}


def sol(name, content):
    return {name: {"content": content}}
