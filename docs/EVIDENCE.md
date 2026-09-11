# TokenScope — Live Evidence

Every claim in this file was produced by a real transaction on
GenLayer Studionet against the FINAL contract:
**`0xb99689391dEC3322911cf06aE2697D7047D42bF6`**
(deployed code byte-identity: `contracts/token_scope.py`, sha256
`37216077dac9623c0265977c18112d56fa41385f06c154fb163986b79ba2d12e`).

Machine-readable log: `docs/deployment_log.json`.
Explorer: https://explorer-studio.genlayer.com/contracts/0xb99689391dEC3322911cf06aE2697D7047D42bF6

## Live smoke results (S2–S6)

All five consensus runs reached **MAJORITY_AGREE** with leader
execution **SUCCESS**; votes were re-derived via raw RPC and are
disclosed per case (idle validators are normal quorum-reached
cancellations, not defects):

| Case | Target | Votes | Consensus | Stored result |
|---|---|---|---|---|
| S2 positive | USDT `0xdAC17…31ec7` (chain 1, PARTIAL_MATCH) | 3 agree / 0 disagree / 2 idle | MAJORITY_AGREE + SUCCESS | COMPLETE; DETECTED: mint, burn, pause, blacklist, fee_control, ownership_detected, ownership_transferable |
| S2b positive | UNI `0x1f98…1F984` (chain 1, PARTIAL_MATCH — verified live: Sourcify reports `match`, not `exact_match`) | **3 agree / 2 disagree** | MAJORITY_AGREE + SUCCESS | COMPLETE; DETECTED: mint, ownership_detected, ownership_renounceable, ownership_transferable, supply_cap |
| S3 negative | unverified address (chain 1) | 3 agree / 0 disagree / 2 idle | MAJORITY_AGREE + SUCCESS | `analysis_status=UNAVAILABLE`, `failure=VERIFICATION/NOT_VERIFIED` — no capability conclusions |
| S4 negative | malformed address | 3 agree / 0 disagree / 2 idle | MAJORITY_AGREE + SUCCESS | `failure=REQUEST/invalid_address` stored as explicit failure |
| S5 determinism | USDT re-analysis | 3 agree / 0 disagree / 2 idle | MAJORITY_AGREE + SUCCESS | identical capability matrix to S2 (verified programmatically) |
| S6 getters | — | — | — | count=10; USDT history exactly the last 5 report ids (bounded storage observed live) |

**S2b disclosure:** UNI passed 3-2. Two validators disagreed on boundary
classifications around UNI's real-world history: its `mint()` function
exists in the verified source while the minter role was renounced to
the zero address (mint is arguably present-but-unusable), and supply
was fixed at construction (supply_cap evidence). The majority
classification committed; the disagreeing votes are visible on the tx
in the explorer. This is disclosed rather than hidden: the Equivalence
Principle worked exactly as designed — disagreement was recorded,
majority ruled, and a genuinely ambiguous case is visible to anyone who
checks. Boundary ambiguity of this kind is precisely what the
UNCERTAIN status exists for, and the taxonomy continues to treat
renounced-role contracts conservatively.

(The per-case tx hashes, decoded return values, and full capability
matrices are in `docs/deployment_log.json`; each tx is verifiable on
the explorer via its `Equivalence Principle Outputs` block.)

## Consensus-stability engineering (the interesting part)

The first full-consensus attempt against the *v1* contract
(`0x39f1…4f613`, tx
`0x5bc83eee449721fc23c88f2402495c649d8cb4f03c4cb00c2460afe68c944ab3`)
produced a **MAJORITY_DISAGREE**: 1 agree / 3 disagree. This was the
designed fail-safe working — nothing was committed — and it exposed a
real Equivalence-Principle engineering problem: independent LLM runs
wobbled on boundary capabilities.

We treated it as a stability bug in the *taxonomy definitions*, not in
the comparison rule, and fixed it empirically before freezing:

1. **Wobble sampling.** `scripts/diagnose_wobble.py` runs the leader
   N times (`leader_only`) against the same live target and diffs the
   canonical capability statuses — sampling the same distribution the
   validator committee draws from.
2. **v1 finding:** `upgradeability`/`upgrade_admin` wobbled on USDT
   (its `deprecate()` sets a migration address — deprecation, not
   proxy upgrade). Fixed by sharpening the definitions with explicit
   negative guidance ("mere deprecation or migration pointers do not
   count").
3. **v2 re-sample:** `upgradeability` stable 5/5; `balance_override`
   wobbled once (USDT's `destroyBlackFunds()` — a subtract-only
   privileged burn, not a set-both-directions balance override).
   Fixed with the same technique.
4. **v3 re-sample:** **all 18 capabilities stable across 5
   independent live LLM runs — zero wobble** (evidence in the run
   transcript below).
5. **v3 full smoke:** every consensus case then reached
   MAJORITY_AGREE + SUCCESS.

Wobble sample (v3, USDT, 5 leader runs):

```
arbitrary_allowance_edit     ['NOT_DETECTED' x5]
balance_override             ['NOT_DETECTED' x5]
blacklist                    ['DETECTED' x5]
burn                         ['DETECTED' x5]
eth_withdraw                 ['NOT_DETECTED' x5]
fee_control                  ['DETECTED' x5]
forced_transfer              ['NOT_DETECTED' x5]
mint                         ['DETECTED' x5]
ownership_detected           ['DETECTED' x5]
ownership_renounceable       ['NOT_DETECTED' x5]
ownership_transferable       ['DETECTED' x5]
pause                        ['DETECTED' x5]
rescue_assets                ['NOT_DETECTED' x5]
role_based_admin             ['NOT_DETECTED' x5]
supply_cap                   ['NOT_DETECTED' x5]
upgrade_admin                ['NOT_DETECTED' x5]
upgradeability               ['NOT_DETECTED' x5]
whitelist                    ['NOT_DETECTED' x5]
WOBBLING CAPS: none — stable
```

The v1 MAJORITY_DISAGREE tx is retained as evidence that the
Equivalence Principle genuinely rejects non-reproducible classifications
(it is visible on the explorer with 3 disagree votes) — and that the
fix was to make the analysis *reproducible*, not to weaken the
comparison.

## Deployed-code byte identity

The final contract was deployed from `contracts/token_scope.py`
exactly as committed. Deploy tx
`0x6981b7cb4940736a65a3976bc85d8ce441d60966c4f6886d33e211552ae138a2`
carries `data.contract_code` (base64 of the full source):

    deployed sha256: 37216077dac9623c0265977c18112d56fa41385f06c154fb163986b79ba2d12e (43016 bytes)
    local     sha256: 37216077dac9623c0265977c18112d56fa41385f06c154fb163986b79ba2d12e (43016 bytes)
    BYTE-IDENTITY: VERIFIED (re-derived 2026-09-11)

Re-run it yourself: `python scripts/verify_byte_identity.py 0x6981b7cb4940736a65a3976bc85d8ce441d60966c4f6886d33e211552ae138a2`

## Earlier iterations (disclosed)

- v1 `0x39f1D47DAfAB7B990BCDf17ed7A8905d3934f613` — deployed to test
  the pipeline end-to-end; S2 analysis (leader output correct) failed
  consensus due to taxonomy-definition wobble; superseded.
- v2 `0xE527a8311ff347201F31c6A37D8a6Ed3D4851aC4` — upgradeability
  fix verified; balance_override wobble found; superseded.
- v3 `0xb99689391dEC3322911cf06aE2697D7047D42bF6` — FINAL. No
  redeployment after the final smoke passed.
