# AI Interaction Log (AI_LOG.md)
**Project**: AI Tech Consultant (BusinessLabs / Anthropic Applied AI Engineering Capstone)  
**Assistant**: Antigravity (Powered by Claude / Gemini models)

---

## 1. Five Useful Prompts Actually Used During Implementation

### Prompt 1: Repository Inspection & Architectural Plan Formulation
- **Prompt**: *"Inspect the repository, identify installed runtimes, and formulate a 4-day incremental implementation plan for the three connected tasks with verifiable acceptance criteria."*
- **Outcome**: Established Python 3.12 + Node v24 + Docker setup, created directory structure, and mapped out inter-service HTTP communication contract between Task 1 (Knowledge Brain) and Tasks 2 & 3.

### Prompt 2: Resumable Sitemap Crawler with Manifest Persistence
- **Prompt**: *"Implement an asynchronous polite crawler for the Brilliant Directories support sitemap XML with exponential backoff, jitter, ETag/Last-Modified tracking, and content hash deduplication in SQLAlchemy."*
- **Outcome**: Built `SitemapCrawler` and `content_extractor` capable of incremental updates, table markdown preservation, and active status tracking without duplicate page fetches.

### Prompt 3: Twenty-Consecutive-Unchanged-Send Autonomy State Machine
- **Prompt**: *"Implement the 20-consecutive-unchanged-send eligibility rule in strict TypeScript. Track qualifying sends with normalized text comparison, reset the counter to zero on edits or rejections, lock out high-risk categories, and monitor quality regression."*
- **Outcome**: Developed `AutonomyEngine` in TypeScript with comprehensive Vitest coverage for 19th, 20th, 21st sends, counter resets, and duplicate send prevention.

### Prompt 4: Multi-Agent Meeting Scoping & Scope Diff Agent
- **Prompt**: *"Build a controlled multi-agent pipeline in Python that extracts requirements from meeting transcripts, checks feasibility via Task 1 Knowledge Brain API, computes PERT 3-point estimates, and calculates scope differences between Meeting A baseline and Meeting C follow-up."*
- **Outcome**: Produced `TranscriptAnalystAgent`, `ProductFeasibilityAgent`, `ScopeAgent`, `EstimationAgent`, `ProposalAgent`, and `ScopeDiffAgent` with immutable baseline preservation.

### Prompt 5: Backend Commercial Approval Gate Enforcement
- **Prompt**: *"Enforce human approval controls in backend business logic so that unapproved commercial proposals cannot be sent, returning HTTP 403 Forbidden on direct API bypass attempts."*
- **Outcome**: Implemented `HumanApprovalGate` verifying reviewer identity and timestamp, successfully validated by automated integration tests.

---

## 2. Genuine Rejection & Correction Example

### Rejected Generated Work: Naive Substring Matching in Email Classifier
- **Generated Code**:
  ```typescript
  // Initial implementation in classifier.ts
  if (text.includes("0 members")) {
    return { category: "troubleshooting", ... };
  }
  ```
- **Observed Failure**: When evaluating email fixture `email_007` ("How to bulk import 10,000 members from CSV?"), the classifier incorrectly flagged the email as `troubleshooting` rather than `how_to`.
- **Reason for Rejection**: The text `"10,000 members"` matched the substring `"0 members"`, causing standard bulk import configuration inquiries to be misclassified as zero-result troubleshooting errors.
- **Corrected Implementation**: Replaced the naive substring check with a word-boundary regular expression:
  ```typescript
  if (/\b0 members\b/.test(text)) {
    return { category: "troubleshooting", ... };
  }
  ```
  This immediately resolved the false positive and achieved 100% test accuracy across the evaluation suite.
