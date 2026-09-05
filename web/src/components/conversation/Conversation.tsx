"use client";

import { useEffect, useRef } from "react";

export type Message = {
  id: number;
  role: "user" | "assistant";
  content: string;
};

type ConversationProps = {
  messages: Message[];
};

function EmptyState() {
  return (
    <div className="mx-auto flex min-h-0 w-full max-w-[54rem] flex-1 flex-col items-center justify-center px-[clamp(.75rem,3vw,2rem)] py-[clamp(1.25rem,3.5vh,3rem)]">
      <div className="relative mx-auto mb-[clamp(.9rem,2vh,1.75rem)]">
        <div className="absolute -inset-7 rounded-full bg-reiterate-orange/5 blur-3xl motion-safe:animate-[reiterate-pulse_4s_ease-in-out_infinite]" />
        <div className="relative grid size-[clamp(3rem,5vw,4.5rem)] place-items-center rounded-[clamp(.9rem,1.6vw,1.3rem)] border border-reiterate-orange/20 bg-gradient-to-br from-reiterate-orange/14 via-reiterate-amber/7 to-reiterate-red/3 text-[clamp(1.05rem,1.6vw,1.3rem)] font-bold shadow-[0_1rem_3rem_rgba(239,68,68,.06),inset_0_1px_rgba(255,255,255,.05)] motion-safe:animate-[reiterate-float_6s_ease-in-out_infinite]">R</div>
      </div>

      <div className="mx-auto max-w-[48rem] text-center">
        <p className="mb-2 text-[0.62rem] font-bold uppercase tracking-[0.24em] text-reiterate-orange/70">A workspace for better thinking</p>
        <h1 className="text-[clamp(1.75rem,4.6vw,4rem)] font-semibold leading-[0.98] tracking-[-0.055em]">What are you<br /><span className="bg-gradient-to-r from-reiterate-orange via-reiterate-amber to-reiterate-red bg-clip-text text-transparent">working on?</span></h1>
        <p className="mx-auto mt-[clamp(.65rem,1.5vh,1.1rem)] max-w-[37rem] text-[clamp(.78rem,1.2vw,.96rem)] leading-6 text-reiterate-muted/70">Bring an idea, question, or half-formed thought. Reiterate helps you push it further.</p>
      </div>
    </div>
  );
}

export function Conversation({ messages }: ConversationProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const previousMessageCount = useRef(messages.length);

  useEffect(() => {
    if (messages.length > previousMessageCount.current) {
      const container = scrollRef.current;
      if (container) {
        container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });
      }
    }
    previousMessageCount.current = messages.length;
  }, [messages.length]);

  return (
    <div ref={scrollRef} className="relative flex min-h-0 min-w-0 flex-1 flex-col overflow-y-auto overscroll-contain">
      {messages.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="mx-auto flex w-full max-w-[54rem] flex-col gap-[clamp(1.25rem,4vh,2.5rem)] px-[clamp(.75rem,2vw,0rem)] py-[clamp(1.25rem,4vh,3.5rem)]">
          {messages.map((message) => (
            <article className={message.role === "user" ? "ml-auto w-[min(88%,42rem)] max-w-full" : "w-[min(92%,46rem)] max-w-full"} key={message.id}>
              <div className="mb-2 flex items-center gap-2 text-[0.62rem] font-bold uppercase tracking-[0.16em] text-reiterate-dim"><span className={message.role === "user" ? "size-1.5 rounded-full bg-reiterate-amber" : "size-1.5 rounded-full bg-reiterate-orange"} />{message.role === "user" ? "You" : "Reiterate"}</div>
              <div className={message.role === "user" ? "rounded-[1.35rem_1.35rem_.4rem_1.35rem] border border-reiterate-orange/10 bg-reiterate-raised/75 px-[clamp(.9rem,2vw,1.25rem)] py-4 shadow-[inset_0_1px_rgba(255,255,255,.03)]" : "rounded-[1.35rem_1.35rem_1.35rem_.4rem] border border-white/[0.06] bg-white/[0.018] px-[clamp(.9rem,2vw,1.25rem)] py-4"}>
                <p className="whitespace-pre-wrap break-words text-[0.92rem] leading-7 text-reiterate-text">{message.content}</p>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
