import {
  CustomerEmail,
  EmailClassification,
  EmailDraft,
  KnowledgeBrainResponse,
} from "../email/types";
import { KnowledgeBrainClient } from "../knowledge-client/knowledgeClient";

export interface DrafterOptions {
  useMock?: boolean;
  model?: string;
  promptVersion?: string;
}

export class EmailDrafter {
  private kbClient: KnowledgeBrainClient;
  private useMock: boolean;
  private model: string;
  private promptVersion: string;

  constructor(options: DrafterOptions = {}) {
    this.kbClient = new KnowledgeBrainClient();
    this.useMock = options.useMock ?? (process.env.USE_MOCK_LLM !== "false");
    this.model = options.model || process.env.ANTHROPIC_MODEL || "claude-3-7-sonnet-20250219";
    this.promptVersion = options.promptVersion || "v1.2.0-grounded";
  }

  async draft(
    email: CustomerEmail,
    classification: EmailClassification
  ): Promise<EmailDraft> {
    const draftId = `draft_${Date.now()}_${Math.random().toString(36).substring(7)}`;
    let citations: any[] = [];
    let kbStatus = "not_consulted";
    let proposedReply = "";

    // 1. Consult Task 1 Knowledge Brain if required
    if (classification.requires_kb_consult) {
      const kbQuery = `${email.subject}. ${email.body.substring(0, 300)}`;
      const kbResponse: KnowledgeBrainResponse = await this.kbClient.query(kbQuery, {
        sender: email.sender,
        category: classification.category,
      });

      citations = kbResponse.sources;
      kbStatus = kbResponse.status;

      if (kbResponse.status === "answered" && kbResponse.sources.length > 0) {
        const topSource = kbResponse.sources[0];
        proposedReply =
          `Hi ${email.sender.split("@")[0]},\n\n` +
          `Thank you for contacting support regarding "${email.subject}".\n\n` +
          `Based on our documentation in [${topSource.title}](${topSource.url}):\n\n` +
          `${kbResponse.answer}\n\n` +
          `If you have any further questions, feel free to reply directly to this email.\n\n` +
          `Best regards,\nAI Tech Support Team`;
      } else {
        proposedReply =
          `Hi ${email.sender.split("@")[0]},\n\n` +
          `Thank you for reaching out regarding "${email.subject}".\n\n` +
          `Our technical documentation does not have an immediate automated resolution for this specific setup. ` +
          `We have opened an escalation review ticket with our senior engineering team, and a technical specialist will follow up shortly.\n\n` +
          `Best regards,\nTechnical Support Team`;
      }
    } else {
      // Non-KB categories: Handle specific business logic safely
      switch (classification.category) {
        case "refund_cancellation":
          proposedReply =
            `Hi ${email.sender.split("@")[0]},\n\n` +
            `Thank you for contacting our billing department regarding your cancellation request.\n\n` +
            `We take your inquiry very seriously and have routed your request directly to our senior finance team for immediate manual review. ` +
            `A billing specialist will inspect your account history and follow up with you within one business day.\n\n` +
            `Please note that automatic refunds cannot be issued without account verification.\n\n` +
            `Sincerely,\nBilling Operations`;
          break;

        case "complaint_urgent":
          proposedReply =
            `Hi ${email.sender.split("@")[0]},\n\n` +
            `We have received your urgent message regarding "${email.subject}".\n\n` +
            `This matter has been escalated with the highest priority to our lead management and engineering team for immediate investigation. ` +
            `We are actively reviewing the details provided and will follow up with an update shortly.\n\n` +
            `Sincerely,\nExecutive Escalations Team`;
          break;

        case "quote_request":
          proposedReply =
            `Hi ${email.sender.split("@")[0]},\n\n` +
            `Thank you for your interest in our consulting services for "${email.subject}".\n\n` +
            `To provide you with an accurate scope of work, technical feasibility breakdown, and verified hour estimate, ` +
            `our technical architect will review your project requirements and prepare a formal proposal.\n\n` +
            `We will contact you within 24 hours with next steps or discovery call availability.\n\n` +
            `Best regards,\nBusinessLabs Solutions Advisory`;
          break;

        case "missing_information":
          proposedReply =
            `Hi ${email.sender.split("@")[0]},\n\n` +
            `Thank you for contacting support. In order to help you quickly diagnose and resolve the issue, ` +
            `could you please provide:\n` +
            `1. Your website domain or admin URL.\n` +
            `2. The specific page or member account where this behavior occurs.\n` +
            `3. A screenshot or exact text of any error message shown.\n\n` +
            `Once we have these details, we will investigate right away.\n\n` +
            `Best regards,\nTechnical Support Team`;
          break;

        case "adversarial_injection":
          proposedReply =
            `Your message has been flagged for audit review. Automated execution of system overrides is prohibited. ` +
            `An administrator has been notified.`;
          break;

        case "follow_up":
          proposedReply =
            `Hi ${email.sender.split("@")[0]},\n\n` +
            `Thank you for following up regarding "${email.subject}".\n\n` +
            `Our team is currently reviewing your ticket status and will provide an updated status report shortly.\n\n` +
            `Best regards,\nTechnical Support Team`;
          break;

        default:
          proposedReply =
            `Hi ${email.sender.split("@")[0]},\n\n` +
            `Thank you for reaching out. We have logged your request and our support team will respond shortly.\n\n` +
            `Best regards,\nCustomer Care`;
      }
    }

    const isAutonomousCandidate =
      classification.category === "how_to" &&
      !classification.requires_human_approval &&
      citations.length > 0;

    return {
      draft_id: draftId,
      case_id: email.case_id,
      sender: email.sender,
      subject: email.subject,
      classification,
      proposed_reply: proposedReply,
      citations,
      kb_status: kbStatus,
      is_autonomous_candidate: isAutonomousCandidate,
      status: "pending_review",
      model_version: this.useMock ? "mock-claude-3-7-sonnet" : this.model,
      prompt_version: this.promptVersion,
      created_at: new Date().toISOString(),
    };
  }
}
