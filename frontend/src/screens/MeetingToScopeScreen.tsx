import React, { useState, useEffect } from "react";
import { api } from "../services/api";
import { FileText, CheckCircle2, GitCompare, Send, AlertTriangle, Clock, DollarSign } from "lucide-react";

export const MeetingToScopeScreen: React.FC = () => {
  const [transcripts, setTranscripts] = useState<any[]>([]);
  const [selectedTrxId, setSelectedTrxId] = useState<string>("trx_meeting_a");
  const [currentProposal, setCurrentProposal] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [reviewerName, setReviewerName] = useState<string>("Sarah Miller (Product Owner)");
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [scopeDiff, setScopeDiff] = useState<any>(null);

  const loadTranscripts = async () => {
    try {
      const list = await api.listTranscripts();
      setTranscripts(list);
    } catch (e) {
      console.warn("Could not load transcripts:", e);
    }
  };

  useEffect(() => {
    loadTranscripts();
  }, []);

  const handleProcessTranscript = async () => {
    setLoading(true);
    setActionMessage(null);
    setScopeDiff(null);
    try {
      const prop = await api.processTranscript(selectedTrxId);
      setCurrentProposal(prop);
    } catch (err: any) {
      setActionMessage(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleApproveProposal = async () => {
    if (!currentProposal) return;
    try {
      const updated = await api.approveProposal(currentProposal.proposal_id, reviewerName);
      setCurrentProposal(updated);
      setActionMessage(`Proposal ${updated.proposal_id} approved by ${reviewerName}!`);
    } catch (err: any) {
      setActionMessage(err.message);
    }
  };

  const handleSendProposal = async () => {
    if (!currentProposal) return;
    try {
      const res = await api.sendProposal(currentProposal.proposal_id);
      setActionMessage(res.message);
    } catch (err: any) {
      setActionMessage(`Send Blocked: ${err.message}`);
    }
  };

  const handleRunScopeDiff = async () => {
    setLoading(true);
    try {
      // Process Meeting A baseline and Meeting C follow-up
      const propA = await api.processTranscript("trx_meeting_a");
      const propC = await api.processTranscript("trx_meeting_c");
      const diff = await api.compareProposals(propA.proposal_id, propC.proposal_id);
      setScopeDiff(diff);
      setCurrentProposal(propC);
    } catch (err: any) {
      setActionMessage(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h2 style={{ margin: "0 0 6px 0" }}>Task 3: Meeting to Scope of Work (Python)</h2>
          <p style={{ color: "var(--text-muted)", margin: 0 }}>
            Multi-agent architecture analyzing discovery transcripts, checking feasibility via Task 1 API, estimating 3-point task hours, generating proposals, and calculating scope diffs.
          </p>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button onClick={handleRunScopeDiff} disabled={loading} className="btn-primary" style={{ background: "#8b5cf6" }}>
            <GitCompare size={16} /> Compare Meeting A vs C Diff
          </button>
        </div>
      </div>

      <div className="grid-2">
        {/* Left Column: Transcript Selector & Requirements */}
        <div>
          <div className="card">
            <h3 style={{ marginTop: 0, display: "flex", alignItems: "center", gap: 8 }}>
              <FileText size={18} /> Select Meeting Transcript
            </h3>
            <div style={{ display: "flex", gap: 10, marginBottom: 14 }}>
              <select
                className="input-box"
                value={selectedTrxId}
                onChange={(e) => setSelectedTrxId(e.target.value)}
              >
                <option value="trx_meeting_a">Meeting A: Search, Filters, & Mobile Overhaul</option>
                <option value="trx_meeting_b">Meeting B: E-Commerce Checkout & Automated Billing</option>
                <option value="trx_meeting_c">Meeting C: Follow-Up Scope Change (Adds AI, Drops Radius, 4w Deadline)</option>
              </select>
              <button onClick={handleProcessTranscript} disabled={loading} className="btn-primary">
                {loading ? "Analyzing..." : "Run Agents"}
              </button>
            </div>

            {currentProposal?.scope_of_work?.confirmed_requirements && (
              <div>
                <h4 style={{ margin: "16px 0 8px 0" }}>
                  Extracted Requirements ({currentProposal.scope_of_work.confirmed_requirements.length}):
                </h4>
                {currentProposal.scope_of_work.confirmed_requirements.map((r: any) => (
                  <div key={r.id} style={{ background: "var(--bg-primary)", padding: 12, borderRadius: 6, marginBottom: 10, border: "1px solid var(--border-color)" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <strong>{r.title}</strong>
                      <span className={`badge ${r.feasibility_classification === "existing_configuration" ? "badge-green" : r.feasibility_classification === "existing_with_limitations" ? "badge-blue" : "badge-amber"}`}>
                        {r.feasibility_classification?.replace(/_/g, " ")}
                      </span>
                    </div>
                    <p style={{ fontSize: 13, margin: "6px 0", color: "#cbd5e1" }}>{r.description}</p>
                    <div style={{ fontSize: 12, color: "var(--text-muted)", fontStyle: "italic" }}>
                      "{r.source_passage}" — {r.speaker}
                    </div>
                    {r.feasibility_evidence && (
                      <div style={{ fontSize: 12, color: "var(--accent-blue)", marginTop: 4 }}>
                        Feasibility Check: {r.feasibility_evidence}
                      </div>
                    )}
                  </div>
                ))}

                {currentProposal.scope_of_work.exclusions && (
                  <div style={{ marginTop: 12, padding: 10, background: "rgba(239, 68, 68, 0.08)", border: "1px solid var(--accent-red)", borderRadius: 6 }}>
                    <strong style={{ color: "var(--accent-red)", fontSize: 13 }}>Explicit Exclusions:</strong>
                    <ul style={{ margin: "4px 0 0 0", paddingLeft: 18, fontSize: 13 }}>
                      {currentProposal.scope_of_work.exclusions.map((ex: string, idx: number) => (
                        <li key={idx}>{ex}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Commercial Proposal Preview, 3-Point Estimates & Approval */}
        <div>
          {scopeDiff && (
            <div className="card" style={{ border: "1px solid #8b5cf6", background: "rgba(139, 92, 246, 0.08)" }}>
              <h3 style={{ marginTop: 0, color: "#a78bfa", display: "flex", alignItems: "center", gap: 8 }}>
                <GitCompare size={18} /> Meeting A vs Meeting C Scope Delta
              </h3>
              <div style={{ display: "flex", gap: 10, marginBottom: 12 }}>
                <span className="badge badge-green">Added Reqs: {scopeDiff.added_requirements.length}</span>
                <span className="badge badge-red">Removed Reqs: {scopeDiff.removed_requirements.length}</span>
                <span className="badge badge-amber">Timeline Delta: {scopeDiff.timeline_delta_weeks} weeks</span>
              </div>
              <div style={{ fontSize: 13, whiteSpace: "pre-line", lineHeight: 1.5 }}>
                {scopeDiff.human_summary}
              </div>
            </div>
          )}

          {currentProposal ? (
            <div className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <h3 style={{ margin: 0 }}>{currentProposal.title}</h3>
                <span className={`badge ${currentProposal.status === "approved" ? "badge-green" : "badge-amber"}`}>
                  {currentProposal.status.toUpperCase()}
                </span>
              </div>

              {/* Effort & Pricing Metrics */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10, margin: "14px 0" }}>
                <div style={{ background: "var(--bg-primary)", padding: 10, borderRadius: 6, textAlign: "center" }}>
                  <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Timeline</div>
                  <div style={{ fontSize: 18, fontWeight: 700, display: "flex", alignItems: "center", justifyContent: "center", gap: 4 }}>
                    <Clock size={16} /> {currentProposal.timeline_weeks} Weeks
                  </div>
                </div>
                <div style={{ background: "var(--bg-primary)", padding: 10, borderRadius: 6, textAlign: "center" }}>
                  <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Total Hours (PERT)</div>
                  <div style={{ fontSize: 18, fontWeight: 700 }}>
                    {currentProposal.total_hours_likely.toFixed(1)} hrs
                  </div>
                </div>
                <div style={{ background: "var(--bg-primary)", padding: 10, borderRadius: 6, textAlign: "center" }}>
                  <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Commercial Price</div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: "var(--accent-green)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    ${currentProposal.estimated_cost_likely.toLocaleString()}
                  </div>
                </div>
              </div>

              <div style={{ background: "var(--bg-primary)", padding: 12, borderRadius: 6, fontSize: 13, lineHeight: 1.5, marginBottom: 14 }}>
                <strong>Executive Summary:</strong>
                <p style={{ margin: "6px 0 0 0", whiteSpace: "pre-line" }}>{currentProposal.executive_summary}</p>
              </div>

              {/* 3-Point Task Breakdown */}
              {currentProposal.task_estimates && (
                <div style={{ marginBottom: 14 }}>
                  <h4 style={{ margin: "10px 0 6px 0" }}>Three-Point Task Estimates:</h4>
                  <div style={{ maxHeight: 220, overflowY: "auto", fontSize: 12 }}>
                    {currentProposal.task_estimates.map((t: any) => (
                      <div key={t.task_id} style={{ padding: "6px 0", borderBottom: "1px solid var(--border-color)", display: "flex", justifyContent: "space-between" }}>
                        <div>
                          <strong>{t.task_name}</strong>
                          <div style={{ color: "var(--text-muted)" }}>{t.rationale}</div>
                        </div>
                        <div style={{ textAlign: "right", minWidth: 100 }}>
                          <div>{t.most_likely_hours}h (likely)</div>
                          <div style={{ color: "var(--text-muted)", fontSize: 11 }}>[{t.low_hours}h - {t.high_hours}h]</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {actionMessage && (
                <div style={{ padding: 10, borderRadius: 6, marginBottom: 14, background: actionMessage.includes("Blocked") ? "rgba(239, 68, 68, 0.15)" : "rgba(16, 185, 129, 0.15)", border: "1px solid var(--border-color)", fontSize: 13 }}>
                  {actionMessage}
                </div>
              )}

              {/* Human Approval Controls */}
              <div style={{ borderTop: "1px solid var(--border-color)", paddingTop: 14 }}>
                <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>
                  Human Commercial Approval Gate (Enforced on Backend):
                </div>
                {currentProposal.status === "draft" ? (
                  <div style={{ display: "flex", gap: 10 }}>
                    <input
                      type="text"
                      className="input-box"
                      placeholder="Reviewer Name (e.g. Lead Consultant)..."
                      value={reviewerName}
                      onChange={(e) => setReviewerName(e.target.value)}
                    />
                    <button onClick={handleApproveProposal} className="btn-success" style={{ whiteSpace: "nowrap" }}>
                      <CheckCircle2 size={16} /> Sign & Approve
                    </button>
                    <button onClick={handleSendProposal} className="btn-primary" style={{ whiteSpace: "nowrap" }}>
                      <Send size={16} /> Attempt Send
                    </button>
                  </div>
                ) : (
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div style={{ fontSize: 13, color: "var(--accent-green)" }}>
                      ✓ Approved by {currentProposal.approved_by} on {new Date(currentProposal.approved_at).toLocaleString()}
                    </div>
                    <button onClick={handleSendProposal} className="btn-success">
                      <Send size={16} /> Dispatch Proposal to Client
                    </button>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="card" style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
              Select a transcript and click "Run Agents" to extract requirements, evaluate feasibility via Task 1, and generate a proposal.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
