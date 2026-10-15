import React, { useState, useEffect } from "react";
import { api } from "../services/api";
import { Mail, Check, Edit3, XCircle, Shield, Award, AlertTriangle } from "lucide-react";
import customerEmails from "../../../datasets/emails/customer_emails.json";

export const InboxAgentScreen: React.FC = () => {
  const [selectedCaseId, setSelectedCaseId] = useState<string>("email_001");
  const [currentDraft, setCurrentDraft] = useState<any>(null);
  const [editedReply, setEditedReply] = useState<string>("");
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [editReason, setEditReason] = useState<string>("");
  const [autonomyStatus, setAutonomyStatus] = useState<any>(null);
  const [auditFeedback, setAuditFeedback] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [reviewMessage, setReviewMessage] = useState<string | null>(null);

  const selectedEmail = customerEmails.find((e) => e.case_id === selectedCaseId) || customerEmails[0];

  const loadAutonomyAndAudit = async () => {
    try {
      const auto = await api.getAutonomyStatus("how_to");
      setAutonomyStatus(auto);
      const feedback = await api.getAuditFeedback();
      setAuditFeedback(feedback);
    } catch (e) {
      console.warn("Could not load autonomy/audit:", e);
    }
  };

  const processSelectedEmail = async () => {
    setLoading(true);
    setReviewMessage(null);
    setIsEditing(false);
    try {
      const draft = await api.processEmail(selectedEmail);
      setCurrentDraft(draft);
      setEditedReply(draft.proposed_reply);
      await loadAutonomyAndAudit();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    processSelectedEmail();
  }, [selectedCaseId]);

  const handleReview = async (action: "approve_send" | "edit_send" | "reject") => {
    if (!currentDraft) return;
    try {
      const res = await api.reviewDraft(
        currentDraft.draft_id,
        action,
        action === "edit_send" ? editedReply : undefined,
        editReason || undefined
      );
      setReviewMessage(res.message);
      setCurrentDraft(res.draft);
      setAutonomyStatus(res.autonomy_status);
      setIsEditing(false);
      setEditReason("");
      await loadAutonomyAndAudit();
    } catch (err: any) {
      setReviewMessage(err.message);
    }
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h2 style={{ margin: "0 0 6px 0" }}>Task 2: Inbox Agent (TypeScript)</h2>
          <p style={{ color: "var(--text-muted)", margin: 0 }}>
            Triages customer emails, calls Task 1 Knowledge Brain, drafts evidence-grounded replies, and tracks the 20-consecutive-unchanged-send autonomy rule.
          </p>
        </div>
      </div>

      {/* Autonomy Status Banner */}
      {autonomyStatus && (
        <div className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "rgba(30, 41, 59, 0.7)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <Award size={32} color={autonomyStatus.is_eligible ? "var(--accent-green)" : "var(--accent-blue)"} />
            <div>
              <div style={{ fontWeight: 600, fontSize: 16 }}>
                20-Consecutive-Unchanged-Send Autonomy Engine ({autonomyStatus.category})
              </div>
              <div style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 2 }}>
                Current Qualifying Streak: <strong>{autonomyStatus.consecutive_unchanged_sends} / {autonomyStatus.threshold}</strong> |
                Autonomy Status: <span style={{ color: autonomyStatus.is_eligible ? "var(--accent-green)" : "var(--accent-amber)" }}>
                  {autonomyStatus.is_eligible ? "ELIGIBLE (TRIAL ACTIVE)" : "HUMAN APPROVAL REQUIRED"}
                </span>
              </div>
            </div>
          </div>
          <div style={{ textAlign: "right" }}>
            <span className={`badge ${autonomyStatus.safety_lock ? "badge-red" : "badge-green"}`}>
              {autonomyStatus.safety_lock ? "SAFETY LOCK ENGAGED" : "AUTONOMY PERMITTED"}
            </span>
            {autonomyStatus.last_reset_reason && (
              <div style={{ fontSize: 11, color: "var(--accent-amber)", marginTop: 4, maxWidth: 300 }}>
                Reset: {autonomyStatus.last_reset_reason}
              </div>
            )}
          </div>
        </div>
      )}

      <div className="grid-2">
        {/* Left Column: Email Fixture Selector & Original Email */}
        <div>
          <div className="card">
            <h3 style={{ marginTop: 0, display: "flex", alignItems: "center", gap: 8 }}>
              <Mail size={18} /> Select Customer Email (52 Scenarios)
            </h3>
            <select
              className="input-box"
              value={selectedCaseId}
              onChange={(e) => setSelectedCaseId(e.target.value)}
              style={{ marginBottom: 14 }}
            >
              {customerEmails.map((em) => (
                <option key={em.case_id} value={em.case_id}>
                  [{em.case_id}] {em.subject.substring(0, 55)} ({em.expected_category})
                </option>
              ))}
            </select>

            <div style={{ background: "var(--bg-primary)", padding: 14, borderRadius: 6 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                <strong>From: {selectedEmail.sender}</strong>
                <span className="badge badge-blue">{selectedEmail.expected_priority?.toUpperCase()}</span>
              </div>
              <div style={{ fontWeight: 600, marginBottom: 8 }}>Subject: {selectedEmail.subject}</div>
              <div style={{ fontSize: 13, whiteSpace: "pre-line", color: "#cbd5e1", lineHeight: 1.5 }}>
                {selectedEmail.body}
              </div>
            </div>

            {currentDraft?.classification && (
              <div style={{ marginTop: 14 }}>
                <h4 style={{ margin: "10px 0 6px 0" }}>AI Classification & Risk Triage:</h4>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
                  <span className="badge badge-blue">Category: {currentDraft.classification.category}</span>
                  <span className={`badge ${currentDraft.classification.risk_level === "critical" ? "badge-red" : "badge-amber"}`}>
                    Risk: {currentDraft.classification.risk_level}
                  </span>
                  <span className={`badge ${currentDraft.classification.requires_human_approval ? "badge-amber" : "badge-green"}`}>
                    Human Approval: {currentDraft.classification.requires_human_approval ? "MANDATORY" : "OPTIONAL"}
                  </span>
                </div>
                <p style={{ fontSize: 13, color: "var(--text-muted)", margin: 0 }}>
                  Suggested Action: {currentDraft.classification.suggested_action}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: AI Draft & Review Controls */}
        <div>
          <div className="card">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 0 }}>
              <h3 style={{ margin: 0, display: "flex", alignItems: "center", gap: 8 }}>
                <Edit3 size={18} /> Generated Response & Evidence
              </h3>
              {currentDraft && (
                <span className={`badge ${currentDraft.status === "approved_sent" ? "badge-green" : currentDraft.status === "edited_sent" ? "badge-blue" : currentDraft.status === "rejected" ? "badge-red" : "badge-amber"}`}>
                  {currentDraft.status.toUpperCase()}
                </span>
              )}
            </div>

            {loading ? (
              <p style={{ color: "var(--text-muted)", marginTop: 20 }}>Generating grounded draft and consulting Task 1 Knowledge Brain...</p>
            ) : currentDraft ? (
              <div style={{ marginTop: 14 }}>
                {isEditing ? (
                  <div>
                    <textarea
                      className="input-box"
                      rows={8}
                      value={editedReply}
                      onChange={(e) => setEditedReply(e.target.value)}
                    />
                    <input
                      type="text"
                      className="input-box"
                      style={{ marginTop: 8 }}
                      placeholder="Reason for edit (logged for regression analysis)..."
                      value={editReason}
                      onChange={(e) => setEditReason(e.target.value)}
                    />
                  </div>
                ) : (
                  <div style={{ background: "var(--bg-primary)", padding: 14, borderRadius: 6, whiteSpace: "pre-line", fontSize: 13, lineHeight: 1.5 }}>
                    {currentDraft.proposed_reply}
                  </div>
                )}

                {/* Citations Preview */}
                {currentDraft.citations && currentDraft.citations.length > 0 && (
                  <div style={{ marginTop: 12, padding: 10, background: "rgba(59, 130, 246, 0.05)", border: "1px solid var(--border-color)", borderRadius: 6 }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: "var(--accent-blue)" }}>
                      Task 1 Citations ({currentDraft.citations.length}):
                    </div>
                    {currentDraft.citations.map((c: any, idx: number) => (
                      <div key={idx} style={{ fontSize: 12, marginTop: 4 }}>
                        • <a href={c.url} target="_blank" rel="noreferrer" style={{ color: "var(--accent-blue)" }}>{c.title}</a>
                        <span style={{ color: "var(--text-muted)" }}> ({c.heading || "Overview"})</span>
                      </div>
                    ))}
                  </div>
                )}

                {reviewMessage && (
                  <div style={{ marginTop: 12, padding: 10, background: "rgba(16, 185, 129, 0.1)", border: "1px solid var(--accent-green)", borderRadius: 6, fontSize: 13 }}>
                    {reviewMessage}
                  </div>
                )}

                {/* Review Controls */}
                <div style={{ display: "flex", gap: 10, marginTop: 16 }}>
                  {isEditing ? (
                    <>
                      <button onClick={() => handleReview("edit_send")} className="btn-success">
                        <Check size={16} /> Save Edits & Send (Resets Autonomy Counter)
                      </button>
                      <button onClick={() => setIsEditing(false)} className="btn-danger">
                        Cancel
                      </button>
                    </>
                  ) : (
                    <>
                      <button onClick={() => handleReview("approve_send")} className="btn-success">
                        <Check size={16} /> Approve & Send
                      </button>
                      <button onClick={() => setIsEditing(true)} className="btn-primary">
                        <Edit3 size={16} /> Edit Draft
                      </button>
                      <button onClick={() => handleReview("reject")} className="btn-danger">
                        <XCircle size={16} /> Reject (Resets Counter)
                      </button>
                    </>
                  )}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
};
