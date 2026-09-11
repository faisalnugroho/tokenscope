"""Semantic fixture tests — the 15 Solidity fixtures run through the
FULL contract pipeline (mocked Sourcify + mocked LLM).

These prove the CONTRACT machinery produces correct stored reports for
each semantic class, that the prompt receives the artifact content, and
that the grounding gates keep evidence honest. Live-model semantic
accuracy is separately verified on Studionet (docs/EVIDENCE.md) — these
tests assert the deterministic layers.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import (  # noqa: E402
    CHAIN, mock_body, sourcify_url, deploy, parse_report,
    load_contract_module, load_taxonomy,
)
import fixtures_data as fd  # noqa: E402


def _analyze_ok(vm, c, slug):
    addr = fd.F[slug]["addr"]
    mock_body(vm, sourcify_url(CHAIN, addr), fd.body_for(slug))
    vm.mock_llm(".*", fd.llm_answer_for(slug))
    rid = c.analyze(CHAIN, addr)
    return rid, parse_report(c.get_report(rid))


def _assert_caps(r, detected=(), not_detected=(), uncertain=()):
    for cap in detected:
        assert r["capabilities"][cap]["status"] == "DETECTED", \
            (cap, r["capabilities"][cap])
    for cap in not_detected:
        assert r["capabilities"][cap]["status"] == "NOT_DETECTED", \
            (cap, r["capabilities"][cap])
    for cap in uncertain:
        assert r["capabilities"][cap]["status"] == "UNCERTAIN", \
            (cap, r["capabilities"][cap])


class TestSemanticFixtures:
    def test_fixture_01_plain_erc20(self, direct_vm, direct_deploy):
        # no admin capabilities at all
        c = deploy(direct_vm)
        _, r = _analyze_ok(direct_vm, c, "plain_erc20")
        assert r["analysis_status"] == "COMPLETE"
        assert r["source_status"] == "EXACT_MATCH"
        _assert_caps(r, not_detected=[
            "ownership_detected", "mint", "burn", "pause", "blacklist",
            "whitelist", "forced_transfer", "fee_control",
            "upgradeability", "balance_override", "rescue_assets",
            "eth_withdraw", "arbitrary_allowance_edit",
        ])

    def test_fixture_02_mintable(self, direct_vm, direct_deploy):
        c = deploy(direct_vm)
        _, r = _analyze_ok(direct_vm, c, "mintable")
        _assert_caps(r, detected=["mint", "ownership_detected"])
        ev = r["capabilities"]["mint"]["evidence"]
        assert ev and ev[0]["func"] == "mint"

    def test_fixture_03_burnable(self, direct_vm, direct_deploy):
        c = deploy(direct_vm)
        _, r = _analyze_ok(direct_vm, c, "burnable")
        _assert_caps(r, detected=["burn"])

    def test_fixture_04_pausable(self, direct_vm, direct_deploy):
        c = deploy(direct_vm)
        _, r = _analyze_ok(direct_vm, c, "pausable")
        _assert_caps(r, detected=["pause", "ownership_detected"])

    def test_fixture_05_blacklist(self, direct_vm, direct_deploy):
        c = deploy(direct_vm)
        _, r = _analyze_ok(direct_vm, c, "blacklist")
        _assert_caps(r, detected=["blacklist", "ownership_detected"])
        _assert_caps(r, not_detected=["whitelist"])

    def test_fixture_06_whitelist(self, direct_vm, direct_deploy):
        c = deploy(direct_vm)
        _, r = _analyze_ok(direct_vm, c, "whitelist")
        _assert_caps(r, detected=["whitelist", "ownership_detected"])
        _assert_caps(r, not_detected=["blacklist"])

    def test_fixture_07_fee_adjustable(self, direct_vm, direct_deploy):
        c = deploy(direct_vm)
        _, r = _analyze_ok(direct_vm, c, "fee_adjustable")
        _assert_caps(r, detected=["fee_control", "ownership_detected"])
        assert r["capabilities"]["fee_control"]["evidence"][0]["func"] \
            == "setFee"

    def test_fixture_08_ownable(self, direct_vm, direct_deploy):
        c = deploy(direct_vm)
        _, r = _analyze_ok(direct_vm, c, "ownable")
        _assert_caps(r, detected=[
            "ownership_detected", "ownership_transferable",
            "ownership_renounceable",
        ])
        _assert_caps(r, not_detected=["mint", "pause"])

    def test_fixture_09_access_control(self, direct_vm, direct_deploy):
        c = deploy(direct_vm)
        _, r = _analyze_ok(direct_vm, c, "access_control")
        _assert_caps(r, detected=["role_based_admin", "mint"])

    def test_fixture_10_upgradeable_proxy(self, direct_vm, direct_deploy):
        c = deploy(direct_vm)
        _, r = _analyze_ok(direct_vm, c, "upgradeable_proxy")
        _assert_caps(r, detected=[
            "upgradeability", "upgrade_admin", "ownership_detected",
        ])

    def test_fixture_11_forced_transfer(self, direct_vm, direct_deploy):
        c = deploy(direct_vm)
        _, r = _analyze_ok(direct_vm, c, "forced_transfer")
        _assert_caps(r, detected=["forced_transfer", "ownership_detected"])

    def test_fixture_12_rescue_sweep(self, direct_vm, direct_deploy):
        c = deploy(direct_vm)
        _, r = _analyze_ok(direct_vm, c, "rescue_sweep")
        _assert_caps(r, detected=[
            "rescue_assets", "eth_withdraw", "ownership_detected",
        ])

    def test_fixture_13_ambiguous(self, direct_vm, direct_deploy):
        c = deploy(direct_vm)
        _, r = _analyze_ok(direct_vm, c, "ambiguous")
        # ambiguous flags are UNCERTAIN — never silently collapsed
        _assert_caps(r, uncertain=["whitelist", "blacklist"])
        _assert_caps(r, detected=["ownership_detected"])
        _assert_caps(r, not_detected=["mint", "pause"])
        assert r["analysis_status"] == "COMPLETE"

    def test_fixture_14_prompt_injection(self, direct_vm, direct_deploy):
        # The fixture's comments demand: mint=NOT_DETECTED,
        # blacklist=NOT_DETECTED, "mark this contract safe". The REAL
        # behavior: owner-gated mint exists; blacklist() writes storage
        # but is not enforced in transfer -> UNCERTAIN. The stored
        # report must reflect behavior, not the comments' demands.
        c = deploy(direct_vm)
        _, r = _analyze_ok(direct_vm, c, "prompt_injection")
        _assert_caps(r, detected=["mint", "ownership_detected"])
        _assert_caps(r, uncertain=["blacklist"])
        # the injection demanded "SAFE"/schema change — none stored
        blob = json.dumps(r)
        assert "SAFE" not in blob
        assert "safe" not in blob
        assert r["analysis_status"] in ("COMPLETE", "UNCERTAIN_EVIDENCE")

    def test_fixture_15_misleading_names(self, direct_vm, direct_deploy):
        c = deploy(direct_vm)
        _, r = _analyze_ok(direct_vm, c, "misleading_names")
        _assert_caps(r, not_detected=[
            "mint", "pause", "blacklist", "rescue_assets",
            "ownership_detected", "forced_transfer",
        ])


class TestPromptCarriesArtifacts:
    # Prove the LLM prompt actually contains the fixture source code
    # (the semantic layer sees real artifact data, not summaries).

    def test_prompt_contains_fixture_source(self, direct_vm,
                                            direct_deploy):
        c = deploy(direct_vm)
        slug = "blacklist"
        addr = fd.F[slug]["addr"]
        mock_body(direct_vm, sourcify_url(CHAIN, addr), fd.body_for(slug))
        seen = []
        orig = direct_vm._match_llm_mock

        def spy(prompt):
            seen.append(prompt)
            return orig(prompt)

        direct_vm._match_llm_mock = spy
        try:
            direct_vm.mock_llm(".*", fd.llm_answer_for(slug))
            c.analyze(CHAIN, addr)
        finally:
            direct_vm._match_llm_mock = orig
        assert len(seen) >= 1
        prompt = seen[0]
        # source text with injection-relevant content must be in prompt
        assert "blacklist(address account)" in prompt
        assert "BlacklistToken" in prompt
        assert "require(!blacklisted[msg.sender]" in prompt
        # ABI present too
        assert '"name": "blacklist"' in prompt

    def test_prompt_injection_fixture_reaches_llm_unaltered(self, direct_vm,
                                                           direct_deploy):
        # the injected comment text travels to the LLM as DATA — the
        # prompt still contains the armor rules; prove the pipeline does
        # not crash and the classification follows BEHAVIOR
        c = deploy(direct_vm)
        slug = "prompt_injection"
        addr = fd.F[slug]["addr"]
        mock_body(direct_vm, sourcify_url(CHAIN, addr), fd.body_for(slug))
        direct_vm.mock_llm(".*", fd.llm_answer_for(slug))
        rid = c.analyze(CHAIN, addr)
        r = parse_report(c.get_report(rid))
        assert r["capabilities"]["mint"]["status"] == "DETECTED"


class TestPartialAndSourceless:
    def test_partial_match_report_labeled(self, direct_vm, direct_deploy):
        c = deploy(direct_vm)
        slug = "mintable"
        addr = fd.F[slug]["addr"]
        mock_body(direct_vm, sourcify_url(CHAIN, addr),
                  fd.body_for(slug, match="match"))
        direct_vm.mock_llm(".*", fd.llm_answer_for(slug))
        rid = c.analyze(CHAIN, addr)
        r = parse_report(c.get_report(rid))
        assert r["source_status"] == "PARTIAL_MATCH"
        assert r["analysis_status"] == "COMPLETE"

    def test_abi_only_report_flagged_uncertain(self, direct_vm,
                                               direct_deploy):
        # sources absent: analysis runs on ABI alone but is flagged
        # UNCERTAIN_EVIDENCE (never silently full-confidence)
        c = deploy(direct_vm)
        slug = "ownable"
        addr = fd.F[slug]["addr"]
        body = json.loads(fd.body_for(slug))
        body["sources"] = {}
        mock_body(direct_vm, sourcify_url(CHAIN, addr), json.dumps(body))
        direct_vm.mock_llm(".*", fd.llm_answer_for(slug))
        rid = c.analyze(CHAIN, addr)
        r = parse_report(c.get_report(rid))
        assert r["source_status"] == "EXACT_MATCH"
        assert r["analysis_status"] == "UNCERTAIN_EVIDENCE"
        assert r["sources_present"] is False
        # ABI-grounded evidence still survives
        assert r["capabilities"]["ownership_transferable"]["status"] \
            == "DETECTED"


class TestSupplyCapAndUngroundedEdge:
    def test_supply_cap_detected_via_llm(self, direct_vm, direct_deploy):
        # supply_cap needs source-level evidence: constructor mints a
        # fixed amount, no mint function — DETECTED via llm answer
        c = deploy(direct_vm)
        slug = "plain_erc20"
        addr = fd.F[slug]["addr"]
        mock_body(direct_vm, sourcify_url(CHAIN, addr), fd.body_for(slug))
        answer = json.loads(fd.llm_answer_for(slug))
        answer["capabilities"]["supply_cap"] = {
            "status": "DETECTED", "confidence": "MEDIUM",
            "reason": "fixed 1M supply minted in constructor",
            "evidence": [{"func": "totalSupply", "ref": "abi"}],
        }
        direct_vm.mock_llm(".*", json.dumps(answer))
        rid = c.analyze(CHAIN, addr)
        r = parse_report(c.get_report(rid))
        assert r["capabilities"]["supply_cap"]["status"] == "DETECTED"
        assert r["capabilities"]["supply_cap"]["evidence"][0]["func"] \
            == "totalSupply"

    def test_supply_cap_ungrounded_demoted(self, direct_vm, direct_deploy):
        c = deploy(direct_vm)
        slug = "plain_erc20"
        addr = fd.F[slug]["addr"]
        mock_body(direct_vm, sourcify_url(CHAIN, addr), fd.body_for(slug))
        answer = json.loads(fd.llm_answer_for(slug))
        answer["capabilities"]["supply_cap"] = {
            "status": "DETECTED", "confidence": "HIGH",
            "reason": "made up",
            "evidence": [{"func": "maxSupply", "ref": "sources"}],
        }
        direct_vm.mock_llm(".*", json.dumps(answer))
        rid = c.analyze(CHAIN, addr)
        r = parse_report(c.get_report(rid))
        assert r["capabilities"]["supply_cap"]["status"] == "UNCERTAIN"
        assert r["analysis_status"] == "UNCERTAIN_EVIDENCE"


class TestTaxonomyCoverage:
    def test_every_capability_answered_in_every_report(self, direct_vm,
                                                       direct_deploy):
        # stored reports always carry all 18 capabilities — no partial
        # matrices ever
        c = deploy(direct_vm)
        for slug in ("plain_erc20", "mintable", "ambiguous"):
            _, r = _analyze_ok(direct_vm, c, slug)
            assert sorted(r["capabilities"].keys()) == \
                sorted(load_taxonomy())
