import { describe, it, expect } from "vitest";
import { AuditStore } from "../src/feedback/auditStore";
import { EmailDraft } from "../src/email/types";
import { SendEvent } from "../src/autonomy/autonomyEngine";

describe("AuditStore", () => {
  it("should record drafts, sends, edits, and analyze feedback recurrence", () => {
    const store = new AuditStore();

    const mockDraft: EmailDraft = {
      draft_id: "draft_123",
      case_id: "case_123",
      sender: "client@example.com",
      subject: "Setup inquiry",
      classification: {
        category: "how_to",
        priority: "medium",
        risk_level: "low",
        summary: "Setup inquiry",
        extracted_facts: [],
        requires_kb_consult: true,
        requires_human_approval: false,
        risk_flags: [],
        suggested_action: "Send",
      },
      proposed_reply: "Here are the steps to configure settings.",
      citations: [],
      is_autonomous_candidate: true,
      status: "edited_sent",
      model_version: "claude-3-7-sonnet",
      prompt_version: "v1.2.0",
      created_at: new Date().toISOString(),
    };

    const mockEvent: SendEvent = {
      eventId: "ev_123",
      draftId: "draft_123",
      caseId: "case_123",
      category: "how_to",
      originalDraftText: "Here are the steps to configure settings.",
      finalSentText: "Here are the steps to configure settings. Link: https://support.bd.com",
      wasUnchanged: false,
      action: "edit_send",
      reviewerId: "qa_agent",
      editReason: "Added direct link to documentation",
      timestamp: new Date().toISOString(),
    };

    store.record(mockDraft, mockEvent);

    const feedback = store.analyzeFeedback();
    expect(feedback.totalRecords).toBe(1);
    expect(feedback.editedSends).toBe(1);
    expect(feedback.unchangedSends).toBe(0);
    expect(feedback.recurringEditReasons["Added direct link to documentation"]).toBe(1);
  });
});
