"use client";

import { useState } from "react";

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

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const content = input.trim();
    if (!content) return;

    setMessages((current) => [...current, { id: Date.now(), role: "user", content }]);
    setInput("");
  }

  function handleNewSession() {
    setMessages([]);
    setInput("");
  }

  return (
    <main className="relative flex h-dvh w-full gap-[clamp(.5rem,1vw,.9rem)] overflow-hidden bg-reiterate-bg p-[clamp(.5rem,1vw,.9rem)] text-reiterate-text">
      <div className="pointer-events-none absolute -left-[12vw] top-[18vh] size-[32vw] max-h-[34rem] max-w-[34rem] rounded-full bg-reiterate-orange/8 blur-[110px]" />
      <div className="pointer-events-none absolute right-[-10vw] top-[-12vh] size-[38vw] max-h-[42rem] max-w-[42rem] rounded-full bg-reiterate-red/7 blur-[120px]" />
      <div className="pointer-events-none absolute bottom-[-18vw] left-[42%] size-[34vw] max-h-[34rem] max-w-[34rem] rounded-full bg-reiterate-amber/5 blur-[110px]" />

      <div className="relative z-10 hidden h-full lg:flex">
        <Sidebar sessions={sessions} hasMessages={messages.length > 0} onNewSession={handleNewSession} />
      </div>

      <section className="relative z-10 flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden rounded-[clamp(1.25rem,1.8vw,1.75rem)] border border-white/7 bg-reiterate-bg/85 shadow-[0_1rem_4rem_rgba(0,0,0,.2),inset_0_1px_rgba(255,255,255,.035)] backdrop-blur-xl" aria-label="Conversation workspace">
        <WorkspaceHeader />
        <Conversation messages={messages} starters={starters} onStarterSelect={setInput} />
        <Composer value={input} onChange={setInput} onSubmit={handleSubmit} />
      </section>
    </main>
  );
}
