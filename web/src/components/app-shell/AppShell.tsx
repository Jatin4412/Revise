"use client";

import { FormEvent, useState } from "react";
import styles from "./AppShell.module.css";

type Message = {
  id: number;
  role: "user" | "assistant";
  content: string;
};

const sessions = ["New conversation", "Understanding Reiterate", "Project planning"];

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
        <div className={styles.brand}>Reiterate</div>
        <button className={styles.newSession} type="button" onClick={() => setMessages([])}>
          <span>+</span> New session
        </button>

        <nav className={styles.sessions} aria-label="Sessions">
          <span className={styles.sectionLabel}>Sessions</span>
          {sessions.map((session, index) => (
            <button className={styles.session} type="button" key={session}>
              <span className={styles.sessionDot} />
              <span>{index === 0 && messages.length > 0 ? "Current session" : session}</span>
            </button>
          ))}
        </nav>

        <div className={styles.sidebarFooter}>
          <button className={styles.footerButton} type="button">Settings</button>
        </div>
      </aside>

      <section className={styles.workspace} aria-label="Conversation">
        <header className={styles.header}>
          <span>Reiterate</span>
          <span className={styles.status}>Ready</span>
        </header>

        <div className={styles.conversation}>
          {messages.length === 0 ? (
            <div className={styles.emptyState}>
              <div className={styles.mark}>R</div>
              <h1>What are you working on?</h1>
              <p>Start a session and Reiterate will help you refine the work through iteration.</p>
            </div>
          ) : (
            <div className={styles.messageList}>
              {messages.map((message) => (
                <article className={`${styles.message} ${message.role === "user" ? styles.userMessage : ""}`} key={message.id}>
                  <span className={styles.messageRole}>{message.role === "user" ? "You" : "Reiterate"}</span>
                  <p>{message.content}</p>
                </article>
              ))}
            </div>
          )}
        </div>

        <div className={styles.composerWrap}>
          <form className={styles.composer} onSubmit={handleSubmit}>
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  event.currentTarget.form?.requestSubmit();
                }
              }}
              placeholder="Message Reiterate..."
              rows={1}
              aria-label="Message Reiterate"
            />
            <button className={styles.send} type="submit" disabled={!input.trim()} aria-label="Send message">
              ↑
            </button>
          </form>
          <p className={styles.composerHint}>Enter to send · Shift + Enter for a new line</p>
        </div>
      </section>
    </main>
  );
}
