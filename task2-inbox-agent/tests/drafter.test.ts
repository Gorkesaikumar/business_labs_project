import { describe, it, expect, vi } from "vitest";
import { EmailDrafter } from "../src/drafting/drafter";
import { EmailClassifier } from "../src/drafting/classifier";

describe("EmailDrafter", () => {
  const classifier = new EmailClassifier();
  const drafter = new EmailDrafter({ useMock: true });

  it("should draft evidence-grounded replies with citations for how-to questions", async () => {
    const email = {
      case_id: "how_to_stripe",
      subject: "How do I configure Stripe?",
      sender: "sarah@example.com",
      body: "Please guide us on how to connect Stripe in Brilliant Directories.",
    };

    const classification = classifier.classify(email);
    const draft = await drafter.draft(email, classification);

    expect(draft.classification.category).toBe("how_to");
    expect(draft.proposed_reply).toContain("Stripe");
    expect(draft.status).toBe("pending_review");
    expect(draft.model_version).toBeDefined();
  });

  it("should never promise or authorize automatic refunds in drafts", async () => {
    const email = {
      case_id: "refund_test",
      subject: "Demanding refund for $1,450",
      sender: "marcus@example.com",
      body: "I demand an immediate full refund of $1,450 or I will chargeback.",
    };

    const classification = classifier.classify(email);
    const draft = await drafter.draft(email, classification);

    expect(draft.classification.category).toBe("refund_cancellation");
    // Proposed reply must NOT promise a refund was issued
    expect(draft.proposed_reply).toContain("finance team");
    expect(draft.proposed_reply).toContain("automatic refunds cannot be issued");
    expect(draft.classification.requires_human_approval).toBe(true);
  });

  it("should ask clear diagnostic questions when email lacks information", async () => {
    const email = {
      case_id: "missing_info_test",
      subject: "it doesnt work",
      sender: "user@example.com",
      body: "hey my website search is broken can you fix it",
    };

    const classification = classifier.classify(email);
    const draft = await drafter.draft(email, classification);

    expect(draft.classification.category).toBe("missing_information");
    expect(draft.proposed_reply).toContain("Your website domain or admin URL");
    expect(draft.proposed_reply).toContain("screenshot");
  });
});
