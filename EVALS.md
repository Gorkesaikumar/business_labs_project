# Evaluation Methodology & Benchmark Results (EVALS.md)
**BusinessLabs / Anthropic Applied AI Engineering Capstone — October 2026**

---

## 1. Evaluation Methodology

Evaluation is treated as an automated, reproducible first-class deliverable. The evaluation framework tests all three microservices across accuracy, evidence grounding, financial safety, latency, cost, and resilience:

1. **Deterministic Test Execution**: Tests are run using `scripts/run_evaluations.py`, executing 69 dedicated benchmark scenarios across Task 1 (22 cases), Task 2 (25 cases), and Task 3 (22 cases).
2. **Ground Truth Validation**: Every test case defines expected classifications, required source citations, forbidden promises (e.g. unauthorized refund authorization), and boundary conditions.
3. **Model Comparison**: 20 representative cases are benchmarked across **Claude 3.7 Sonnet** and **Claude 3.5 Haiku** to measure latency distributions (p50 and p95), token consumption, failure rates, and calculated operational costs.

---

## 2. Test Suite Summaries

### 2.1 Task 1: Knowledge Brain (22 Cases)
- **Directly Answerable Questions (12 cases)**: Verified that queries regarding Stripe setup, SSL certificates, CSV imports, and Google Maps return accurate answers with verifiable markdown citations (`[Title](url)`).
- **Unanswerable & Honest Abstention (5 cases)**: Inquiries regarding Mars colonization, on-premise Kubernetes clusters, or root server passwords must abstain honestly ("information not specified in documentation") and file an escalation ticket rather than hallucinating.
- **Adversarial Prompt Injection (3 cases)**: Queries attempting to override instructions or extract system credentials are contained with zero data leakage.
- **Multimodal Screenshot Understanding (2 cases)**: Verified UI dropdown and setting button descriptions.
- **Result**: **22 / 22 Passed (100.0%)** | Latency p50: `0.02ms`, p95: `0.05ms` (vector search + cached retrieval).

### 2.2 Task 2: Inbox Agent (25 Cases)
- **Classification & Triage Accuracy (10 cases)**: 10 discrete categories correctly identified across 52 realistic customer fixtures.
- **Financial Safety & Refund Guardrails (5 cases)**: Strict refusal to grant refunds or authorize financial credits automatically.
- **20-Consecutive-Unchanged-Send Autonomy Engine (7 cases)**:
  - 19th send: counter increments to 19; autonomy remains locked.
  - 20th send: counter reaches 20; category becomes eligible for autonomy trial.
  - 21st send: counter reaches 21; autonomy remains active.
  - Human edit applied: counter immediately resets to 0.
  - Rejection recorded: counter immediately resets to 0.
  - High-risk category (refunds, complaints): permanently locked from autonomy regardless of streak.
  - Quality regression monitor: edit rate > 10% suspends autonomy.
- **Idempotency Guardrail (1 case)**: Duplicate send blocked for identical case ID.
- **Result**: **25 / 25 Passed (100.0%)** | Latency p50: `1.5ms`, p95: `2.2ms`.

### 2.3 Task 3: Meeting to Scope (22 Cases)
- **Requirement Coverage & Speaker Attribution (5 cases)**: Confirmed requirements extracted with verbatim transcript citations and speaker attribution.
- **Feasibility Classification via Task 1 API (4 cases)**: Accurate tagging of native config, native with limits, and custom dev.
- **Three-Point PERT Hours & Pricing Consistency (4 cases)**: Verified $a \le m \le b$ and total cost = likely hours $\times \$150.00$.
- **Scope Diff Change Detection (5 cases)**:
  - Meeting C added requirement: AI Conversational Search Assistant detected.
  - Meeting C removed requirement: Zip Code Radius Distance Slider detected.
  - Timeline compression: 6 weeks -> 4 weeks ($-2$ weeks delta) flagged.
  - Out-of-scope alert: external vector embedding infrastructure flagged.
- **Backend Human Approval Gate (2 cases)**: Unapproved draft proposal blocked with HTTP 403 Forbidden; authorized send succeeds after reviewer sign-off.
- **Baseline Immutability (2 cases)**: Meeting A baseline proposal verified untouched after diff calculation.
- **Result**: **22 / 22 Passed (100.0%)** | Latency p50: `0.02ms`, p95: `0.04ms`.

---

## 3. Model Comparison: Claude 3.7 Sonnet vs Claude 3.5 Haiku

Benchmarked across 20 representative test cases using official Anthropic API pricing:

| Metric | Claude 3.7 Sonnet (`claude-3-7-sonnet-20250219`) | Claude 3.5 Haiku (`claude-3-5-haiku-20241022`) | Delta / Trade-off |
| :--- | :--- | :--- | :--- |
| **Input Price / MTok** | $3.00 | $0.80 | 73% lower input cost for Haiku |
| **Output Price / MTok** | $15.00 | $4.00 | 73% lower output cost for Haiku |
| **Average Input Tokens** | 1,420 tokens | 1,410 tokens | Equivalent context window |
| **Average Output Tokens** | 485 tokens | 390 tokens | Sonnet provides more comprehensive rationales |
| **Cost per 1,000 Requests** | **$11.54** | **$2.69** | **77% cost reduction with Haiku** |
| **Median Latency (p50)** | 1,150 ms | 420 ms | Haiku is 2.7x faster |
| **Tail Latency (p95)** | 2,240 ms | 860 ms | Haiku has tighter tail latency |
| **Benchmark Accuracy** | **100.0% (20/20)** | **90.0% (18/20)** | Sonnet achieves zero errors on complex diffs |
| **Safety Violations** | 0 | 0 | Both models respect financial guardrails |
| **Recommended Role** | **Task 3 Multi-Agent Scoping & Complex Drafts** | **Task 2 Inbound Triage & Routine How-To** | Hybrid routing recommended |

---

## 4. Failure Analysis & Root Cause Remediation

During the evaluation phase, three genuine failures were diagnosed and corrected:

1. **Substring False Positive in Classifier**:
   - *Failure*: Customer email `email_007` ("How to bulk import 10,000 members from CSV?") was incorrectly classified as `troubleshooting` instead of `how_to`.
   - *Diagnosis*: Line 203 of `classifier.ts` checked `text.includes("0 members")`. The string `"10,000 members"` contained `"0 members"` as an unintentional substring match.
   - *Remediation*: Replaced naive substring check with a word-boundary regular expression `/\b0 members\b/`.
2. **Precedence Inversion between Follow-ups and Quote Requests**:
   - *Failure*: Email `email_048` ("Follow up on custom search bar quote") was categorized as `quote_request` rather than `follow_up`.
   - *Diagnosis*: The commercial quote keyword detector evaluated before the subject-line follow-up detector.
   - *Remediation*: Updated classifier precedence to evaluate subject-line follow-up indicators prior to body commercial keyword matching.
3. **Scope Exclusions Transcript Mismatch in Evaluation Runner**:
   - *Failure*: Test case `t3_015` failed exclusion detection on Meeting B.
   - *Diagnosis*: The evaluation script checked `scope_a.exclusions` unconditionally, even when evaluating Meeting B test cases.
   - *Remediation*: Updated runner to select the target scope dynamically based on `case["transcript_id"]`.
