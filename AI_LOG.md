# AI Interaction Log (AI_LOG.md)
**Project**: AI Tech Consultant (BusinessLabs / Anthropic Applied AI Engineering Capstone)  
**Assistant**: Antigravity (Powered by Claude / Gemini models)

---

## Log of Key Prompts and Architectural Interactions

### Interaction 1: Environment & Dependency Discovery
- **User Prompt**: Master build prompt providing comprehensive specifications across Task 1 (Knowledge Brain), Task 2 (Inbox Agent), Task 3 (Meeting to Scope), shared Frontend, Docker Compose, Evaluation Framework, and Submission deliverables.
- **Action Taken**: Inspected local Windows environment, identifying Python 3.14 + uv 0.12.17, Node v24.21.0, npm 11.16.0, Docker 28.5.1, and Git 2.54. Verified live reachability of the Brilliant Directories sitemap (`https://support.brilliantdirectories.com/support/sitemap.xml`) via HTTP/200.
- **Architectural Decision**: Selected Python 3.12 managed via `uv` for backend compatibility with PostgreSQL/pgvector async drivers, and strict TypeScript for Task 2. Initialized root git repository and structured directories according to the required specification.

### Interaction 2: Deterministic Testing & LLM Provider Abstraction
- **Context**: Ensuring automated unit and regression tests run reproducibly without requiring live paid API credits, while maintaining full production-grade Anthropic Claude API SDK integration for deployed environments.
- **Architectural Decision**: Designed an extensible `LLMClient` protocol with dual implementations:
  1. `ClaudeClient`: Uses the official `@anthropic-ai/sdk` and `anthropic` Python client with Claude 3.7 Sonnet / Claude 3.5 Haiku.
  2. `MockClaudeClient`: Deterministic mock adapter capable of handling structured output validation, citation verification, and test failure simulation without network reliance.

*(Subsequent prompts and genuine rejections will be appended incrementally as milestones are executed.)*
