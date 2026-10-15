import express, { Request, Response } from "express";
import { CustomerEmailSchema, ReviewActionSchema } from "../email/types";
import { EmailClassifier } from "../drafting/classifier";
import { EmailDrafter } from "../drafting/drafter";
import { AutonomyEngine } from "../autonomy/autonomyEngine";
import { AuditStore } from "../feedback/auditStore";

export function createServer() {
  const app = express();
  app.use(express.json());

  const classifier = new EmailClassifier();
  const drafter = new EmailDrafter();
  const autonomyEngine = new AutonomyEngine({ threshold: 20 });
  const auditStore = new AuditStore();

  const draftsMap = new Map<string, any>();

  // Health check
  app.get("/health", (req: Request, res: Response) => {
    res.json({
      service: "Task 2: Inbox Agent",
      status: "healthy",
      timestamp: new Date().toISOString(),
    });
  });

  // Process single email
  app.post("/emails/process", async (req: Request, res: Response) => {
    try {
      const email = CustomerEmailSchema.parse(req.body);
      const classification = classifier.classify(email);
      const draft = await drafter.draft(email, classification);

      // Check autonomy engine
      if (draft.is_autonomous_candidate) {
        const autoDecision = autonomyEngine.processAutonomousCandidate(draft);
        if (autoDecision.canAutoSend) {
          draft.status = "approved_sent";
          const result = autonomyEngine.recordReviewDecision(draft, {
            action: "approve_send",
            reviewer_id: "system_autonomous_agent",
          });
          if (result.sendEvent) {
            auditStore.record(draft, result.sendEvent);
          }
        }
      }

      draftsMap.set(draft.draft_id, draft);
      res.json(draft);
    } catch (err: any) {
      res.status(400).json({ error: err.message });
    }
  });

  // List drafts
  app.get("/emails/drafts", (req: Request, res: Response) => {
    res.json(Array.from(draftsMap.values()));
  });

  // Human review action (approve, edit, reject)
  app.post("/emails/drafts/:id/review", (req: Request, res: Response) => {
    try {
      const draftId = String(req.params.id);
      const draft = draftsMap.get(draftId);
      if (!draft) {
        return res.status(404).json({ error: `Draft ${draftId} not found.` });
      }

      const action = ReviewActionSchema.parse(req.body);
      const result = autonomyEngine.recordReviewDecision(draft, action);

      if (!result.success) {
        return res.status(400).json({ error: result.message });
      }

      // Update draft status
      if (action.action === "reject") {
        draft.status = "rejected";
      } else if (action.action === "edit_send") {
        draft.status = "edited_sent";
        draft.proposed_reply = action.edited_content || draft.proposed_reply;
      } else {
        draft.status = "approved_sent";
      }

      if (result.sendEvent) {
        auditStore.record(draft, result.sendEvent);
      }

      res.json({
        message: result.message,
        draft,
        autonomy_status: autonomyEngine.getStatus(draft.classification.category),
      });
    } catch (err: any) {
      res.status(400).json({ error: err.message });
    }
  });

  // Autonomy status
  app.get("/autonomy/status", (req: Request, res: Response) => {
    const category = (req.query.category as string) || "how_to";
    res.json(autonomyEngine.getStatus(category as any));
  });

  // Audit feedback
  app.get("/audit/feedback", (req: Request, res: Response) => {
    res.json(auditStore.analyzeFeedback());
  });

  return { app, classifier, drafter, autonomyEngine, auditStore, draftsMap };
}
