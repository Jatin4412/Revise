"use client";

import { useEffect, useState, type FormEvent } from "react";

import { Composer } from "@/components/composer/Composer";
import { Conversation, type Message } from "@/components/conversation/Conversation";
import { Sidebar } from "@/components/sidebar/Sidebar";
import { WorkspaceHeader } from "@/components/workspace/WorkspaceHeader";

const sessions = ["New conversation", "Understanding Reiterate", "Project planning"];
const starters = [
  "Help me think through an idea",
  "Challenge my current reasoning",
  "Turn these rough notes into a plan",
];

export function AppShell() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  useEffect(() => {
    if (!mobileSidebarOpen) return;
    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setMobileSidebarOpen(false);
    }
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [mobileSidebarOpen]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const content = input.trim();
    if (!content) return;
    setMessages((current) => [...current, { id: Date.now(), role: "user", content }]);
    setInput("");
  }

  function handleNewSession() {
    setMessages([]);
    setInput("");
    setMobileSidebarOpen(false);
  }

  return (
    <main className="relative h-dvh w-full overflow-hidden bg-reiterate-bg p-[clamp(.5rem,1vw,.9rem)] text-reiterate-text">
      <div className="pointer-events-none absolute -left-[12vw] top-[18vh] size-[32vw] max-h-[34rem] max-w-[34rem] rounded-full bg-reiterate-orange/6 blur-[110px]" />
      <div className="pointer-events-none absolute right-[-10vw] top-[-12vh] size-[38vw] max-h-[42rem] max-w-[42rem] rounded-full bg-reiterate-red/5 blur-[120px]" />

      <div className="relative flex h-full min-h-0 min-w-0 overflow-hidden rounded-[clamp(1.25rem,1.8vw,1.75rem)] border border-white/[0.07] bg-reiterate-bg/90 shadow-[0_1rem_4rem_rgba(0,0,0,.22),inset_0_1px_rgba(255,255,255,.035)] backdrop-blur-xl">
        <div className={`relative z-20 hidden h-full shrink-0 border-r border-white/[0.07] transition-[width] duration-200 lg:block ${sidebarOpen ? "w-[clamp(15rem,18vw,18rem)]" : "w-14"}`}>
          <Sidebar
            sessions={sessions}
            hasMessages={messages.length > 0}
            onNewSession={handleNewSession}
            isOpen={sidebarOpen}
            onToggle={() => setSidebarOpen((current) => !current)}
          />
        </div>

        <section className="relative z-10 flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden" aria-label="Conversation workspace">
          <WorkspaceHeader />
          <Conversation messages={messages} starters={starters} onStarterSelect={setInput} />
          <Composer value={input} onChange={setInput} onSubmit={handleSubmit} />
        </section>

        <div className={`absolute inset-y-0 left-0 z-40 w-14 lg:hidden ${mobileSidebarOpen ? "w-[min(18rem,86vw)]" : "w-14"}`}>
          <Sidebar
            sessions={sessions}
            hasMessages={messages.length > 0}
            onNewSession={handleNewSession}
            isOpen={mobileSidebarOpen}
            onToggle={() => setMobileSidebarOpen((current) => !current)}
          />
        </div>

        {mobileSidebarOpen && (
          <button
            className="absolute inset-0 z-30 bg-black/45 backdrop-blur-[1px] lg:hidden"
            type="button"
            onClick={() => setMobileSidebarOpen(false)}
            aria-label="Close sidebar"
          />
        )}
      </div>
    </main>
  );
}
