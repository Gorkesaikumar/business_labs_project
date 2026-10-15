import { z } from "zod";

export const EmailCategorySchema = z.enum([
  "how_to",
  "troubleshooting",
  "feature_request",
  "refund_cancellation",
  "complaint_urgent",
  "quote_request",
  "follow_up",
  "missing_information",
  "unanswerable_out_of_scope",
  "adversarial_injection",
]);
export type EmailCategory = z.infer<typeof EmailCategorySchema>;

export const PrioritySchema = z.enum(["low", "medium", "high", "urgent"]);
export type Priority = z.infer<typeof PrioritySchema>;

export const RiskLevelSchema = z.enum(["low", "medium", "high", "critical"]);
export type RiskLevel = z.infer<typeof RiskLevelSchema>;

export const CustomerEmailSchema = z.object({
  case_id: z.string(),
  subject: z.string(),
  sender: z.string(),
  body: z.string(),
  expected_category: EmailCategorySchema.optional(),
  expected_priority: PrioritySchema.optional(),
  important_facts: z.array(z.string()).optional(),
  requires_kb_consult: z.boolean().optional(),
  requires_human_approval: z.boolean().optional(),
  risk_level: RiskLevelSchema.optional(),
  safety_constraints: z.array(z.string()).optional(),
});
export type CustomerEmail = z.infer<typeof CustomerEmailSchema>;

export const KnowledgeCitationSchema = z.object({
  article_id: z.string(),
  url: z.string(),
  title: z.string(),
  heading: z.string().optional(),
  passage: z.string(),
  relevance_score: z.number(),
  screenshot_urls: z.array(z.string()).default([]),
});
export type KnowledgeCitation = z.infer<typeof KnowledgeCitationSchema>;

export const KnowledgeBrainResponseSchema = z.object({
  request_id: z.string(),
  question: z.string(),
  answer: z.string(),
  status: z.enum(["answered", "insufficient_evidence", "escalated"]),
  sources: z.array(KnowledgeCitationSchema).default([]),
  evidence_sufficiency: z.enum(["sufficient", "partial", "insufficient"]),
  confidence_score: z.number(),
  requires_human: z.boolean(),
  escalation_id: z.string().nullable().optional(),
  processing_time_ms: z.number(),
  model: z.string(),
});
export type KnowledgeBrainResponse = z.infer<typeof KnowledgeBrainResponseSchema>;

export const EmailClassificationSchema = z.object({
  category: EmailCategorySchema,
  priority: PrioritySchema,
  risk_level: RiskLevelSchema,
  summary: z.string(),
  extracted_facts: z.array(z.string()),
  requires_kb_consult: z.boolean(),
  requires_human_approval: z.boolean(),
  risk_flags: z.array(z.string()),
  suggested_action: z.string(),
});
export type EmailClassification = z.infer<typeof EmailClassificationSchema>;

export const EmailDraftSchema = z.object({
  draft_id: z.string(),
  case_id: z.string(),
  sender: z.string(),
  subject: z.string(),
  classification: EmailClassificationSchema,
  proposed_reply: z.string(),
  citations: z.array(KnowledgeCitationSchema),
  kb_status: z.string().optional(),
  is_autonomous_candidate: z.boolean(),
  status: z.enum(["pending_review", "approved_sent", "edited_sent", "rejected", "escalated"]),
  model_version: z.string(),
  prompt_version: z.string(),
  created_at: z.string(),
});
export type EmailDraft = z.infer<typeof EmailDraftSchema>;

export const ReviewActionSchema = z.object({
  action: z.enum(["approve_send", "edit_send", "reject", "escalate"]),
  edited_content: z.string().optional(),
  reviewer_id: z.string(),
  edit_reason: z.string().optional(),
});
export type ReviewAction = z.infer<typeof ReviewActionSchema>;

export const AutonomyStatusSchema = z.object({
  category: EmailCategorySchema,
  consecutive_unchanged_sends: z.number(),
  threshold: z.number(),
  is_eligible: z.boolean(),
  is_active: z.boolean(),
  recent_edits_count: z.number(),
  recent_sends_count: z.number(),
  error_rate: z.number(),
  safety_lock: z.boolean(),
  last_reset_reason: z.string().nullable(),
});
export type AutonomyStatus = z.infer<typeof AutonomyStatusSchema>;
