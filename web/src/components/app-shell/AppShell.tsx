"use client";

import { FormEvent, useState } from "react";
import styles from "./AppShell.module.css";

type Message = {
  id: number;
  role: "user" | "assistant";
  content: string;
};

const sessions = ["New conversation", "Understanding Reiterate", "Project planning"];
const prompts = [
  "Help me think through an idea",
  "Challenge my current reasoning",
  "Turn these rough notes into a plan",
];

export function AppShell() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const content = input.trim();
    if (!content) return;

    setMessages((current) => [
      ...current,
      { id: Date.now(), role: "user", content },
    ]);
    setInput("");
  }

  return (
    <main className={styles.shell}>
      <aside className={styles.sidebar}>
        <div className={styles.brandRow}>
          <div className={styles.brandMark}>R</div>
          <div>
            <div className={styles.brand}>Reiterate</div>
            <div className={styles.brandSub}>Think. Refine. Repeat.</div>
          </div>
        </div>

        <button className={styles.newSession} type="button" onClick={() => setMessages([])}>
          <span className={styles.plus}>+</span>
          <span>New session</span>
          <kbd>⌘ N</kbd>
        </button>

        <nav className={styles.sessions} aria-label="Sessions">
          <span className={styles.sectionLabel}>Recent sessions</span>
          {sessions.map((session, index) => (
            <button className={styles.session} type="button" key={session}>
              <span className={`${styles.sessionDot} ${index === 0 ? styles.activeDot : ""}`} />
              <span>{index === 0 && messages.length > 0 ? "Current session" : session}</span>
            </button>
          ))}
        </nav>

        <div className={styles.sidebarFooter}>
          <div className={styles.sidebarPulse}>
            <span />
            <div>
              <strong>System ready</strong>
              <small>Reiterate core</small>
            </div>
          </div>
          <button className={styles.footerButton} type="button">
            <span>⚙</span> Settings
          </button>
        </div>
      </aside>

      <section className={styles.workspace} aria-label="Conversation">
        <div className={styles.ambientOrb} aria-hidden="true" />
        <div className={styles.ambientOrbTwo} aria-hidden="true" />

        <header className={styles.header}>
          <div className={styles.headerTitle}>
            <span>Workspace</span>
            <span className={styles.headerSlash}>/</span>
            <span className={styles.headerSession}>Untitled session</span>
          </div>
          <div className={styles.status}><span>Ready</span></div>
        </header>

        <div className={styles.conversation}>
          {messages.length === 0 ? (
            <div className={styles.emptyState}>
              <div className={styles.heroOrb} aria-hidden="true">
                <div className={styles.heroOrbCore}>R</div>
              </div>
              <div className={styles.eyebrow}><span /> A workspace for better thinking</div>
              <h1>What are you<br /><em>working on?</em></h1>
              <p>Bring an idea, question, or half-formed thought. Reiterate helps you push it further.</p>

              <div className={styles.promptGrid}>
                {prompts.map((prompt, index) => (
                  <button key={prompt} className={styles.promptCard} type="button" onClick={() => setInput(prompt)}>
                    <span className={styles.promptIndex}>0{index + 1}</span>
                    <span>{prompt}</span>
                    <span className={styles.promptArrow}>↗</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className={styles.messageList}>
              {messages.map((message) => (
                <article className={`${styles.message} ${message.role === "user" ? styles.userMessage : styles.assistantMessage}`} key={message.id}>
                  <span className={styles.messageRole}>{message.role === "user" ? "You" : "Reiterate"}</span>
                  <p>{message.content}</p>
                </article>
              ))}
            </div>
          )}
        </div>

        <div className={styles.composerWrap}>
          <form className={styles.composer} onSubmit={handleSubmit}>
            <div className={styles.composerAccent} aria-hidden="true" />
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  event.currentTarget.form?.requestSubmit();
                }
              }}
              placeholder="Start a thought..."
              rows={1}
              aria-label="Message Reiterate"
            />
            <button className={styles.send} type="submit" disabled={!input.trim()} aria-label="Send message">
              ↑
            </button>
          </form>
          <p className={styles.composerHint}>Enter to send <span>·</span> Shift + Enter for a new line</p>
        </div>
      </section>
    </main>
  );
}
