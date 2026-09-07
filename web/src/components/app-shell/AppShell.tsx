"use client";

import { useEffect, useRef, useState } from "react";

function SendIcon() {
  return (
    <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="m5 12 14-7-4 14-3.5-6.5L5 12Z" />
      <path d="m11.5 12.5 3-1.5" />
    </svg>
  );
}

function PlusIcon() {
  return <svg aria-hidden="true" width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"><path d="M12 5v14" /><path d="M5 12h14" /></svg>;
}

function Logo() {
  return <div className="logo-mark" aria-label="Reiterate">R</div>;
}

export function AppShell() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<string[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 180)}px`;
  }, [input]);

  function submit() {
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
    <main className="chat-shell">
      <header className="chat-header">
        <button className="chat-brand" type="button" onClick={newChat} aria-label="New conversation">
          <Logo />
          <span>Reiterate</span>
        </button>
      </header>

      <section className="chat-scroll" aria-label="Conversation">
        {messages.length === 0 ? (
          <div className="welcome">
            <Logo />
            <h1>What do you want to work on?</h1>
            <p>Start a conversation and work through it with Reiterate.</p>
          </div>
        ) : (
          <div className="messages">
            {messages.map((message, index) => (
              <div className="message" key={`${message}-${index}`}>
                <div className="message-avatar">You</div>
                <div className="message-body">{message}</div>
              </div>
            ))}
          </div>
        )}
      </section>

      <div className="composer-area">
        <form className="composer" onSubmit={(event) => { event.preventDefault(); submit(); }}>
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
            <button type="button" className="attach-button" aria-label="Add attachment"><PlusIcon /></button>
            <button className="send-button" type="submit" disabled={!input.trim()} aria-label="Send message"><SendIcon /></button>
          </div>
        </form>
        <div className="composer-hint">Reiterate can make mistakes. Check important information.</div>
      </div>
    </main>
  );
}
