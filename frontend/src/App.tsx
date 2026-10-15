import React, { useState } from "react";
import { KnowledgeBrainScreen } from "./screens/KnowledgeBrainScreen";
import { InboxAgentScreen } from "./screens/InboxAgentScreen";
import { MeetingToScopeScreen } from "./screens/MeetingToScopeScreen";
import { Brain, Inbox, FileCheck, Layers } from "lucide-react";

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"task1" | "task2" | "task3">("task1");

  return (
    <div>
      {/* Header Navigation */}
      <header style={{ background: "var(--bg-secondary)", borderBottom: "1px solid var(--border-color)", padding: "14px 24px" }}>
        <div className="container" style={{ padding: 0, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <Layers size={26} color="var(--accent-blue)" />
            <div>
              <h1 style={{ fontSize: 18, margin: 0, fontWeight: 700 }}>AI Tech Consultant</h1>
              <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                BusinessLabs / Anthropic Applied AI Engineering Capstone
              </div>
            </div>
          </div>

          <nav style={{ display: "flex", gap: 8 }}>
            <button
              onClick={() => setActiveTab("task1")}
              className={`btn-primary`}
              style={{
                background: activeTab === "task1" ? "var(--accent-blue)" : "transparent",
                border: activeTab === "task1" ? "none" : "1px solid var(--border-color)",
                color: activeTab === "task1" ? "white" : "var(--text-muted)",
              }}
            >
              <Brain size={16} /> Task 1: Knowledge Brain
            </button>
            <button
              onClick={() => setActiveTab("task2")}
              className={`btn-primary`}
              style={{
                background: activeTab === "task2" ? "var(--accent-blue)" : "transparent",
                border: activeTab === "task2" ? "none" : "1px solid var(--border-color)",
                color: activeTab === "task2" ? "white" : "var(--text-muted)",
              }}
            >
              <Inbox size={16} /> Task 2: Inbox Agent
            </button>
            <button
              onClick={() => setActiveTab("task3")}
              className={`btn-primary`}
              style={{
                background: activeTab === "task3" ? "var(--accent-blue)" : "transparent",
                border: activeTab === "task3" ? "none" : "1px solid var(--border-color)",
                color: activeTab === "task3" ? "white" : "var(--text-muted)",
              }}
            >
              <FileCheck size={16} /> Task 3: Meeting to Scope
            </button>
          </nav>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="container">
        {activeTab === "task1" && <KnowledgeBrainScreen />}
        {activeTab === "task2" && <InboxAgentScreen />}
        {activeTab === "task3" && <MeetingToScopeScreen />}
      </main>
    </div>
  );
};

export default App;
