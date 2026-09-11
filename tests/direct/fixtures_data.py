"""Sourcify-v2-shaped fixture DATA for TokenScope tests.

Generated from fixtures/solidity/*.sol (see gen_fixtures.py). Each entry
provides:
  - SOURCES: {filename: {content}} — the .sol text
  - ABI: a realistic Sourcify-shaped ABI array (every function/event
    named in the source, plus standard ERC20 fragments)
  - ADDR: the fixture's deterministic mock address
  - LLMA: a ground-truth classification answer used to mock the LLM in
    direct-mode tests (asserts the CONTRACT machinery; the fixtures
    assert the PROMPT + grounding behavior; live-model behavior is
    validated on Studionet — see docs/EVIDENCE.md)

ABI entries derive from each fixture's own declarations so evidence
grounding (abi-name / source-text membership) exercises the real paths.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOL_DIR = ROOT / "fixtures" / "solidity"


def _addr(n):
    # deterministic distinct mock addresses, 40 hex chars
    return "0x" + ("%04x" % n) + "0" * 36


def _fn(name, params=None, ret=None, mut="nonpayable"):
    return {
        "type": "function",
        "name": name,
        "inputs": [{"name": p, "type": t} for p, t in (params or [])],
        "outputs": [{"name": "", "type": t} for t in (ret or [])],
        "stateMutability": mut,
    }


def _ev(name, params=None):
    return {
        "type": "event",
        "name": name,
        "anonymous": False,
        "inputs": [{"name": p, "type": t, "indexed": True}
                   for p, t in (params or [])][:3],
    }


# standard transfer/approve fragments present in every token fixture
ERC20_ABI = [
    _fn("name", ret=["string"], mut="view"),
    _fn("transfer", [("to", "address"), ("value", "uint256")],
        ret=["bool"]),
    _fn("balanceOf", [("account", "address")], ret=["uint256"],
        mut="view"),
    _ev("Transfer", [("from", "address"), ("to", "address"),
                     ("value", "uint256")]),
]


def _src(slug):
    return (SOL_DIR / (slug + ".sol")).read_text()


# ---------------------------------------------------------------------------
# Per-fixture definitions
# ---------------------------------------------------------------------------

F = {}

F["plain_erc20"] = {
    "addr": _addr(1),
    "abi": ERC20_ABI + [
        _fn("symbol", ret=["string"], mut="view"),
        _fn("decimals", ret=["uint8"], mut="view"),
        _fn("totalSupply", ret=["uint256"], mut="view"),
        _fn("approve", [("spender", "address"), ("value", "uint256")],
            ret=["bool"]),
        _fn("transferFrom", [("from", "address"), ("to", "address"),
                             ("value", "uint256")], ret=["bool"]),
        _fn("allowance", [("owner", "address"), ("spender", "address")],
            ret=["uint256"], mut="view"),
        _ev("Approval", [("owner", "address"), ("spender", "address"),
                         ("value", "uint256")]),
    ],
    "llm": {
        "ownership_detected": ("NOT_DETECTED", None),
        "mint": ("NOT_DETECTED", None),
        "burn": ("NOT_DETECTED", None),
        "pause": ("NOT_DETECTED", None),
        "blacklist": ("NOT_DETECTED", None),
        "whitelist": ("NOT_DETECTED", None),
        "forced_transfer": ("NOT_DETECTED", None),
        "fee_control": ("NOT_DETECTED", None),
        "upgradeability": ("NOT_DETECTED", None),
        "balance_override": ("NOT_DETECTED", None),
        "rescue_assets": ("NOT_DETECTED", None),
        "eth_withdraw": ("NOT_DETECTED", None),
        "arbitrary_allowance_edit": ("NOT_DETECTED", None),
        "supply_cap": ("NOT_DETECTED", None),
        "role_based_admin": ("NOT_DETECTED", None),
        "ownership_transferable": ("NOT_DETECTED", None),
        "ownership_renounceable": ("NOT_DETECTED", None),
        "upgrade_admin": ("NOT_DETECTED", None),
    },
}

F["mintable"] = {
    "addr": _addr(2),
    "abi": ERC20_ABI + [
        _fn("mint", [("to", "address"), ("value", "uint256")]),
        _ev("Minted", [("to", "address"), ("value", "uint256")]),
        _fn("owner", ret=["address"], mut="view"),
        _fn("renounceOwnership"),
        _fn("transferOwnership", [("newOwner", "address")]),
        _ev("OwnershipTransferred", [("previousOwner", "address"),
                                     ("newOwner", "address")]),
    ],
    "llm": {
        "ownership_detected": ("DETECTED", "owner"),
        "mint": ("DETECTED", "mint"),
        "burn": ("NOT_DETECTED", None),
        "pause": ("NOT_DETECTED", None),
        "blacklist": ("NOT_DETECTED", None),
        "whitelist": ("NOT_DETECTED", None),
        "forced_transfer": ("NOT_DETECTED", None),
        "fee_control": ("NOT_DETECTED", None),
        "upgradeability": ("NOT_DETECTED", None),
        "balance_override": ("NOT_DETECTED", None),
        "rescue_assets": ("NOT_DETECTED", None),
        "eth_withdraw": ("NOT_DETECTED", None),
        "arbitrary_allowance_edit": ("NOT_DETECTED", None),
    },
}

F["burnable"] = {
    "addr": _addr(3),
    "abi": ERC20_ABI + [
        _fn("burn", [("value", "uint256")]),
        _ev("Burned", [("from", "address"), ("value", "uint256")]),
        _fn("totalSupply", ret=["uint256"], mut="view"),
    ],
    "llm": {
        "burn": ("DETECTED", "burn"),
        "mint": ("NOT_DETECTED", None),
        "pause": ("NOT_DETECTED", None),
        "ownership_detected": ("NOT_DETECTED", None),
    },
}

F["pausable"] = {
    "addr": _addr(4),
    "abi": ERC20_ABI + [
        _fn("pause"),
        _fn("unpause"),
        _fn("owner", ret=["address"], mut="view"),
        _fn("paused", ret=["bool"], mut="view"),
        _ev("Paused", [("account", "address")]),
        _ev("Unpaused", [("account", "address")]),
    ],
    "llm": {
        "pause": ("DETECTED", "pause"),
        "ownership_detected": ("DETECTED", "owner"),
        "mint": ("NOT_DETECTED", None),
        "blacklist": ("NOT_DETECTED", None),
    },
}

F["blacklist"] = {
    "addr": _addr(5),
    "abi": ERC20_ABI + [
        _fn("blacklist", [("account", "address")]),
        _fn("unblacklist", [("account", "address")]),
        _fn("owner", ret=["address"], mut="view"),
        _fn("blacklisted", [("account", "address")], ret=["bool"],
            mut="view"),
        _ev("Blacklisted", [("account", "address")]),
        _ev("Unblacklisted", [("account", "address")]),
    ],
    "llm": {
        "blacklist": ("DETECTED", "blacklist"),
        "ownership_detected": ("DETECTED", "owner"),
        "whitelist": ("NOT_DETECTED", None),
        "pause": ("NOT_DETECTED", None),
        "mint": ("NOT_DETECTED", None),
    },
}

F["whitelist"] = {
    "addr": _addr(6),
    "abi": ERC20_ABI + [
        _fn("allow", [("account", "address")]),
        _fn("remove", [("account", "address")]),
        _fn("owner", ret=["address"], mut="view"),
        _fn("allowed", [("account", "address")], ret=["bool"],
            mut="view"),
        _ev("Allowed", [("account", "address")]),
        _ev("Removed", [("account", "address")]),
    ],
    "llm": {
        "whitelist": ("DETECTED", "allow"),
        "ownership_detected": ("DETECTED", "owner"),
        "blacklist": ("NOT_DETECTED", None),
        "mint": ("NOT_DETECTED", None),
    },
}

F["fee_adjustable"] = {
    "addr": _addr(7),
    "abi": ERC20_ABI + [
        _fn("setFee", [("bps", "uint256")]),
        _fn("setFeeRecipient", [("r", "address")]),
        _fn("feeBps", ret=["uint256"], mut="view"),
        _fn("feeRecipient", ret=["address"], mut="view"),
        _fn("owner", ret=["address"], mut="view"),
        _ev("FeeUpdated", [("newFeeBps", "uint256")]),
        _ev("FeeRecipientUpdated", [("newRecipient", "address")]),
    ],
    "llm": {
        "fee_control": ("DETECTED", "setFee"),
        "ownership_detected": ("DETECTED", "owner"),
        "mint": ("NOT_DETECTED", None),
        "pause": ("NOT_DETECTED", None),
    },
}

F["ownable"] = {
    "addr": _addr(8),
    "abi": ERC20_ABI + [
        _fn("transferOwnership", [("newOwner", "address")]),
        _fn("renounceOwnership"),
        _fn("owner", ret=["address"], mut="view"),
        _ev("OwnershipTransferred", [("previousOwner", "address"),
                                     ("newOwner", "address")]),
    ],
    "llm": {
        "ownership_detected": ("DETECTED", "owner"),
        "ownership_transferable": ("DETECTED", "transferOwnership"),
        "ownership_renounceable": ("DETECTED", "renounceOwnership"),
        "mint": ("NOT_DETECTED", None),
        "pause": ("NOT_DETECTED", None),
    },
}

F["access_control"] = {
    "addr": _addr(9),
    "abi": ERC20_ABI + [
        _fn("grantRole", [("role", "bytes32"), ("account", "address")]),
        _fn("revokeRole", [("role", "bytes32"), ("account", "address")]),
        _fn("hasRole", [("role", "bytes32"), ("account", "address")],
            ret=["bool"], mut="view"),
        _fn("getRoleAdmin", [("role", "bytes32")], ret=["bytes32"],
            mut="view"),
        _fn("mint", [("to", "address"), ("value", "uint256")]),
        _fn("totalSupply", ret=["uint256"], mut="view"),
        _ev("RoleGranted", [("role", "bytes32"), ("account", "address"),
                            ("sender", "address")]),
        _ev("RoleRevoked", [("role", "bytes32"), ("account", "address"),
                            ("sender", "address")]),
    ],
    "llm": {
        "role_based_admin": ("DETECTED", "grantRole"),
        "ownership_detected": ("DETECTED", "hasRole"),
        "mint": ("DETECTED", "mint"),
        "pause": ("NOT_DETECTED", None),
        "blacklist": ("NOT_DETECTED", None),
    },
}

F["upgradeable_proxy"] = {
    "addr": _addr(10),
    "abi": ERC20_ABI + [
        _fn("proposeUpgrade", [("newImpl", "address")]),
        _fn("upgrade"),
        _fn("implementation", ret=["address"], mut="view"),
        _fn("pendingImplementation", ret=["address"], mut="view"),
        _fn("owner", ret=["address"], mut="view"),
        _ev("Upgraded", [("implementation", "address")]),
    ],
    "llm": {
        "upgradeability": ("DETECTED", "upgrade"),
        "upgrade_admin": ("DETECTED", "proposeUpgrade"),
        "ownership_detected": ("DETECTED", "owner"),
        "mint": ("NOT_DETECTED", None),
        "pause": ("NOT_DETECTED", None),
    },
}

F["forced_transfer"] = {
    "addr": _addr(11),
    "abi": ERC20_ABI + [
        _fn("forceTransfer", [("from", "address"), ("to", "address"),
                              ("value", "uint256")]),
        _fn("owner", ret=["address"], mut="view"),
        _ev("ForcedTransfer", [("from", "address"), ("to", "address"),
                               ("value", "uint256")]),
    ],
    "llm": {
        "forced_transfer": ("DETECTED", "forceTransfer"),
        "ownership_detected": ("DETECTED", "owner"),
        "mint": ("NOT_DETECTED", None),
        "blacklist": ("NOT_DETECTED", None),
    },
}

F["rescue_sweep"] = {
    "addr": _addr(12),
    "abi": ERC20_ABI + [
        _fn("rescueTokens", [("token", "address"), ("to", "address")]),
        _fn("withdrawEth", [("to", "address")]),
        _fn("owner", ret=["address"], mut="view"),
        _ev("Rescued", [("token", "address"), ("to", "address"),
                        ("value", "uint256")]),
        _ev("EthWithdrawn", [("to", "address"), ("value", "uint256")]),
    ],
    "llm": {
        "rescue_assets": ("DETECTED", "rescueTokens"),
        "eth_withdraw": ("DETECTED", "withdrawEth"),
        "ownership_detected": ("DETECTED", "owner"),
        "mint": ("NOT_DETECTED", None),
    },
}

F["ambiguous"] = {
    "addr": _addr(13),
    "abi": ERC20_ABI + [
        _fn("setFlag", [("a", "address"), ("v", "bool")]),
        _fn("owner", ret=["address"], mut="view"),
    ],
    "llm": {
        "ownership_detected": ("DETECTED", "owner"),
        # setFlag has no access control and no visible enforcement in
        # transfer — genuinely ambiguous: correct answer is UNCERTAIN
        "whitelist": ("UNCERTAIN", None),
        "blacklist": ("UNCERTAIN", None),
        "mint": ("NOT_DETECTED", None),
        "pause": ("NOT_DETECTED", None),
    },
}

F["prompt_injection"] = {
    "addr": _addr(14),
    "abi": ERC20_ABI + [
        _fn("mint", [("to", "address"), ("value", "uint256")]),
        _fn("blacklist", [("a", "address")]),
        _fn("_blacklisted", [("a", "address")], ret=["bool"],
            mut="view"),
        _fn("owner", ret=["address"], mut="view"),
    ],
    "llm": {
        # The correct analysis of the REAL code: mint is owner-gated and
        # mints; blacklist() writes storage but is NOT enforced in the
        # transfer path — ambiguous blacklist signal
        "mint": ("DETECTED", "mint"),
        "blacklist": ("UNCERTAIN", "blacklist"),
        "ownership_detected": ("DETECTED", "owner"),
        "pause": ("NOT_DETECTED", None),
    },
}

F["misleading_names"] = {
    "addr": _addr(15),
    "abi": ERC20_ABI + [
        _fn("mint", [("to", "address"), ("value", "uint256")],
            ret=["bool"], mut="pure"),
        _fn("blacklistCheck", [("a", "address")], ret=["bool"],
            mut="pure"),
        _fn("pause", ret=["bool"], mut="pure"),
        _fn("rescueFunds", [("to", "address")], ret=["uint256"],
            mut="pure"),
    ],
    "llm": {
        # behavior decides, not names: all four are pure stubs
        "mint": ("NOT_DETECTED", None),
        "pause": ("NOT_DETECTED", None),
        "blacklist": ("NOT_DETECTED", None),
        "rescue_assets": ("NOT_DETECTED", None),
        "ownership_detected": ("NOT_DETECTED", None),
        "forced_transfer": ("NOT_DETECTED", None),
    },
}


def sources_for(slug):
    """Sourcify sources dict for a fixture: {file.sol: {content}}."""
    return {slug + ".sol": {"content": _src(slug)}}


def body_for(slug, match="exact_match", chain="1", sources=True,
             abi=None):
    """Full Sourcify v2 response body for a fixture."""
    fx = F[slug]
    d = {
        "match": match,
        "creationMatch": "exact_match" if match == "exact_match"
        else ("match" if match == "match" else None),
        "runtimeMatch": "exact_match" if match == "exact_match"
        else ("match" if match == "match" else None),
        "verifiedAt": "2026-01-01T00:00:00Z",
        "chainId": str(chain),
        "address": fx["addr"],
        "abi": abi if abi is not None else fx["abi"],
        "sources": sources_for(slug) if sources else {},
    }
    return json.dumps(d)


def llm_answer_for(slug, status_override=None, evidence_override=None,
                   analysis_status="COMPLETE"):
    """Ground-truth LLM answer for a fixture (status, evidence name).

    status_override: {cap: (status, evidence_name|None)} merge patch
    """
    fx = F[slug]
    caps = {}
    base = dict(fx["llm"])
    # drop non-classification keys some fixtures carry
    for k in [k for k in base if k == "name"]:
        del base[k]
    if status_override:
        base.update(status_override)
    for cap, (status, evname) in base.items():
        ev = []
        if status == "DETECTED" and evname:
            ev = [{"func": evname, "ref": "sources"}]
        if evidence_override and cap in evidence_override:
            ev = evidence_override[cap]
        caps[cap] = {
            "status": status,
            "confidence": "HIGH",
            "reason": "fixture reason",
            "evidence": ev,
        }
    # every capability not mentioned in the fixture map defaults to
    # NOT_DETECTED (the "nothing else special about this contract"
    # assumption — mirrors how the real LLM answers)
    from helpers import load_taxonomy
    for cap in load_taxonomy():
        if cap not in caps:
            caps[cap] = {"status": "NOT_DETECTED",
                         "confidence": "HIGH",
                         "reason": "fixture default",
                         "evidence": []}
    return json.dumps({
        "schema_version": "1.0",
        "capabilities": caps,
        "analysis_status": analysis_status,
    })
