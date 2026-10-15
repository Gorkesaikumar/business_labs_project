import React, { useState, useEffect } from "react";
import { api } from "../services/api";
import { Search, Database, AlertCircle, CheckCircle, RefreshCw, BookOpen } from "lucide-react";

export const KnowledgeBrainScreen: React.FC = () => {
  const [question, setQuestion] = useState("");
  const [queryResult, setQueryResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [ingestionStatus, setIngestionStatus] = useState<any>(null);
  const [escalations, setEscalations] = useState<any[]>([]);
  const [expertAnswer, setExpertAnswer] = useState("");
  const [selectedEscalationId, setSelectedEscalationId] = useState<string | null>(null);

  const loadStatus = async () => {
    try {
      const status = await api.getIngestionStatus();
      setIngestionStatus(status);
      const escList = await api.listEscalations();
      setEscalations(escList);
    } catch (e) {
      console.warn("Could not load KB status:", e);
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    try {
      const res = await api.queryKnowledge(question);
      setQueryResult(res);
      await loadStatus();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerIngestion = async () => {
    setLoading(true);
    try {
      await api.triggerIngestion(10);
      await loadStatus();
    } finally {
      setLoading(false);
    }
  };

  const handleResolveEscalation = async (id: string) => {
    if (!expertAnswer.trim()) return;
    try {
      await api.resolveEscalation(id, expertAnswer, "Lead Knowledge Architect");
      setExpertAnswer("");
      setSelectedEscalationId(null);
      await loadStatus();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h2 style={{ margin: "0 0 6px 0" }}>Task 1: Knowledge Brain</h2>
          <p style={{ color: "var(--text-muted)", margin: 0 }}>
            Solution Center RAG service with evidence sufficiency checks, verifiable citations, and human escalations.
          </p>
        </div>
        <button onClick={handleTriggerIngestion} disabled={loading} className="btn-primary">
          <RefreshCw size={16} /> Run Sitemap Sync
        </button>
      </div>

      <div className="grid-2">
        {/* Left Column: Query Interface */}
        <div>
          <div className="card">
            <h3 style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 0 }}>
              <Search size={18} /> Ask Product Question
            </h3>
            <form onSubmit={handleQuery}>
              <div style={{ display: "flex", gap: 10 }}>
                <input
                  type="text"
                  className="input-box"
                  placeholder="e.g. How do I configure Stripe for member subscriptions?"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                />
                <button type="submit" disabled={loading} className="btn-primary">
                  {loading ? "Searching..." : "Query"}
                </button>
              </div>
            </form>

            {queryResult && (
              <div style={{ marginTop: 20 }}>
                <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 12 }}>
                  <span className={`badge ${queryResult.status === "answered" ? "badge-green" : "badge-amber"}`}>
                    {queryResult.status.toUpperCase()}
                  </span>
                  <span className="badge badge-blue">
                    Sufficiency: {queryResult.evidence_sufficiency}
                  </span>
                  <span style={{ fontSize: 13, color: "var(--text-muted)" }}>
                    Confidence: {(queryResult.confidence_score * 100).toFixed(1)}% | {queryResult.processing_time_ms}ms
                  </span>
                </div>

                <div style={{ background: "var(--bg-primary)", padding: 14, borderRadius: 6, marginBottom: 16 }}>
                  <p style={{ margin: 0, whiteSpace: "pre-line" }}>{queryResult.answer}</p>
                </div>

                {queryResult.sources && queryResult.sources.length > 0 && (
                  <div>
                    <h4 style={{ margin: "10px 0 8px 0" }}>Verifiable Source Citations ({queryResult.sources.length}):</h4>
                    {queryResult.sources.map((s: any, idx: number) => (
                      <div key={idx} style={{ background: "rgba(255,255,255,0.03)", padding: 10, borderRadius: 6, marginBottom: 8, border: "1px solid var(--border-color)" }}>
                        <div style={{ fontWeight: 600, display: "flex", justifyContent: "space-between" }}>
                          <a href={s.url} target="_blank" rel="noreferrer" style={{ color: "var(--accent-blue)" }}>
                            {s.title}
                          </a>
                          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Relevance: {(s.relevance_score * 100).toFixed(1)}%</span>
                        </div>
                        <div style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 4 }}>
                          Section: {s.heading}
                        </div>
                        <p style={{ fontSize: 13, margin: "6px 0 0 0" }}>"{s.passage}"</p>
                      </div>
                    ))}
                  </div>
                )}

                {queryResult.escalation_id && (
                  <div style={{ background: "rgba(245, 158, 11, 0.1)", border: "1px solid var(--accent-amber)", padding: 12, borderRadius: 6, marginTop: 12 }}>
                    <div style={{ display: "flex", gap: 8, alignItems: "center", color: "var(--accent-amber)" }}>
                      <AlertCircle size={16} />
                      <strong>Escalation Ticket Auto-Created: {queryResult.escalation_id}</strong>
                    </div>
                    <p style={{ fontSize: 13, margin: "6px 0 0 0" }}>
                      Evidence was insufficient to provide a grounded answer. Routed to expert resolution queue.
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Ingestion Status & Escalation Queue */}
        <div>
          <div className="card">
            <h3 style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 0 }}>
              <Database size={18} /> Ingestion Operational Status
            </h3>
            {ingestionStatus ? (
              <div>
                <div style={{ display: "flex", gap: 10, marginBottom: 10 }}>
                  <span className="badge badge-green">Status: {ingestionStatus.status || "IDLE"}</span>
                  <span className="badge badge-blue">Discovered: {ingestionStatus.total_discovered || 0}</span>
                  <span className="badge badge-amber">Updated: {ingestionStatus.updated || 0}</span>
                  <span className="badge badge-red">Errors: {ingestionStatus.errors || 0}</span>
                </div>
                <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
                  Daily Ingestion Schedule: Active (Every 24h via APScheduler)
                </div>
              </div>
            ) : (
              <p style={{ color: "var(--text-muted)" }}>No ingestion runs recorded yet.</p>
            )}
          </div>

          <div className="card">
            <h3 style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 0 }}>
              <AlertCircle size={18} /> Human Escalation Queue ({escalations.filter(e => e.status === "pending").length} Pending)
            </h3>
            {escalations.length === 0 ? (
              <p style={{ color: "var(--text-muted)" }}>No escalation tickets in queue.</p>
            ) : (
              <div style={{ maxHeight: 350, overflowY: "auto" }}>
                {escalations.map((esc) => (
                  <div key={esc.id} style={{ padding: 10, borderBottom: "1px solid var(--border-color)" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span className={`badge ${esc.status === "resolved" ? "badge-green" : "badge-amber"}`}>
                        {esc.status}
                      </span>
                      <span style={{ fontSize: 12, color: "var(--text-muted)" }}>{esc.id}</span>
                    </div>
                    <p style={{ margin: "6px 0", fontWeight: 600 }}>{esc.question}</p>
                    <p style={{ fontSize: 12, color: "var(--text-muted)", margin: "0 0 6px 0" }}>Reason: {esc.reason}</p>

                    {esc.status === "pending" && (
                      <div>
                        {selectedEscalationId === esc.id ? (
                          <div style={{ marginTop: 8 }}>
                            <textarea
                              className="input-box"
                              placeholder="Type authoritative expert answer to index into Knowledge Brain..."
                              rows={3}
                              value={expertAnswer}
                              onChange={(e) => setExpertAnswer(e.target.value)}
                            />
                            <div style={{ display: "flex", gap: 8, marginTop: 6 }}>
                              <button onClick={() => handleResolveEscalation(esc.id)} className="btn-success">
                                Submit & Index to DB
                              </button>
                              <button onClick={() => setSelectedEscalationId(null)} className="btn-danger">
                                Cancel
                              </button>
                            </div>
                          </div>
                        ) : (
                          <button onClick={() => setSelectedEscalationId(esc.id)} className="btn-primary" style={{ padding: "4px 10px", fontSize: 12 }}>
                            Resolve Ticket
                          </button>
                        )}
                      </div>
                    )}

                    {esc.status === "resolved" && (
                      <div style={{ background: "rgba(16, 185, 129, 0.1)", padding: 8, borderRadius: 4, marginTop: 6 }}>
                        <div style={{ fontSize: 12, fontWeight: 600, color: "var(--accent-green)" }}>
                          Resolved by: {esc.approved_by}
                        </div>
                        <p style={{ fontSize: 12, margin: "4px 0 0 0" }}>{esc.expert_answer}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
