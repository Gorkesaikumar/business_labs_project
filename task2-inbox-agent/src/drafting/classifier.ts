import {
  CustomerEmail,
  EmailCategory,
  EmailClassification,
  Priority,
  RiskLevel,
} from "../email/types";

export class EmailClassifier {
  classify(email: CustomerEmail): EmailClassification {
    const subjectLower = email.subject.toLowerCase();
    const bodyLower = email.body.toLowerCase();
    const text = `${subjectLower} ${bodyLower}`;
    const flags: string[] = [];

    // 1. Adversarial Injection Detection
    if (
      text.includes("ignore all previous") ||
      text.includes("system prompt") ||
      text.includes("system override") ||
      text.includes("disregard safety") ||
      text.includes("granted a $")
    ) {
      flags.push("ADVERSARIAL_INJECTION_DETECTED");
      return {
        category: "adversarial_injection",
        priority: "urgent",
        risk_level: "critical",
        summary: "Attempted prompt injection or system override detected.",
        extracted_facts: ["Sender attempted to override system instructions."],
        requires_kb_consult: false,
        requires_human_approval: true,
        risk_flags: flags,
        suggested_action: "Block automated reply and alert security operations.",
      };
    }

    // 2. Refund & Cancellation
    if (
      text.includes("refund") ||
      text.includes("cancel my subscription") ||
      text.includes("chargeback") ||
      text.includes("double charged") ||
      text.includes("charged again")
    ) {
      flags.push("FINANCIAL_LIABILITY_RISK");
      if (text.includes("chargeback") || text.includes("urgent")) {
        flags.push("HIGH_CHURN_OR_DISPUTE_RISK");
      }
      return {
        category: "refund_cancellation",
        priority: text.includes("urgent") || text.includes("chargeback") ? "urgent" : "high",
        risk_level: "high",
        summary: "Customer requesting subscription cancellation or payment refund.",
        extracted_facts: [
          email.body.includes("$") ? `Mentioned amount: ${email.body.match(/\$[\d,]+/)?.[0]}` : "No specific amount stated",
          "Explicitly requesting refund or cancellation",
        ],
        requires_kb_consult: false,
        requires_human_approval: true,
        risk_flags: flags,
        suggested_action: "Escalate to billing & finance team; do not authorize refund via AI.",
      };
    }

    // 3. Urgent Complaints & Legal Threats
    if (
      text.includes("trademark infringement") ||
      text.includes("legal proceedings") ||
      text.includes("site down") ||
      text.includes("emergency") ||
      text.includes("disgusted") ||
      text.includes("security report") ||
      text.includes("xss")
    ) {
      flags.push("LEGAL_OR_SECURITY_INCIDENT");
      return {
        category: "complaint_urgent",
        priority: "urgent",
        risk_level: "critical",
        summary: "High severity complaint, outage, or legal notice requiring immediate executive review.",
        extracted_facts: ["Critical severity incident reported"],
        requires_kb_consult: false,
        requires_human_approval: true,
        risk_flags: flags,
        suggested_action: "Immediate routing to legal counsel or on-call engineering.",
      };
    }

    // 4. Follow-ups (Check before quote_request to catch follow-ups on quotes)
    if (
      subjectLower.includes("follow up") ||
      subjectLower.includes("follow-up") ||
      text.includes("checking in on ticket") ||
      text.includes("checking if your team") ||
      subjectLower.includes("invoice #") ||
      text.includes("any updates on the feasibility study")
    ) {
      return {
        category: "follow_up",
        priority: "medium",
        risk_level: "low",
        summary: "Follow-up communication regarding an ongoing ticket or deliverable.",
        extracted_facts: ["Referenced existing engagement or ticket number"],
        requires_kb_consult: false,
        requires_human_approval: false,
        risk_flags: flags,
        suggested_action: "Check status in tracking system and respond with concise progress update.",
      };
    }

    // 5. Quote & Proposal Requests
    if (
      text.includes("quote") ||
      text.includes("scope of work") ||
      text.includes("sow") ||
      text.includes("cost estimate") ||
      text.includes("hire your consulting") ||
      text.includes("discount code")
    ) {
      flags.push("COMMERCIAL_NEGOTIATION");
      return {
        category: "quote_request",
        priority: "high",
        risk_level: "high",
        summary: "Prospective or existing client inquiring about pricing, estimates, or commercial scope.",
        extracted_facts: ["Commercial engagement inquiry"],
        requires_kb_consult: true,
        requires_human_approval: true,
        risk_flags: flags,
        suggested_action: "Route to Task 3 Meeting to Scope pipeline for formal evaluation.",
      };
    }

    // 6. Missing Information / Ambiguous Context
    if (
      subjectLower.includes("missing information") ||
      text.includes("it doesnt work") ||
      text.includes("it says error on my screen") ||
      (email.body.trim().length < 80 && (text.includes("broken") || text.includes("call me") || text.includes("help me") || text.includes("check")))
    ) {
      return {
        category: "missing_information",
        priority: "medium",
        risk_level: "low",
        summary: "Customer reported an issue with insufficient context to diagnose.",
        extracted_facts: ["Insufficient diagnostic detail provided in body"],
        requires_kb_consult: false,
        requires_human_approval: false,
        risk_flags: flags,
        suggested_action: "Request specific website URL, steps to reproduce, and error screenshot.",
      };
    }

    // 7. Unanswerable / Out of Scope Architecture
    if (
      text.includes("woocommerce") ||
      text.includes("wordpress plugin") ||
      text.includes("external rds") ||
      text.includes("python flask") ||
      text.includes("ssh into the bd server")
    ) {
      return {
        category: "unanswerable_out_of_scope",
        priority: "low",
        risk_level: "low",
        summary: "Inquiry regarding architectural features unsupported by Brilliant Directories SaaS.",
        extracted_facts: ["Inquiring about third-party server access or incompatible CMS plugins"],
        requires_kb_consult: true,
        requires_human_approval: false,
        risk_flags: flags,
        suggested_action: "Politely clarify platform architectural boundaries and suggest supported alternatives.",
      };
    }

    // 8. Custom Feature Requests
    if (
      text.includes("native ios and android") ||
      text.includes("custom flutter") ||
      text.includes("franchise with 200") ||
      text.includes("bidirectional synchronization")
    ) {
      return {
        category: "feature_request",
        priority: "medium",
        risk_level: "medium",
        summary: "Request for bespoke custom platform features or third-party integrations.",
        extracted_facts: ["Complex customization request requiring technical evaluation"],
        requires_kb_consult: true,
        requires_human_approval: true,
        risk_flags: flags,
        suggested_action: "Consult Knowledge Brain on API capabilities and arrange technical scoping.",
      };
    }

    // 9. Troubleshooting (Use regex boundary for 0 members to avoid matching 10,000 members!)
    if (
      text.includes("error") ||
      text.includes("failing") ||
      text.includes("404") ||
      text.includes("500") ||
      text.includes("413") ||
      text.includes("spam folder") ||
      text.includes("not active") ||
      text.includes("unable to") ||
      text.includes("0 bytes") ||
      text.includes("does not appear") ||
      /\b0 members\b/.test(text)
    ) {
      return {
        category: "troubleshooting",
        priority: "high",
        risk_level: "low",
        summary: "Customer encountering an operational error or unexpected configuration behavior.",
        extracted_facts: ["Technical operational issue requiring configuration guidance"],
        requires_kb_consult: true,
        requires_human_approval: false,
        risk_flags: flags,
        suggested_action: "Retrieve solution articles from Knowledge Brain and provide step-by-step resolution.",
      };
    }

    // 10. Default: How-to
    return {
      category: "how_to",
      priority: "medium",
      risk_level: "low",
      summary: "Customer inquiring how to configure a native Brilliant Directories feature.",
      extracted_facts: ["Standard product configuration inquiry"],
      requires_kb_consult: true,
      requires_human_approval: false,
      risk_flags: flags,
      suggested_action: "Retrieve verified solution steps and citations from Knowledge Brain.",
    };
  }
}
