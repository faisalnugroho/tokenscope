# TokenScope

**Semantic Smart-Contract Capability Oracle** — a GenLayer Intelligent
Contract that translates *verified* smart-contract artifacts into a
structured, consensus-backed capability profile that other applications
can consume.

TokenScope retrieves a contract's verified artifacts from the public
[Sourcify API v2](https://sourcify.dev) and uses GenLayer's
decentralized AI-validator consensus to answer one question:

> What meaningful administrative or control capabilities does this
> contract's verified source actually expose?

- **Live contract (Studionet):** see `docs/deployment_log.json` —
  address + deploy tx + byte-identity sha256
- **Live dApp:** https://faisalnugroho.github.io/tokenscope/
- **What it is NOT:** a security audit, a safety score, or financial
  advice. `NOT_DETECTED` means *not evidenced in the analyzed verified
  artifacts* — never "impossible".

---

## Why GenLayer is necessary

A deterministic smart contract can store an ABI; it cannot *interpret*
arbitrary human-readable source code. Whether a privileged role can
mint, whether an owner can pause transfers, whether a proxy's
implementation can be swapped, whether `mint()` actually modifies
supply — these require semantic reasoning over verified artifacts.
TokenScope performs that reasoning inside GenLayer's nondeterministic
boundaries, with validators independently reproducing the analysis and
an Equivalence Principle that compares only stable canonical fields:

```
┌────────────────┐   GET abi,sources   ┌───────────────────────────┐
│  Sourcify v2   │ ──────────────────► │  gl.nondet.web.get        │  nondeterministic
│  (public,      │                     │  (leader + validators)    │  boundary
│   keyless)     │                     └───────────────────────────┘
└────────────────┘                                 │ artifacts
                                                    ▼
                                       ┌───────────────────────────┐
                                       │  gl.nondet.exec_prompt    │  18-capability
                                       │  classify + cite evidence │  semantic layer
                                       └───────────────────────────┘
                                                    │ canonical JSON
                                                    ▼
┌────────────────────────────────────────────────────────────────────┐
│  DETERMINISTIC: validation gates · evidence grounding · demotion   │
│  · canonicalization · consensus comparison · storage              │
└────────────────────────────────────────────────────────────────────┘
```

Everything outside the two nondeterministic calls is plain
deterministic Python. On-chain state transitions are a pure function of
the consensus-verified canonical result.

## Capability taxonomy (v1.0)

18 capabilities in 8 groups — ownership/administration, token supply,
transfer control, fees, upgradeability, balance control, emergency
controls, and access control. Each is classified as:

| Status | Meaning |
|---|---|
| `DETECTED` | The analyzed verified artifacts evidence the capability (≥1 artifact-grounded supporting function required). |
| `NOT_DETECTED` | The analyzed artifacts provide no sufficient evidence. **Not** a claim of impossibility. |
| `UNCERTAIN` | Evidence exists but is ambiguous, contradictory, or insufficient. Uncertainty is never collapsed into NOT_DETECTED. |
| `NOT_APPLICABLE` | The capability has no meaning for this artifact kind. |
| `UNAVAILABLE` | Report-level: the analysis could not be completed (retrieval/verification/LLM failure). Never a negative finding. |

Full definitions: `get_taxonomy()` on the contract, and
`contracts/token_scope.py` (`_CAP_DOCS`).

## Equivalence Principle design

Validators do **not** compare prose, reasons, confidence, evidence
wording, or timestamps. Each validator independently re-fetches
Sourcify and re-runs the LLM, then compares only:

- `source_status` (EXACT_MATCH / PARTIAL_MATCH)
- `analysis_status` (COMPLETE / UNCERTAIN_EVIDENCE)
- all 18 per-capability statuses
- on failure paths: the deterministic `failure.stage` + `error_code`

Evidence names are deterministically grounded against the fetched
artifacts (ABI member or literal source-text occurrence) and a DETECTED
capability always carries grounded evidence by construction, so the
evidenced-capability set equals the DETECTED set — already
consensus-compared. Comparing evidence wording across independent LLM
runs would add consensus fragility with no security gain (see
`docs/DESIGN.md`).

## Deterministic gates (before/around the LLM)

1. Chain ID `^[1-9][0-9]{0,9}$`, address `^0[xX][0-9a-fA-F]{40}$`
   (case-insensitive), zero address rejected.
2. HTTP failures map to stable families: `RETRIEVAL_UNAVAILABLE`
   (timeout/429/5xx), `RETRIEVAL_BAD_REQUEST` (400),
   `RETRIEVAL_TOO_LARGE` (>2 MB), `MALFORMED_RESPONSE`.
3. Sourcify verification gates: returned chain/address must match the
   request; `match` must be `exact_match`/`match`; missing ABI →
   explicit `ABI_MISSING` failure; sources absent → analysis allowed
   but deterministically flagged `UNCERTAIN_EVIDENCE`.
4. LLM output sanitization: fenced/prose-wrapped JSON tolerated;
   unknown statuses → `UNCERTAIN`; missing capability → `UNCERTAIN`
   (never NOT_DETECTED); every stored string clamped.
5. Evidence grounding: DETECTED requires ≥1 evidence name that exists
   in the artifacts — otherwise the capability is demoted to
   `UNCERTAIN` (`evidence_not_grounded`) and the report is flagged.
6. All failure paths produce well-formed `UNAVAILABLE` reports — a
   retrieval/LLM failure can never become a negative capability
   finding.

## Contract surface

One write: `analyze(chain_id, address) -> report_id`.
Six views: `get_report`, `get_latest_for`, `get_history_for`,
`get_analysis_count`, `get_taxonomy`, `get_contract_info`.

Storage is bounded: latest report per target + 5-entry history per
target + global 100k report cap (uniform `TreeMap[str, str]`, JSON
values). Anyone may request an analysis (public oracle); requesters are
recorded for audit only. Re-analysis replaces "latest" for the target
and appends to the bounded history.

## Repository layout

```
contracts/token_scope.py       the Intelligent Contract
fixtures/solidity/*.sol        15 semantic fixtures (plain ERC20 …
                               prompt-injection, misleading names)
tests/direct/                  149 gltest direct-mode tests
  test_units.py                A–I unit + state + web-failure tests
  test_semantic_fixtures.py    the 15 fixtures through the pipeline
  test_consensus.py            spec consensus cases 1–8 + forgeries
  test_security.py             access/isolation/bounds/injection
scripts/deploy_studionet.py    deploy + live smoke (S1–S6)
scripts/diagnose_wobble.py     LLM classification-stability sampler
frontend/                      single-page dApp (GitHub Pages)
docs/                          DESIGN, SECURITY, EVIDENCE, logs
```

## Running the tests

```bash
pip install "genlayer-test==0.29.2" pytest eth_utils
python -m pytest tests/direct/ -q      # 149 passed
```

CI (`.github/workflows/ci.yml`) runs the same suite on push.

## Limitations (read before consuming a report)

- Reports describe the **verified artifacts Sourcify serves at
  analysis time**. Unverified sibling code, off-chain admin keys,
  proxy targets outside the analyzed artifact set, and future
  re-verification can change reality without changing an old report.
- `PARTIAL_MATCH` sources may not include the full creation runtime;
  ABI-only analyses are flagged `UNCERTAIN_EVIDENCE`.
- The classification is semantic consensus over artifacts — it is not
  a security audit, does not execute the contract, and cannot detect
  behavior that is not present in the analyzed artifacts.
- Semantic edge cases can classify as `UNCERTAIN` by design; that is
  the safe direction, not a defect.

## License

MIT.
