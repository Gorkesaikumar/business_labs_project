import {
  EmailCategory,
  EmailDraft,
  AutonomyStatus,
  ReviewAction,
} from "../email/types";

export interface AutonomyConfig {
  threshold?: number;
  allowedAutonomousCategories?: EmailCategory[];
  maxEditRatePercent?: number; // e.g. 10%
}

export interface SendEvent {
  eventId: string;
  draftId: string;
  caseId: string;
  category: EmailCategory;
  originalDraftText: string;
  finalSentText: string;
  wasUnchanged: boolean;
  action: "approve_send" | "edit_send" | "reject" | "autonomous_send";
  reviewerId?: string;
  editReason?: string;
  timestamp: string;
}

export function normalizeContent(text: string): string {
  return text
    .replace(/\r\n/g, "\n")
    .split("\n")
    .map((line) => line.trim())
    .join("\n")
    .trim();
}

export class AutonomyEngine {
  private threshold: number;
  private allowedCategories: Set<EmailCategory>;
  private maxEditRatePercent: number;

  // Category -> consecutive count
  private consecutiveCounts: Map<EmailCategory, number> = new Map();
  // Category -> list of recent sends (for quality monitoring)
  private sendHistory: SendEvent[] = [];
  // Sent case IDs to prevent duplicate sends
  private sentCaseIds: Set<string> = new Set();
  // Category -> last reset reason
  private resetReasons: Map<EmailCategory, string> = new Map();

  constructor(config: AutonomyConfig = {}) {
    this.threshold = config.threshold ?? 20;
    this.allowedCategories = new Set(
      config.allowedAutonomousCategories ?? ["how_to"]
    );
    this.maxEditRatePercent = config.maxEditRatePercent ?? 10.0;
  }

  getConsecutiveCount(category: EmailCategory): number {
    return this.consecutiveCounts.get(category) ?? 0;
  }

  isCategoryEligible(category: EmailCategory): boolean {
    if (!this.allowedCategories.has(category)) {
      return false; // High risk categories are strictly forbidden
    }
    const count = this.getConsecutiveCount(category);
    return count >= this.threshold && !this.isQualityRegressed(category);
  }

  isQualityRegressed(category: EmailCategory): boolean {
    const recent = this.sendHistory
      .filter((e) => e.category === category)
      .slice(-10); // Look at last 10 sends

    if (recent.length < 5) {
      return false; // Need minimum volume to trigger regression
    }

    const editCount = recent.filter((e) => !e.wasUnchanged).length;
    const rate = (editCount / recent.length) * 100;
    return rate > this.maxEditRatePercent;
  }

  getStatus(category: EmailCategory): AutonomyStatus {
    const count = this.getConsecutiveCount(category);
    const recent = this.sendHistory.filter((e) => e.category === category).slice(-10);
    const edits = recent.filter((e) => !e.wasUnchanged).length;
    const errorRate = recent.length > 0 ? (edits / recent.length) * 100 : 0;
    const regressed = this.isQualityRegressed(category);
    const isAllowed = this.allowedCategories.has(category);

    return {
      category,
      consecutive_unchanged_sends: count,
      threshold: this.threshold,
      is_eligible: isAllowed && count >= this.threshold && !regressed,
      is_active: isAllowed && count >= this.threshold && !regressed,
      recent_edits_count: edits,
      recent_sends_count: recent.length,
      error_rate: Math.round(errorRate * 10) / 10,
      safety_lock: !isAllowed || regressed,
      last_reset_reason: this.resetReasons.get(category) ?? null,
    };
  }

  recordReviewDecision(
    draft: EmailDraft,
    action: ReviewAction
  ): { success: boolean; message: string; sendEvent?: SendEvent } {
    const category = draft.classification.category;
    const normalizedOriginal = normalizeContent(draft.proposed_reply);

    // Prevent duplicate send
    if (this.sentCaseIds.has(draft.case_id) && action.action !== "reject") {
      return {
        success: false,
        message: `Duplicate send prevented: Case ID ${draft.case_id} has already been sent.`,
      };
    }

    if (action.action === "reject") {
      // Rejection resets the consecutive counter immediately!
      this.consecutiveCounts.set(category, 0);
      this.resetReasons.set(category, `Reviewer rejected draft ${draft.draft_id}: ${action.edit_reason || "No reason given"}`);

      const event: SendEvent = {
        eventId: `ev_${Date.now()}_${Math.random().toString(36).substring(7)}`,
        draftId: draft.draft_id,
        caseId: draft.case_id,
        category,
        originalDraftText: draft.proposed_reply,
        finalSentText: "",
        wasUnchanged: false,
        action: "reject",
        reviewerId: action.reviewer_id,
        editReason: action.edit_reason,
        timestamp: new Date().toISOString(),
      };
      this.sendHistory.push(event);

      return {
        success: true,
        message: `Draft rejected. Consecutive unchanged count for ${category} reset to 0.`,
        sendEvent: event,
      };
    }

    if (action.action === "edit_send") {
      const normalizedSent = normalizeContent(action.edited_content || "");
      const isActuallyUnchanged = normalizedOriginal === normalizedSent;

      if (!isActuallyUnchanged) {
        // Human edited the reply -> RESET counter to 0!
        this.consecutiveCounts.set(category, 0);
        this.resetReasons.set(
          category,
          `Human edit applied by ${action.reviewer_id}. Reason: ${action.edit_reason || "Correction"}`
        );
      } else {
        // Reviewer clicked edit but left text identical
        const currentCount = this.getConsecutiveCount(category);
        this.consecutiveCounts.set(category, currentCount + 1);
      }

      this.sentCaseIds.add(draft.case_id);

      const event: SendEvent = {
        eventId: `ev_${Date.now()}_${Math.random().toString(36).substring(7)}`,
        draftId: draft.draft_id,
        caseId: draft.case_id,
        category,
        originalDraftText: draft.proposed_reply,
        finalSentText: action.edited_content || draft.proposed_reply,
        wasUnchanged: isActuallyUnchanged,
        action: "edit_send",
        reviewerId: action.reviewer_id,
        editReason: action.edit_reason,
        timestamp: new Date().toISOString(),
      };
      this.sendHistory.push(event);

      return {
        success: true,
        message: isActuallyUnchanged
          ? `Sent without text changes. Count incremented to ${this.getConsecutiveCount(category)}.`
          : `Sent with human edits. Consecutive count for ${category} reset to 0.`,
        sendEvent: event,
      };
    }

    if (action.action === "approve_send") {
      // Direct approval without edits -> Increment counter!
      const currentCount = this.getConsecutiveCount(category);
      const newCount = currentCount + 1;
      this.consecutiveCounts.set(category, newCount);
      this.sentCaseIds.add(draft.case_id);

      const event: SendEvent = {
        eventId: `ev_${Date.now()}_${Math.random().toString(36).substring(7)}`,
        draftId: draft.draft_id,
        caseId: draft.case_id,
        category,
        originalDraftText: draft.proposed_reply,
        finalSentText: draft.proposed_reply,
        wasUnchanged: true,
        action: "approve_send",
        reviewerId: action.reviewer_id,
        timestamp: new Date().toISOString(),
      };
      this.sendHistory.push(event);

      let msg = `Approved and sent. Consecutive unchanged sends for ${category}: ${newCount}/${this.threshold}.`;
      if (newCount === this.threshold && this.allowedCategories.has(category)) {
        msg += ` Threshold reached! Category '${category}' is now eligible for controlled autonomy trial.`;
      }

      return {
        success: true,
        message: msg,
        sendEvent: event,
      };
    }

    return { success: false, message: "Unhandled review action." };
  }

  processAutonomousCandidate(draft: EmailDraft): { canAutoSend: boolean; reason: string } {
    const category = draft.classification.category;

    // Safety Gate 1: Category must be in whitelist
    if (!this.allowedCategories.has(category)) {
      return {
        canAutoSend: false,
        reason: `Category '${category}' is classified high-risk and requires mandatory human review.`,
      };
    }

    // Safety Gate 2: Counter threshold
    const count = this.getConsecutiveCount(category);
    if (count < this.threshold) {
      return {
        canAutoSend: false,
        reason: `Consecutive unchanged count (${count}/${this.threshold}) has not met the threshold.`,
      };
    }

    // Safety Gate 3: Quality regression monitor
    if (this.isQualityRegressed(category)) {
      return {
        canAutoSend: false,
        reason: `Autonomy temporarily suspended: recent edit rate exceeds ${this.maxEditRatePercent}% quality limit.`,
      };
    }

    // Safety Gate 4: Citations presence
    if (draft.citations.length === 0) {
      return {
        canAutoSend: false,
        reason: "Cannot auto-send: draft lacks verifiable citations.",
      };
    }

    // Passed all safety gates
    return {
      canAutoSend: true,
      reason: "All autonomy eligibility and safety criteria satisfied.",
    };
  }

  getHistory(): SendEvent[] {
    return [...this.sendHistory];
  }
}
