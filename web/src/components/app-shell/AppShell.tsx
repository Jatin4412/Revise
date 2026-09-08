"use client";

import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { createEngineClient, type EngineModel } from "@/engine/client";

const MODELS: Array<EngineModel & { label: string; providerLabel: string }> = [
  { provider: "gemini", model: "gemini-3.7-flash", label: "Gemini 3.7 Flash", providerLabel: "Gemini" },
  { provider: "gemini", model: "gemini-3.1-flash-lite", label: "Gemini 3.1 Flash-Lite", providerLabel: "Gemini" },
  { provider: "groq", model: "openai/gpt-oss-120b", label: "GPT-OSS 120B", providerLabel: "Groq" },
  { provider: "openrouter", model: "openrouter/free", label: "OpenRouter Free", providerLabel: "OpenRouter" },
];

type Message = {
  role: "user" | "assistant";
  text: string;
};

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

function AssistantMarkdown({ content }: { content: string }) {
  return (
    <div className="markdown-content">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          pre: ({ children }) => <pre className="markdown-code-block">{children}</pre>,
          code: ({ className, children, ...props }) => {
            if (className) {
              return <code className={className} {...props}>{children}</code>;
            }
            return <code className="markdown-inline-code" {...props}>{children}</code>;
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

export function AppShell() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [modelOpen, setModelOpen] = useState(false);
  const [selectedModel, setSelectedModel] = useState(MODELS[0]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const scrollRef = useRef<HTMLElement>(null);
  const engineClient = useRef(createEngineClient());

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 180)}px`;
  }, [input]);

  useEffect(() => {
    const scroll = scrollRef.current;
    if (!scroll) return;
    scroll.scrollTo({ top: scroll.scrollHeight, behavior: "smooth" });
  }, [messages, isLoading, error]);

  async function submit() {
    const value = input.trim();
    if (!value || isLoading) return;

    setError(null);
    setMessages((current) => [...current, { role: "user", text: value }]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await engineClient.current.request({
        prompt: value,
        mode: "basic",
        primary_model: {
          provider: selectedModel.provider,
          model: selectedModel.model,
        },
      });

      setMessages((current) => [...current, { role: "assistant", text: response.text }]);
    } catch {
      setError("Revise couldn't generate a response right now.");
    } finally {
      setIsLoading(false);
      textareaRef.current?.focus();
    }
  }

  function newChat() {
    if (isLoading) return;
    setMessages([]);
    setInput("");
    setError(null);
    setModelOpen(false);
    textareaRef.current?.focus();
  }

  return (
    <main className="chat-shell">
      <header className="chat-header">
        <button className="chat-brand" type="button" onClick={newChat} aria-label="New conversation">
          <span>Reiterate</span>
        </button>
      </header>

      <section ref={scrollRef} className="chat-scroll" aria-label="Conversation">
        {messages.length === 0 && !isLoading && !error ? (
          <div className="welcome">
            <Logo />
            <h1>What do you want to work on?</h1>
            <p>Start a conversation and work through it with Reiterate.</p>
          </div>
        ) : (
          <div className="messages">
            {messages.map((message, index) => (
              <div className={`message message-${message.role}`} key={`${message.role}-${index}`}>
                {message.role === "assistant" && <div className="message-avatar">R</div>}
                <div className="message-body">
                  {message.role === "assistant" ? <AssistantMarkdown content={message.text} /> : message.text}
                </div>
                {message.role === "user" && <div className="message-avatar">You</div>}
              </div>
            ))}
            {isLoading && (
              <div className="message message-assistant" aria-live="polite">
                <div className="message-avatar">R</div>
                <div className="message-body message-thinking">Thinking…</div>
              </div>
            )}
            {error && (
              <div className="message message-assistant" role="alert">
                <div className="message-avatar">R</div>
                <div className="message-body message-error">{error}</div>
              </div>
            )}
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
            disabled={isLoading}
          />
          <div className="composer-footer">
            <div className="composer-left">
              <button type="button" className="attach-button" aria-label="Add attachment" disabled={isLoading}><PlusIcon /></button>
              <div className="model-picker">
                <button type="button" className="model-button" onClick={() => setModelOpen((open) => !open)} aria-haspopup="listbox" aria-expanded={modelOpen} disabled={isLoading}>
                  <span>{selectedModel.label}</span>
                  <ChevronIcon />
                </button>
                {modelOpen && !isLoading && (
                  <div className="model-menu" role="listbox" aria-label="Choose primary model">
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
            <button className="send-button" type="submit" disabled={!input.trim() || isLoading} aria-label="Send message"><SendIcon /></button>
          </div>
        </form>
      </div>
    </main>
  );
}
