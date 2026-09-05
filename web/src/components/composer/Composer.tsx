import { useEffect, useRef } from "react";
import type { FormEvent, KeyboardEvent } from "react";

type ComposerProps = {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
};

export function Composer({ value, onChange, onSubmit }: ComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`;
  }, [value]);

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  }

  return (
    <div className="relative z-20 shrink-0 px-[clamp(.75rem,2.5vw,2.5rem)] pb-[max(.75rem,env(safe-area-inset-bottom))] pt-2 sm:pb-4">
      <div className="mx-auto w-[min(92vw,54rem)]">
        <form className="group flex items-end gap-2 rounded-[clamp(1.15rem,1.8vw,1.4rem)] border border-white/[0.08] bg-reiterate-surface/90 p-2 shadow-[0_1.25rem_4rem_rgba(0,0,0,.28),0_0_2.5rem_rgba(251,146,60,.035),inset_0_1px_rgba(255,255,255,.045)] backdrop-blur-2xl transition focus-within:border-reiterate-orange/25 focus-within:shadow-[0_1.5rem_4rem_rgba(0,0,0,.32),0_0_2.5rem_rgba(251,146,60,.055),inset_0_1px_rgba(255,255,255,.055)]" onSubmit={onSubmit}>
          <button className="mb-0.5 hidden size-9 shrink-0 place-items-center rounded-xl border border-white/[0.06] bg-white/[0.02] text-sm text-reiterate-dim transition hover:border-reiterate-orange/15 hover:text-reiterate-muted sm:grid" type="button" aria-label="Add attachment">+</button>
          <textarea ref={textareaRef} className="min-h-11 max-h-40 min-w-0 flex-1 resize-none overflow-y-auto border-0 bg-transparent px-2 py-2.5 text-[clamp(.88rem,1.2vw,.95rem)] leading-6 text-reiterate-text outline-none placeholder:text-reiterate-dim/75" value={value} onChange={(event) => onChange(event.target.value)} onKeyDown={handleKeyDown} placeholder="Start a thought..." rows={1} aria-label="Message Reiterate" />
          <span className="mb-2 hidden rounded-full border border-white/[0.05] px-2.5 py-1 text-[0.58rem] text-reiterate-dim md:block">Enter ↵</span>
          <button className="grid size-10 shrink-0 place-items-center rounded-[.9rem] bg-gradient-to-br from-reiterate-orange via-reiterate-amber to-reiterate-red text-[1.05rem] font-bold text-[#1a0c03] shadow-[0_.45rem_1.3rem_rgba(251,146,60,.15)] transition duration-200 hover:-translate-y-0.5 hover:shadow-[0_.6rem_1.6rem_rgba(251,146,60,.22)] disabled:cursor-default disabled:opacity-20 disabled:shadow-none" type="submit" disabled={!value.trim()} aria-label="Send message">↑</button>
        </form>
        <p className="mt-1.5 text-center text-[0.6rem] text-reiterate-dim/65">Enter to send <span className="px-1">·</span> Shift + Enter for a new line</p>
      </div>
    </div>
  );
}
