"use client";

import { useEffect, useRef, useState } from "react";
import { createEngineClient } from "@/engine/client";

const MODELS = [
  { provider: "google", model: "gemini-2.5-flash", label: "Gemini 2.5 Flash", providerLabel: "Google" },
  { provider: "google", model: "gemini-2.5-pro", label: "Gemini 2.5 Pro", providerLabel: "Google" },
];

function SendIcon() {
  return <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="m5 12 14-7-4 14-3.5-6.5L5 12Z" /><path d="m11.5 12.5 3-1.5" /></svg>;
}

function PlusIcon() {
  return <svg aria-hidden="true" width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"><path d="M12 5v14" /><path d="M5 12h14" /></svg>;
}

function ChevronIcon() {
  return <svg aria-hidden="true" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m7 10 5 5 5-5" /></svg>;
}

function Logo() {
  return <div className="logo-mark" aria-label="Reiterate">R</div>;
}

export function AppShell() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<string[]>([]);
  const [modelOpen, setModelOpen] = useState(false);
  const [selectedModel, setSelectedModel] = useState(MODELS[0]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const engineClient = useRef(createEngineClient());

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 180)}px`;
  }, [input]);

  async function submit() {
    const value = input.trim();
    if (!value) return;
    setMessages((current) => [...current, value]);
    setInput("");

    try {
      await engineClient.current.request({
        type: "chat",
        payload: {
          prompt: value,
          provider: selectedModel.provider,
          model: selectedModel.model,
        },
      });
    } catch {
      // The engine transport is intentionally not configured in the UI yet.
    }
  }

  function newChat() {
    setMessages([]);
    setInput("");
    setModelOpen(false);
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
        <form className="composer" onSubmit={(event) => { event.preventDefault(); void submit(); }}>
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                void submit();
              }
            }}
            placeholder="Message Reiterate..."
            rows={1}
            aria-label="Message Reiterate"
          />
          <div className="composer-footer">
            <div className="composer-left">
              <button type="button" className="attach-button" aria-label="Add attachment"><PlusIcon /></button>
              <div className="model-picker">
                <button type="button" className="model-button" onClick={() => setModelOpen((open) => !open)} aria-haspopup="listbox" aria-expanded={modelOpen}>
                  <span>{selectedModel.label}</span>
                  <ChevronIcon />
                </button>
                {modelOpen && (
                  <div className="model-menu" role="listbox" aria-label="Choose model">
                    {MODELS.map((option) => (
                      <button
                        key={`${option.provider}:${option.model}`}
                        type="button"
                        className={`model-option ${selectedModel.model === option.model ? "is-selected" : ""}`}
                        onClick={() => { setSelectedModel(option); setModelOpen(false); }}
                      >
                        <span className="model-option-copy">
                          <strong>{option.label}</strong>
                          <small>{option.providerLabel}</small>
                        </span>
                        {selectedModel.model === option.model && <span className="model-check">✓</span>}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
            <button className="send-button" type="submit" disabled={!input.trim()} aria-label="Send message"><SendIcon /></button>
          </div>
        </form>
        <div className="composer-hint">Reiterate can make mistakes. Check important information.</div>
      </div>
    </main>
  );
}
