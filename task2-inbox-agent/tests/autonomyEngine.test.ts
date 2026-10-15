import { describe, it, expect, beforeEach } from "vitest";
import { AutonomyEngine } from "../src/autonomy/autonomyEngine";
import { EmailDraft } from "../src/email/types";

describe("AutonomyEngine (20-consecutive-unchanged-send rule)", () => {
  let engine: AutonomyEngine;

  const createMockDraft = (caseId: string, category: any = "how_to", reply: string = "Standard reply"): EmailDraft => ({
    draft_id: `draft_${caseId}`,
    case_id: caseId,
    sender: "user@example.com",
    subject: "Question",
    classification: {
      category,
      priority: "medium",
      risk_level: "low",
      summary: "Summary",
      extracted_facts: [],
      requires_kb_consult: true,
      requires_human_approval: category !== "how_to",
      risk_flags: [],
      suggested_action: "Send",
    },
    proposed_reply: reply,
    citations: [{
      article_id: "art_1",
      url: "https://support.bd.com/art_1",
      title: "Doc 1",
      passage: "Text",
      relevance_score: 0.9,
      screenshot_urls: [],
    }],
    is_autonomous_candidate: category === "how_to",
    status: "pending_review",
    model_version: "claude-3-7-sonnet",
    prompt_version: "v1.0",
    created_at: new Date().toISOString(),
  });

  beforeEach(() => {
    engine = new AutonomyEngine({ threshold: 20, allowedAutonomousCategories: ["how_to"], maxEditRatePercent: 10 });
  });

  it("should track 19th, 20th, and 21st qualifying sends accurately", () => {
    // 19 consecutive unchanged approvals
    for (let i = 1; i <= 19; i++) {
      const draft = createMockDraft(`case_${i}`);
      const res = engine.recordReviewDecision(draft, {
        action: "approve_send",
        reviewerId: "agent_1",
      });
      expect(res.success).toBe(true);
      expect(engine.getConsecutiveCount("how_to")).toBe(i);
      expect(engine.isCategoryEligible("how_to")).toBe(false);
    }

    // 20th qualifying send -> reaches threshold!
    const draft20 = createMockDraft("case_20");
    const res20 = engine.recordReviewDecision(draft20, {
      action: "approve_send",
      reviewerId: "agent_1",
    });
    expect(res20.success).toBe(true);
    expect(engine.getConsecutiveCount("how_to")).toBe(20);
    expect(engine.isCategoryEligible("how_to")).toBe(true);

    // 21st qualifying send -> remains eligible
    const draft21 = createMockDraft("case_21");
    const res21 = engine.recordReviewDecision(draft21, {
      action: "approve_send",
      reviewerId: "agent_1",
    });
    expect(res21.success).toBe(true);
    expect(engine.getConsecutiveCount("how_to")).toBe(21);
    expect(engine.isCategoryEligible("how_to")).toBe(true);
  });

  it("should reset counter to 0 immediately upon human edit", () => {
    // Accumulate 15 consecutive unchanged sends
    for (let i = 1; i <= 15; i++) {
      const draft = createMockDraft(`case_edit_${i}`);
      engine.recordReviewDecision(draft, { action: "approve_send", reviewerId: "agent_1" });
    }
    expect(engine.getConsecutiveCount("how_to")).toBe(15);

    // 16th send is edited by a human reviewer
    const draft16 = createMockDraft("case_edit_16", "how_to", "Original draft text");
    const res16 = engine.recordReviewDecision(draft16, {
      action: "edit_send",
      edited_content: "Manually edited and corrected response text.",
      reviewerId: "reviewer_lead",
      editReason: "Missing specific link",
    });

    expect(res16.success).toBe(true);
    // Counter MUST reset to 0!
    expect(engine.getConsecutiveCount("how_to")).toBe(0);
    expect(engine.isCategoryEligible("how_to")).toBe(false);
    expect(engine.getStatus("how_to").last_reset_reason).toContain("Human edit applied");
  });

  it("should reset counter to 0 immediately upon rejection", () => {
    // Accumulate 8 consecutive sends
    for (let i = 1; i <= 8; i++) {
      const draft = createMockDraft(`case_rej_${i}`);
      engine.recordReviewDecision(draft, { action: "approve_send", reviewerId: "agent_1" });
    }
    expect(engine.getConsecutiveCount("how_to")).toBe(8);

    // Rejection occurs
    const draftReject = createMockDraft("case_rej_9");
    const resReject = engine.recordReviewDecision(draftReject, {
      action: "reject",
      reviewerId: "lead_qa",
      editReason: "Inaccurate procedural step",
    });

    expect(resReject.success).toBe(true);
    expect(engine.getConsecutiveCount("how_to")).toBe(0);
    expect(engine.isCategoryEligible("how_to")).toBe(false);
  });

  it("should strictly exclude high-risk categories like refunds from autonomy regardless of counter", () => {
    const refundDraft = createMockDraft("refund_1", "refund_cancellation");
    for (let i = 1; i <= 25; i++) {
      engine.recordReviewDecision(createMockDraft(`refund_${i}`, "refund_cancellation"), {
        action: "approve_send",
        reviewerId: "finance_agent",
      });
    }

    // Even with 25 approvals, refund_cancellation MUST NEVER be eligible for autonomous send
    expect(engine.isCategoryEligible("refund_cancellation")).toBe(false);
    const candidateCheck = engine.processAutonomousCandidate(refundDraft);
    expect(candidateCheck.canAutoSend).toBe(false);
    expect(candidateCheck.reason).toContain("high-risk");
  });

  it("should prevent duplicate sends for the same case ID", () => {
    const draft = createMockDraft("dup_case_1");
    const res1 = engine.recordReviewDecision(draft, { action: "approve_send", reviewerId: "agent_1" });
    expect(res1.success).toBe(true);

    // Attempt second send with same case_id
    const res2 = engine.recordReviewDecision(draft, { action: "approve_send", reviewerId: "agent_1" });
    expect(res2.success).toBe(false);
    expect(res2.message).toContain("Duplicate send prevented");
  });
});
