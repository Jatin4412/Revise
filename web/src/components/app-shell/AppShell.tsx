"use client";

import { useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";

type IconProps = { size?: number };

function Icon({ children, size = 18 }: IconProps & { children: ReactNode }) {
  return (
    <svg aria-hidden="true" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      {children}
    </svg>
  );
}

function Logo() {
  return (
    <div className="logo-mark" aria-label="Reiterate">
      <span>R</span>
    </div>
  );
}

export function AppShell() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<string[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 180)}px`;
  }, [input]);

  function submit(event?: FormEvent) {
    event?.preventDefault();
    const value = input.trim();
    if (!value) return;
    setMessages((current) => [...current, value]);
    setInput("");
  }

  function newChat() {
    setMessages([]);
    setInput("");
    textareaRef.current?.focus();
  }

  return (
    <main className="app-shell">
      <aside className={`sidebar ${sidebarOpen ? "is-open" : "is-collapsed"}`}>
        <div className="sidebar-top">
          <button className="brand-button" type="button" onClick={() => setSidebarOpen((value) => !value)} aria-label="Toggle sidebar">
            <Logo />
            {sidebarOpen && <span>Reiterate</span>}
          </button>
          <button className="icon-button" type="button" onClick={() => setSidebarOpen((value) => !value)} aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}>
            <Icon><path d="M6 4v16" /><path d="m15 8-4 4 4 4" /></Icon>
          </button>
        </div>

        <button className="new-chat" type="button" onClick={newChat}>
          <Icon><path d="M12 5v14" /><path d="M5 12h14" /></Icon>
          {sidebarOpen && <span>New chat</span>}
          {sidebarOpen && <kbd>⌘ K</kbd>}
        </button>

        {sidebarOpen && (
          <div className="sidebar-content">
            <div className="sidebar-label">Recent</div>
            <div className="empty-history">Your conversations<br />will appear here.</div>
          </div>
        )}

        <div className="sidebar-bottom">
          <button className="side-item" type="button">
            <Icon><path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z" /><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-1.8 1.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.1h-2.6V20a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1-1.8-1.8.1-.1A1.7 1.7 0 0 0 8 15a1.7 1.7 0 0 0-1.6-1H6v-2.6h.4A1.7 1.7 0 0 0 8 10a1.7 1.7 0 0 0-.3-1.9l-.1-.1 1.8-1.8.1.1a1.7 1.7 0 0 0 1.9.3 1.7 1.7 0 0 0 1-1.6V5h2.6v.1a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1 1.8 1.8-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.1V14h-.1a1.7 1.7 0 0 0-1.6 1Z" /></Icon>
            {sidebarOpen && <span>Settings</span>}
          </button>
          {sidebarOpen && <div className="status-line"><span /> Engine ready</div>}
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div className="topbar-title">New conversation</div>
          <button className="topbar-action" type="button" onClick={newChat}>
            <Icon size={17}><path d="M12 5v14" /><path d="M5 12h14" /></Icon>
            <span>New chat</span>
          </button>
        </header>

        <div className="conversation">
          {messages.length === 0 ? (
            <div className="welcome">
              <div className="welcome-mark"><Logo /></div>
              <h1>What do you want to work on?</h1>
              <p>Ask anything. Reiterate will help you think it through, refine it, and move it forward.</p>
            </div>
          ) : (
            <div className="messages">
              {messages.map((message, index) => (
                <div className="message-row" key={`${message}-${index}`}>
                  <div className="message-avatar"><span>You</span></div>
                  <div className="message-body">{message}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="composer-area">
          <form className="composer" onSubmit={submit}>
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  submit();
                }
              }}
              placeholder="Message Reiterate..."
              rows={1}
              aria-label="Message Reiterate"
            />
            <div className="composer-footer">
              <div className="composer-tools">
                <button type="button" className="tool-button" aria-label="Attach file">
                  <Icon size={18}><path d="m20.5 11.5-7.9 7.9a5 5 0 0 1-7.1-7.1l8.5-8.5a3.5 3.5 0 0 1 5 5l-8.6 8.6a2 2 0 0 1-2.8-2.8l7.8-7.8" /></Icon>
                </button>
                <button type="button" className="model-button" aria-label="Choose model">
                  Reiterate <span>⌄</span>
                </button>
              </div>
              <button className="send-button" type="submit" disabled={!input.trim()} aria-label="Send message">
                <Icon size={18}><path d="m5 12 14-7-4 14-3.5-6.5L5 12Z" /><path d="m11.5 12.5 3-1.5" /></Icon>
              </button>
            </div>
          </form>
          <div className="composer-hint">Reiterate can make mistakes. Check important information.</div>
        </div>
      </section>
    </main>
  );
}
