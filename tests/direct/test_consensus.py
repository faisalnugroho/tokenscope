"""Consensus / Equivalence-Principle tests — spec cases 1–8.

Consensus model in gltest direct mode: the leader runs inside the
contract call; vm.run_validator() then executes the CAPTURED validator
against the leader's actual result — or against a forged one — with
independently swappable web/LLM mocks. This proves the validator does
its own retrieval and re-derivation, and that the Equivalence Principle
verifies SUBSTANCE (canonical statuses), not JSON shape or prose.

Case 1  leader+validators equivalent matrices, different prose
        -> CONSENSUS ACCEPTED (validator returns True)
Case 2  capabilities reordered in the leader's serialization
        -> ACCEPTED (TAXONOMY-ordered comparison)
Case 3  different explanatory text, identical normalized statuses
        -> ACCEPTED
Case 4  validator disagrees on a material capability
        -> REJECTED (no silent commit of an incorrect result)
Case 5  web source unavailable (leader and validator both fail)
        -> explicit UNAVAILABLE/ERROR state stored
Case 6  LLM returns malformed JSON
        -> safe failure (LLM_MALFORMED_JSON stored; deterministic code)
Case 7  LLM returns extra prose around valid JSON
        -> safely normalized
Case 8  LLM attempts to invent evidence
        -> evidence validation rejects unsupported references
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

SLUG = "mintable"
ADDR = fd.F[SLUG]["addr"]
URL = sourcify_url(CHAIN, ADDR)


def _mocks(vm, answer=None, body=None):
    mock_body(vm, URL, body if body is not None else fd.body_for(SLUG))
    vm.mock_llm(".*", answer if answer is not None
                else fd.llm_answer_for(SLUG))


def _prose_variant(answer, seed):
    """Rewrite every reason/confidence deterministically per seed —
    statuses and evidence untouched."""
    d = json.loads(answer)
    for cap, item in d["capabilities"].items():
        item["reason"] = ("validator wording %d for %s" % (seed, cap))[:120]
        item["confidence"] = ("HIGH", "MEDIUM", "LOW")[seed % 3]
    d["analysis_status"] = "COMPLETE"
    return json.dumps(d)


class TestCase1EquivalentDifferentProse:
    def test_consensus_accepted(self, direct_vm, direct_deploy):
        c = deploy(direct_vm)
        _mocks(direct_vm)                     # leader: ground truth
        rid = c.analyze(CHAIN, ADDR)
        assert parse_report(c.get_report(rid))["analysis_status"] == \
            "COMPLETE"
        # validator: same statuses, different prose/confidence
        direct_vm.clear_mocks()
        _mocks(direct_vm, answer=_prose_variant(fd.llm_answer_for(SLUG), 1))
        assert direct_vm.run_validator() is True


class TestCase2ReorderedCapabilities:
    def test_consensus_accepted(self, direct_vm, direct_deploy):
        c = deploy(direct_vm)
        _mocks(direct_vm)
        c.analyze(CHAIN, ADDR)
        # validator: capabilities dict arrives in reversed key order —
        # the TAXONOMY-ordered comparison is order-insensitive
        direct_vm.clear_mocks()
        answer = json.loads(fd.llm_answer_for(SLUG))
        answer["capabilities"] = dict(
            reversed(list(answer["capabilities"].items())))
        _mocks(direct_vm, answer=json.dumps(answer))
        assert direct_vm.run_validator() is True


class TestCase3DifferentTextSameStatuses:
    def test_consensus_accepted(self, direct_vm, direct_deploy):
        c = deploy(direct_vm)
        _mocks(direct_vm)
        c.analyze(CHAIN, ADDR)
        # validator: entirely different reasoning style, same statuses
        direct_vm.clear_mocks()
        answer = json.loads(fd.llm_answer_for(SLUG))
        for cap, item in answer["capabilities"].items():
            item["reason"] = "as I already explained, %s is %s" % (
                cap, item["status"])
        _mocks(direct_vm, answer=json.dumps(answer))
        assert direct_vm.run_validator() is True


class TestCase4MaterialDisagreement:
    def test_rejected_no_silent_commit(self, direct_vm, direct_deploy):
        c = deploy(direct_vm)
        _mocks(direct_vm)                     # leader: mint DETECTED
        rid = c.analyze(CHAIN, ADDR)
        assert parse_report(
            c.get_report(rid))["capabilities"]["mint"]["status"] == \
            "DETECTED"
        # validator's own fetch+LLM conclude mint NOT_DETECTED
        direct_vm.clear_mocks()
        answer = json.loads(fd.llm_answer_for(SLUG))
        answer["capabilities"]["mint"]["status"] = "NOT_DETECTED"
        answer["capabilities"]["mint"]["evidence"] = []
        _mocks(direct_vm, answer=json.dumps(answer))
        assert direct_vm.run_validator() is False

    def test_web_differences_drive_disagreement(self, direct_vm,
                                                direct_deploy):
        # leader analyzes mintable; validator's fetch serves plain_erc20
        c = deploy(direct_vm)
        _mocks(direct_vm)
        c.analyze(CHAIN, ADDR)
        direct_vm.clear_mocks()
        _mocks(direct_vm, answer=fd.llm_answer_for("plain_erc20"),
               body=fd.body_for("plain_erc20"))
        assert direct_vm.run_validator() is False


class TestCase5WebSourceUnavailable:
    def test_explicit_unavailable_state(self, direct_vm, direct_deploy):
        c = deploy(direct_vm)
        # leader: no web mock -> RETRIEVAL_UNAVAILABLE
        direct_vm.mock_llm(".*", fd.llm_answer_for(SLUG))
        rid = c.analyze(CHAIN, ADDR)
        r = parse_report(c.get_report(rid))
        assert r["analysis_status"] == "UNAVAILABLE"
        assert r["failure"] == {"stage": "RETRIEVAL",
                                "error_code": "RETRIEVAL_UNAVAILABLE"}
        # validator sees the SAME unavailable source -> agrees on the
        # deterministic failure state
        assert direct_vm.run_validator() is True

    def test_unavailable_never_negative_finding(self, direct_vm,
                                                direct_deploy):
        c = deploy(direct_vm)
        direct_vm.mock_llm(".*", fd.llm_answer_for(SLUG))
        rid = c.analyze(CHAIN, ADDR)
        r = parse_report(c.get_report(rid))
        for cap in load_taxonomy():
            assert r["capabilities"][cap]["status"] == "UNAVAILABLE"


class TestCase6MalformedLLMJson:
    def test_safe_failure(self, direct_vm, direct_deploy):
        c = deploy(direct_vm)
        mock_body(direct_vm, URL, fd.body_for(SLUG))
        direct_vm.mock_llm(".*", "{this is not json")
        rid = c.analyze(CHAIN, ADDR)
        r = parse_report(c.get_report(rid))
        assert r["failure"] == {"stage": "SEMANTIC",
                                "error_code": "LLM_MALFORMED_JSON"}

    def test_consensus_on_failure_state(self, direct_vm, direct_deploy):
        # both leader and validator get malformed LLM output — they
        # agree on the deterministic failure (no retry inside one
        # consensus round; a re-submitted analyze() is the retry path)
        c = deploy(direct_vm)
        mock_body(direct_vm, URL, fd.body_for(SLUG))
        direct_vm.mock_llm(".*", "{oops")
        rid = c.analyze(CHAIN, ADDR)
        assert parse_report(c.get_report(rid))["analysis_status"] == \
            "UNAVAILABLE"
        assert direct_vm.run_validator() is True

    def test_retry_via_resubmission_recovers(self, direct_vm,
                                              direct_deploy):
        # the practical retry: submit analyze() again — new round, new
        # LLM run — recovers to a full report
        c = deploy(direct_vm)
        mock_body(direct_vm, URL, fd.body_for(SLUG))
        direct_vm.mock_llm(".*", "{bad json")
        rid1 = c.analyze(CHAIN, ADDR)
        assert parse_report(
            c.get_report(rid1))["analysis_status"] == "UNAVAILABLE"
        direct_vm.clear_mocks()
        _mocks(direct_vm)
        rid2 = c.analyze(CHAIN, ADDR)
        r2 = parse_report(c.get_report(rid2))
        assert r2["analysis_status"] == "COMPLETE"
        assert r2["capabilities"]["mint"]["status"] == "DETECTED"
        # the failed attempt is retained in history (audit trail)
        hist = json.loads(c.get_history_for(CHAIN, ADDR))
        assert rid1 in hist and rid2 in hist


class TestCase7LLMExtraProse:
    def test_parser_normalizes(self, direct_vm, direct_deploy):
        c = deploy(direct_vm)
        mock_body(direct_vm, URL, fd.body_for(SLUG))
        wrapped = ("Sure — analysis complete:\n```json\n"
                   + fd.llm_answer_for(SLUG) + "\n```\nHope this helps!")
        direct_vm.mock_llm(".*", wrapped)
        rid = c.analyze(CHAIN, ADDR)
        r = parse_report(c.get_report(rid))
        assert r["analysis_status"] == "COMPLETE"
        assert r["capabilities"]["mint"]["status"] == "DETECTED"

    def test_consensus_accepted_with_prose_wrapper(self, direct_vm,
                                                   direct_deploy):
        c = deploy(direct_vm)
        mock_body(direct_vm, URL, fd.body_for(SLUG))
        direct_vm.mock_llm(
            ".*", "Here: " + fd.llm_answer_for(SLUG) + " done")
        c.analyze(CHAIN, ADDR)
        direct_vm.clear_mocks()
        mock_body(direct_vm, URL, fd.body_for(SLUG))
        direct_vm.mock_llm(
            ".*", "Wrapping differently: "
            + fd.llm_answer_for(SLUG) + " !!!")
        assert direct_vm.run_validator() is True


class TestCase8InventedEvidence:
    def test_unsupported_reference_rejected(self, direct_vm,
                                             direct_deploy):
        c = deploy(direct_vm)
        mock_body(direct_vm, URL, fd.body_for(SLUG))
        answer = json.loads(fd.llm_answer_for(SLUG))
        answer["capabilities"]["mint"]["evidence"] = [
            {"func": "superSecretMint", "ref": "sources"},
            {"func": "hiddenOwner", "ref": "abi"},
        ]
        direct_vm.mock_llm(".*", json.dumps(answer))
        rid = c.analyze(CHAIN, ADDR)
        r = parse_report(c.get_report(rid))
        # both fabricated references rejected -> mint demoted
        assert r["capabilities"]["mint"]["status"] == "UNCERTAIN"
        assert r["capabilities"]["mint"]["evidence"] == []
        assert r["capabilities"]["mint"]["reason"] == \
            "evidence_not_grounded"

    def test_partially_real_evidence_keeps_grounded_part(self, direct_vm,
                                                          direct_deploy):
        c = deploy(direct_vm)
        mock_body(direct_vm, URL, fd.body_for(SLUG))
        answer = json.loads(fd.llm_answer_for(SLUG))
        answer["capabilities"]["mint"]["evidence"] = [
            {"func": "mint", "ref": "sources"},          # real
            {"func": "phantomFunction", "ref": "sources"}  # fake
        ]
        direct_vm.mock_llm(".*", json.dumps(answer))
        rid = c.analyze(CHAIN, ADDR)
        r = parse_report(c.get_report(rid))
        # real evidence survives; fake dropped; DETECTED stands
        assert r["capabilities"]["mint"]["status"] == "DETECTED"
        assert [e["func"] for e in
                r["capabilities"]["mint"]["evidence"]] == ["mint"]

    def test_consensus_with_evidence_variance(self, direct_vm,
                                              direct_deploy):
        # leader cites mint; validator cites mint AND owner for the
        # same DETECTED statuses — evidence is not consensus-compared
        # (grounded by construction), so consensus holds
        c = deploy(direct_vm)
        mock_body(direct_vm, URL, fd.body_for(SLUG))
        direct_vm.mock_llm(".*", fd.llm_answer_for(SLUG))
        c.analyze(CHAIN, ADDR)
        direct_vm.clear_mocks()
        mock_body(direct_vm, URL, fd.body_for(SLUG))
        answer = json.loads(fd.llm_answer_for(SLUG))
        answer["capabilities"]["mint"]["evidence"] = [
            {"func": "mint", "ref": "sources"},
            {"func": "owner", "ref": "abi"},
        ]
        direct_vm.mock_llm(".*", json.dumps(answer))
        assert direct_vm.run_validator() is True


class TestForgeResistance:
    # adversarial: can a MALICIOUS leader slip anything past the
    # validator's independent re-derivation?

    def _leader_established(self, vm, c):
        _mocks(vm)
        rid = c.analyze(CHAIN, ADDR)
        return rid

    def test_forged_all_detected(self, direct_vm, direct_deploy):
        c = deploy(direct_vm)
        self._leader_established(direct_vm, c)
        direct_vm.clear_mocks()
        _mocks(direct_vm)
        forged_caps = {}
        for cap in load_taxonomy():
            forged_caps[cap] = {"status": "DETECTED",
                                "confidence": "HIGH", "reason": "lie",
                                "evidence": []}
        forged = {"source_status": "EXACT_MATCH",
                  "analysis_status": "COMPLETE",
                  "capabilities": forged_caps, "verified_at": "",
                  "sources_present": True, "failure": None}
        assert direct_vm.run_validator(leader_result=forged) is False

    def test_forged_failure_hides_real_capability(self, direct_vm,
                                                  direct_deploy):
        # a malicious leader claims RETRIEVAL failed while the source
        # is fine — validator fetches fine and disagrees
        c = deploy(direct_vm)
        self._leader_established(direct_vm, c)
        direct_vm.clear_mocks()
        _mocks(direct_vm)
        forged = load_contract_module()._failure_pipeline(
            "RETRIEVAL", "RETRIEVAL_UNAVAILABLE")
        assert direct_vm.run_validator(leader_result=forged) is False

    def test_forged_bad_schema_version(self, direct_vm, direct_deploy):
        c = deploy(direct_vm)
        self._leader_established(direct_vm, c)
        direct_vm.clear_mocks()
        _mocks(direct_vm)
        forged = {"schema_version": "9.9", "source_status": "EXACT_MATCH",
                  "analysis_status": "COMPLETE", "capabilities": {},
                  "failure": None}
        assert direct_vm.run_validator(leader_result=forged) is False

    def test_forged_partial_capability_set(self, direct_vm, direct_deploy):
        # leader answers only 3 of 18 capabilities — validator's full
        # re-derivation disagrees (missing != NOT_DETECTED)
        c = deploy(direct_vm)
        self._leader_established(direct_vm, c)
        direct_vm.clear_mocks()
        _mocks(direct_vm)
        forged_caps = {
            "mint": {"status": "DETECTED", "confidence": "HIGH",
                     "reason": "x", "evidence": []},
            "pause": {"status": "NOT_DETECTED", "confidence": "HIGH",
                      "reason": "x", "evidence": []},
            "burn": {"status": "NOT_DETECTED", "confidence": "HIGH",
                     "reason": "x", "evidence": []},
        }
        forged = {"source_status": "EXACT_MATCH",
                  "analysis_status": "COMPLETE",
                  "capabilities": forged_caps, "verified_at": "",
                  "sources_present": True, "failure": None}
        assert direct_vm.run_validator(leader_result=forged) is False
