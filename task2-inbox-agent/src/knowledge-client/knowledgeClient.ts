import {
  KnowledgeBrainResponse,
  KnowledgeBrainResponseSchema,
} from "../email/types";

export interface KnowledgeClientOptions {
  baseUrl?: string;
  apiKey?: string;
  timeoutMs?: number;
  maxRetries?: number;
}

export class KnowledgeBrainClient {
  private baseUrl: string;
  private apiKey: string;
  private timeoutMs: number;
  private maxRetries: number;

  constructor(options: KnowledgeClientOptions = {}) {
    this.baseUrl = options.baseUrl || process.env.KNOWLEDGE_BRAIN_URL || "http://localhost:8001";
    this.apiKey = options.apiKey || process.env.TASK1_API_KEY || "kb_dev_secret_key_12345";
    this.timeoutMs = options.timeoutMs || 10000;
    this.maxRetries = options.maxRetries || 3;
  }

  async query(
    question: string,
    context?: Record<string, any>,
    threshold: number = 0.55
  ): Promise<KnowledgeBrainResponse> {
    const endpoint = `${this.baseUrl}/query`;
    const payload = {
      question,
      context,
      threshold,
      top_k: 5,
    };

    let lastError: Error | null = null;

    for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeoutMs);

        const response = await fetch(endpoint, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-API-Key": this.apiKey,
            "X-Request-ID": `kb_client_${Date.now()}_${Math.random().toString(36).substring(7)}`,
          },
          body: JSON.stringify(payload),
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          if (response.status >= 500 && attempt < this.maxRetries) {
            const delay = Math.pow(2, attempt) * 200 + Math.random() * 100;
            await new Promise((resolve) => setTimeout(resolve, delay));
            continue;
          }
          throw new Error(`Knowledge Brain API returned HTTP ${response.status}: ${await response.text()}`);
        }

        const rawData = await response.json();
        // Strict Zod parsing and response validation
        const parsed = KnowledgeBrainResponseSchema.parse(rawData);
        return parsed;
      } catch (err: any) {
        lastError = err;
        if (attempt < this.maxRetries && (err.name === "AbortError" || err.message?.includes("fetch failed"))) {
          const delay = Math.pow(2, attempt) * 200 + Math.random() * 100;
          await new Promise((resolve) => setTimeout(resolve, delay));
          continue;
        }
      }
    }

    // Return structured graceful degradation if API is unreachable without fabricating knowledge
    return {
      request_id: `kb_fallback_${Date.now()}`,
      question,
      answer: `Knowledge Brain service unavailable: ${lastError?.message || "Connection failed"}. Technical escalation required.`,
      status: "escalated",
      sources: [],
      evidence_sufficiency: "insufficient",
      confidence_score: 0.0,
      requires_human: true,
      escalation_id: null,
      processing_time_ms: 0,
      model: "system-unavailability-fallback",
    };
  }
}
