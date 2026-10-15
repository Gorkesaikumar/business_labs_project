import { EmailDraft } from "../email/types";
import { SendEvent } from "../autonomy/autonomyEngine";

export interface AuditRecord {
  recordId: string;
  caseId: string;
  sender: string;
  subject: string;
  category: string;
  priority: string;
  originalDraftText: string;
  finalSentText: string;
  wasUnchanged: boolean;
  action: string;
  reviewerId?: string;
  editReason?: string;
  modelVersion: string;
  promptVersion: string;
  citationsCount: number;
  timestamp: string;
}

export class AuditStore {
  private records: Map<string, AuditRecord> = new Map();

  record(draft: EmailDraft, sendEvent: SendEvent): AuditRecord {
    const record: AuditRecord = {
      recordId: sendEvent.eventId,
      caseId: draft.case_id,
      sender: draft.sender,
      subject: draft.subject,
      category: draft.classification.category,
      priority: draft.classification.priority,
      originalDraftText: draft.proposed_reply,
      finalSentText: sendEvent.finalSentText,
      wasUnchanged: sendEvent.wasUnchanged,
      action: sendEvent.action,
      reviewerId: sendEvent.reviewerId,
      editReason: sendEvent.editReason,
      modelVersion: draft.model_version,
      promptVersion: draft.prompt_version,
      citationsCount: draft.citations.length,
      timestamp: sendEvent.timestamp,
    };

    this.records.set(record.recordId, record);
    return record;
  }

  getRecord(recordId: string): AuditRecord | undefined {
    return this.records.get(recordId);
  }

  listRecords(limit: number = 100): AuditRecord[] {
    return Array.from(this.records.values())
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, limit);
  }

  analyzeFeedback(): {
    totalRecords: number;
    unchangedSends: number;
    editedSends: number;
    rejections: number;
    editRatePercent: number;
    recurringEditReasons: Record<string, number>;
  } {
    const all = Array.from(this.records.values());
    const total = all.length;
    if (total === 0) {
      return {
        totalRecords: 0,
        unchangedSends: 0,
        editedSends: 0,
        rejections: 0,
        editRatePercent: 0,
        recurringEditReasons: {},
      };
    }

    const unchanged = all.filter((r) => r.wasUnchanged && r.action !== "reject").length;
    const edited = all.filter((r) => !r.wasUnchanged && r.action === "edit_send").length;
    const rejections = all.filter((r) => r.action === "reject").length;

    const reasons: Record<string, number> = {};
    for (const r of all) {
      if (r.editReason) {
        reasons[r.editReason] = (reasons[r.editReason] || 0) + 1;
      }
    }

    return {
      totalRecords: total,
      unchangedSends: unchanged,
      editedSends: edited,
      rejections,
      editRatePercent: Math.round(((edited + rejections) / total) * 1000) / 10,
      recurringEditReasons: reasons,
    };
  }
}
