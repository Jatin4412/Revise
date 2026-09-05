"use client";

import { FormEvent, useState } from "react";

type Message = {
  id: number;
  role: "user" | "assistant";
  content: string;
};

const sessions = ["New conversation", "Understanding Reiterate", "Project planning"];
const starters = [
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

    setMessages((current) => [...current, { id: Date.now(), role: "user", content }]);
    setInput("");
  }

  return (
    <main className="relative flex min-h-dvh overflow-hidden bg-reiterate-bg text-reiterate-text">
      <div className="pointer-events-none absolute -left-[12vw] top-[18vh] size-[32vw] max-h-[34rem] max-w-[34rem] rounded-full bg-reiterate-orange/8 blur-[110px]" />
      <div className="pointer-events-none absolute right-[-10vw] top-[-12vh] size-[38vw] max-h-[42rem] max-w-[42rem] rounded-full bg-reiterate-red/7 blur-[120px]" />
      <div className="pointer-events-none absolute bottom-[-18vw] left-[42%] size-[34vw] max-h-[34rem] max-w-[34rem] rounded-full bg-reiterate-amber/5 blur-[110px]" />

      <aside className="relative z-10 hidden w-[clamp(15rem,18vw,18rem)] shrink-0 flex-col border-r border-white/7 bg-reiterate-deep/65 px-[clamp(1rem,1.5vw,1.5rem)] py-[clamp(1rem,2vh,1.5rem)] backdrop-blur-2xl lg:flex">
        <div className="mb-[clamp(1.5rem,3vh,2.5rem)] flex items-center justify-between px-1">
          <div>
            <p className="text-[0.68rem] font-semibold uppercase tracking-[0.24em] text-reiterate-muted/60">Workspace</p>
            <div className="mt-1 text-[clamp(1rem,1.2vw,1.125rem)] font-bold tracking-[-0.03em]">Reiterate</div>
          </div>
          <span className="grid size-8 place-items-center rounded-[0.8rem] border border-reiterate-orange/20 bg-gradient-to-br from-reiterate-orange/20 to-reiterate-red/8 text-sm font-bold shadow-[0_0_28px_rgba(251,146,60,.08)]">R</span>
        </div>

        <button className="group flex w-full items-center gap-3 rounded-2xl border border-reiterate-orange/15 bg-gradient-to-br from-reiterate-orange/12 to-reiterate-red/5 px-4 py-3 text-left text-sm font-semibold shadow-[inset_0_1px_rgba(255,255,255,.05)] transition duration-200 hover:-translate-y-px hover:border-reiterate-orange/30 hover:from-reiterate-orange/18 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-reiterate-orange/50" type="button" onClick={() => setMessages([])}>
          <span className="grid size-7 place-items-center rounded-xl bg-reiterate-orange/12 text-lg text-reiterate-orange transition-transform group-hover:rotate-90">+</span>
          New session
        </button>

        <nav className="mt-[clamp(1.5rem,4vh,2.75rem)]" aria-label="Sessions">
          <div className="mb-2 flex items-center justify-between px-2 text-[0.65rem] font-bold uppercase tracking-[0.18em] text-reiterate-dim">
            <span>Recent sessions</span><span>{sessions.length.toString().padStart(2, "0")}</span>
          </div>
          <div className="space-y-1">
            {sessions.map((session, index) => (
              <button className="group flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-[0.8rem] text-reiterate-muted transition hover:bg-white/[0.035] hover:text-reiterate-text focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-reiterate-orange/40" type="button" key={session}>
                <span className="size-1.5 shrink-0 rounded-full bg-reiterate-dim/70 transition group-hover:bg-reiterate-orange group-hover:shadow-[0_0_10px_rgba(251,146,60,.5)]" />
                <span className="truncate">{index === 0 && messages.length > 0 ? "Current session" : session}</span>
              </button>
            ))}
          </div>
        </nav>

        <div className="mt-auto border-t border-white/7 pt-3">
          <div className="mb-2 flex items-center gap-3 rounded-xl bg-white/[0.02] px-3 py-2.5">
            <span className="size-1.5 rounded-full bg-reiterate-orange shadow-[0_0_10px_rgba(251,146,60,.6)]" />
            <div><p className="text-xs font-medium">System ready</p><p className="text-[0.62rem] text-reiterate-dim">Reiterate core</p></div>
          </div>
          <button className="w-full rounded-xl px-3 py-2.5 text-left text-xs text-reiterate-dim transition hover:bg-white/[0.035] hover:text-reiterate-muted" type="button">⚙ Settings</button>
        </div>
      </aside>

      <section className="relative z-10 flex min-w-0 flex-1 flex-col overflow-hidden" aria-label="Conversation">
        <header className="flex h-[clamp(3.5rem,7vh,4.5rem)] shrink-0 items-center justify-between border-b border-white/7 bg-reiterate-bg/55 px-[clamp(1rem,3vw,3rem)] backdrop-blur-2xl">
          <div className="flex min-w-0 items-center gap-2.5"><span className="text-sm font-semibold tracking-[-0.02em]">Reiterate</span><span className="hidden text-reiterate-dim sm:inline">/</span><span className="hidden max-w-[18rem] truncate text-xs text-reiterate-dim sm:inline">Untitled session</span></div>
          <div className="flex items-center gap-2 rounded-full border border-white/7 bg-white/[0.025] px-3 py-1.5 text-[0.68rem] text-reiterate-muted"><span className="size-1.5 rounded-full bg-reiterate-orange shadow-[0_0_10px_rgba(251,146,60,.7)]" />Ready</div>
        </header>

        <div className="relative flex min-h-0 flex-1 flex-col overflow-y-auto">
          {messages.length === 0 ? (
            <div className="mx-auto flex min-h-full w-[min(92vw,54rem)] flex-1 flex-col justify-center py-[clamp(4rem,10vh,8rem)]">
              <div className="relative mx-auto mb-[clamp(1.75rem,4vh,2.75rem)]">
                <div className="absolute -inset-10 rounded-full bg-reiterate-orange/10 blur-3xl motion-safe:animate-[reiterate-pulse_4s_ease-in-out_infinite]" />
                <div className="relative grid size-[clamp(4rem,7vw,5.5rem)] place-items-center rounded-[clamp(1.25rem,2vw,1.6rem)] border border-reiterate-orange/25 bg-gradient-to-br from-reiterate-orange/20 via-reiterate-amber/10 to-reiterate-red/5 text-[clamp(1.25rem,2vw,1.5rem)] font-bold shadow-[0_1rem_4rem_rgba(239,68,68,.12),inset_0_1px_rgba(255,255,255,.08)] motion-safe:animate-[reiterate-float_6s_ease-in-out_infinite]">R</div>
              </div>

              <div className="mx-auto max-w-[48rem] text-center">
                <p className="mb-3 text-[0.68rem] font-bold uppercase tracking-[0.28em] text-reiterate-orange/80">A workspace for better thinking</p>
                <h1 className="text-[clamp(2.35rem,5vw,4.5rem)] font-semibold leading-[0.98] tracking-[-0.055em]">What are you<br /><span className="bg-gradient-to-r from-reiterate-orange via-reiterate-amber to-reiterate-red bg-clip-text text-transparent">working on?</span></h1>
                <p className="mx-auto mt-[clamp(1rem,2.5vh,1.5rem)] max-w-[37rem] text-[clamp(0.9rem,1.4vw,1rem)] leading-7 text-reiterate-muted/80">Bring an idea, question, or half-formed thought. Reiterate helps you push it further.</p>
              </div>

              <div className="mx-auto mt-[clamp(2rem,5vh,3.5rem)] grid w-full max-w-[50rem] grid-cols-1 gap-3 sm:grid-cols-3">
                {starters.map((starter, index) => (
                  <button className="group min-h-[clamp(7rem,14vh,8.5rem)] rounded-[1.35rem] border border-white/7 bg-white/[0.025] p-4 text-left transition duration-200 hover:-translate-y-1 hover:border-reiterate-orange/20 hover:bg-reiterate-orange/[0.045] hover:shadow-[0_1.5rem_4rem_rgba(0,0,0,.18)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-reiterate-orange/40" type="button" key={starter} onClick={() => setInput(starter)}>
                    <span className="mb-6 flex size-7 items-center justify-center rounded-full border border-reiterate-orange/15 bg-reiterate-orange/8 text-[0.65rem] font-bold text-reiterate-orange/80">0{index + 1}</span>
                    <span className="block text-sm font-medium leading-5 text-reiterate-muted transition group-hover:text-reiterate-text">{starter}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="mx-auto flex w-[min(92vw,54rem)] flex-col gap-8 py-[clamp(2rem,5vh,4rem)]">
              {messages.map((message) => (
                <article className={message.role === "user" ? "ml-auto w-[min(88%,42rem)]" : "w-[min(92%,46rem)]"} key={message.id}>
                  <div className="mb-2 flex items-center gap-2 text-[0.65rem] font-bold uppercase tracking-[0.16em] text-reiterate-dim"><span className={message.role === "user" ? "size-1.5 rounded-full bg-reiterate-amber" : "size-1.5 rounded-full bg-reiterate-orange"} />{message.role === "user" ? "You" : "Reiterate"}</div>
                  <div className={message.role === "user" ? "rounded-[1.35rem_1.35rem_.4rem_1.35rem] border border-reiterate-orange/10 bg-reiterate-raised/80 px-5 py-4 shadow-[inset_0_1px_rgba(255,255,255,.03)]" : "rounded-3xl border border-white/6 bg-white/[0.02] px-5 py-4"}><p className="whitespace-pre-wrap text-[0.95rem] leading-7 text-reiterate-text">{message.content}</p></div>
                </article>
              ))}
            </div>
          )}
        </div>

        <div className="relative z-20 shrink-0 px-[clamp(.75rem,3vw,3rem)] pb-[max(.75rem,env(safe-area-inset-bottom))] pt-2 sm:pb-5">
          <div className="mx-auto w-[min(92vw,54rem)]">
            <form className="group flex items-end gap-2 rounded-[1.35rem] border border-white/8 bg-reiterate-surface/90 p-2 shadow-[0_1.5rem_5rem_rgba(0,0,0,.3),0_0_3rem_rgba(251,146,60,.045),inset_0_1px_rgba(255,255,255,.05)] backdrop-blur-2xl transition focus-within:border-reiterate-orange/30 focus-within:shadow-[0_1.5rem_5rem_rgba(0,0,0,.35),0_0_3rem_rgba(251,146,60,.08),inset_0_1px_rgba(255,255,255,.06)]" onSubmit={handleSubmit}>
              <textarea className="min-h-12 max-h-40 min-w-0 flex-1 resize-none border-0 bg-transparent px-3 py-2.5 text-[0.95rem] leading-6 text-reiterate-text outline-none placeholder:text-reiterate-dim/80" value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); event.currentTarget.form?.requestSubmit(); } }} placeholder="Start a thought..." rows={1} aria-label="Message Reiterate" />
              <button className="grid size-11 shrink-0 place-items-center rounded-[1rem] bg-gradient-to-br from-reiterate-orange via-reiterate-amber to-reiterate-red text-[1.15rem] font-bold text-[#1a0c03] shadow-[0_.5rem_1.5rem_rgba(251,146,60,.18)] transition duration-200 hover:-translate-y-0.5 hover:shadow-[0_.65rem_1.8rem_rgba(251,146,60,.28)] disabled:cursor-default disabled:opacity-25 disabled:shadow-none" type="submit" disabled={!input.trim()} aria-label="Send message">↑</button>
            </form>
            <p className="mt-2 text-center text-[0.62rem] text-reiterate-dim/70">Enter to send <span className="px-1">·</span> Shift + Enter for a new line</p>
          </div>
        </div>
      </section>
    </main>
  );
}
