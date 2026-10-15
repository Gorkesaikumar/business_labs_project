const TASK1_URL = import.meta.env.VITE_TASK1_URL || "http://localhost:8001";
const TASK2_URL = import.meta.env.VITE_TASK2_URL || "http://localhost:8002";
const TASK3_URL = import.meta.env.VITE_TASK3_URL || "http://localhost:8003";

export const api = {
  // Task 1: Knowledge Brain
  async queryKnowledge(question: string) {
    const res = await fetch(`${TASK1_URL}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, threshold: 0.5, top_k: 5 }),
    });
    return res.json();
  },

  async getIngestionStatus() {
    const res = await fetch(`${TASK1_URL}/ingestion/status`);
    return res.json();
  },

  async triggerIngestion(maxPages: number = 20) {
    const res = await fetch(`${TASK1_URL}/ingestion/run`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": "kb_dev_secret_key_12345",
      },
      body: JSON.stringify({ max_pages: maxPages, force_resync: false }),
    });
    return res.json();
  },

  async listEscalations(status?: string) {
    const url = status ? `${TASK1_URL}/escalations?status=${status}` : `${TASK1_URL}/escalations`;
    const res = await fetch(url);
    return res.json();
  },

  async resolveEscalation(id: string, expertAnswer: string, approvedBy: string) {
    const res = await fetch(`${TASK1_URL}/escalations/${id}/resolve`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": "kb_dev_secret_key_12345",
      },
      body: JSON.stringify({ expert_answer: expertAnswer, approved_by: approvedBy }),
    });
    return res.json();
  },

  // Task 2: Inbox Agent
  async processEmail(email: any) {
    const res = await fetch(`${TASK2_URL}/emails/process`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(email),
    });
    return res.json();
  },

  async listDrafts() {
    const res = await fetch(`${TASK2_URL}/emails/drafts`);
    return res.json();
  },

  async reviewDraft(id: string, action: string, editedContent?: string, reason?: string) {
    const res = await fetch(`${TASK2_URL}/emails/drafts/${id}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action,
        edited_content: editedContent,
        reviewer_id: "human_reviewer_lead",
        edit_reason: reason,
      }),
    });
    return res.json();
  },

  async getAutonomyStatus(category: string = "how_to") {
    const res = await fetch(`${TASK2_URL}/autonomy/status?category=${category}`);
    return res.json();
  },

  async getAuditFeedback() {
    const res = await fetch(`${TASK2_URL}/audit/feedback`);
    return res.json();
  },

  // Task 3: Meeting to Scope
  async listTranscripts() {
    const res = await fetch(`${TASK3_URL}/transcripts`);
    return res.json();
  },

  async processTranscript(id: string) {
    const res = await fetch(`${TASK3_URL}/transcripts/${id}/process`, { method: "POST" });
    return res.json();
  },

  async listProposals() {
    const res = await fetch(`${TASK3_URL}/proposals`);
    return res.json();
  },

  async approveProposal(id: string, reviewerName: string, comments?: string) {
    const res = await fetch(`${TASK3_URL}/proposals/${id}/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reviewer_name: reviewerName, comments }),
    });
    return res.json();
  },

  async sendProposal(id: string) {
    const res = await fetch(`${TASK3_URL}/proposals/${id}/send`, { method: "POST" });
    return res.json();
  },

  async compareProposals(baselineId: string, revisedId: string) {
    const res = await fetch(`${TASK3_URL}/proposals/diff?baseline_id=${baselineId}&revised_id=${revisedId}`, {
      method: "POST",
    });
    return res.json();
  },
};
