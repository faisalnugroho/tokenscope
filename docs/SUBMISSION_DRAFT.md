# TokenScope — Submission Draft (for the Builder Portal)

The owner pastes/attaches these fields manually. Nothing here claims
steward acceptance; every claim is evidence-backed.

## Category
Builder → Intelligent Contracts

## Title
TokenScope — Semantic Smart-Contract Capability Oracle

## One-liner
TokenScope translates verified smart-contract artifacts (Sourcify v2)
into a structured, consensus-backed capability profile that
applications can consume — what can a privileged party actually do
with this contract?

## Full description
TokenScope is a GenLayer Intelligent Contract that answers one
question about any verified EVM contract: what meaningful
administrative or control capabilities does the verified source
actually expose? It retrieves the contract's verified artifacts from
the public Sourcify API v2 (keyless), classifies 18 taxonomy
capabilities (ownership, mint/burn, pause, blacklist/whitelist, forced
transfer, fees, upgradeability, balance override, rescue, allowances)
through GenLayer's decentralized AI-validator consensus, and stores a
compact deterministic report on-chain for any application to consume.

Why GenLayer is necessary: a deterministic contract can store an ABI
but cannot interpret human-readable source — whether a privileged role
can mint, whether `mint()` actually modifies supply, whether
`deprecate()` is real upgradeability. Independent validators each
fetch the same public artifacts and re-derive the classification; the
Equivalence Principle compares only the stable canonical fields
(verification status + per-capability statuses), never prose. A
DETECTED capability always carries evidence function names grounded
against the fetched artifacts — a hallucinating or injected model
cannot manufacture a DETECTED.

Safety properties (tested adversarially): uncertainty is never
collapsed into NOT_DETECTED; every retrieval/verification/LLM failure
produces an explicit UNAVAILABLE state, never a negative finding;
prompt-injection comments in verified source are ignored (fixtures
with "IGNORE ALL PREVIOUS INSTRUCTIONS" demand mint=NOT_DETECTED; the
stored report reflects behavior); misleading names (a pure `mint()`
stub) do not produce DETECTED. TokenScope does not certify safety —
the UI and docs state this prominently.

Deliverables: 149-test gltest suite (unit/semantic/consensus/
security), 15 Solidity fixtures, live Studionet deployment with a
5-case smoke (positive x2, negative x2, determinism) all
MAJORITY_AGREE, GitHub Pages dApp with real transaction states,
evidence log with tx hashes, and a disclosed consensus-engineering
record (a first-attempt MAJORITY_DISAGREE led to taxonomy-definition
stabilization sampled across 5 live LLM runs — the disagreement tx is
preserved as proof the fail-safe works).

## Links
- Repo: https://github.com/faisalnugroho/tokenscope
- Live explorer (contract):
  https://explorer-studio.genlayer.com/contracts/0xb99689391dEC3322911cf06aE2697D7047D42bF6
- dApp: https://faisalnugroho.github.io/tokenscope/
- Evidence: docs/EVIDENCE.md + docs/deployment_log.json in the repo

## Key evidence transactions (Studionet)
- Deploy (MAJORITY_AGREE): contract `0xb99689391dEC3322911cf06aE2697D7047D42bF6`, code sha256 `37216077dac9623c0265977c18112d56fa41385f06c154fb163986b79ba2d12e`
- S2 USDT positive (3-0, 2 idle): `0x73106499203d7667b10d17ffc5bd384e9ae1adc0024c8e1c705bc7c5b93ebfbf`
- S2b UNI positive (3-2, disclosed): `0xbbb4ace7be0568dd3d2b91c19b095a05598046ff0ffdc36709b78f40869d60ff`
- S3 unverified negative: `0xd5b83835a86c314a96c03b035539f3a3c765ca1ae35e427ae50c89b7956a2483`
- S4 malformed negative: `0xb495a0fa6f608331949ede326086a1d5926e5534408f921fb5bbb86c5700a6e6`
- S5 determinism (identical matrix): `0x08cab99b7ef205912b50584df7391c3b6145f4249a2bdcbe217ec622f0d9ebc0`
- v1 disagreement (fail-safe proof, 1-3):
  `0x5bc83eee449721fc23c88f2402495c649d8cb4f03c4cb00c2460afe68c944ab3`

## Honest scope notes
- Not a security audit; not financial advice; no safety scores.
- Reports describe the verified artifacts Sourcify serves at analysis
  time; they cannot see unverified code, off-chain keys, or proxy
  targets outside the artifact set.
- Studionet deployment (chain 61999) — Bradbury/mainnet deployment
  is future work the owner may choose.
- The consensus model is the network's configured validator set; the
  taxonomy was stability-sampled (5 runs, zero wobble) before the
  final smoke.
