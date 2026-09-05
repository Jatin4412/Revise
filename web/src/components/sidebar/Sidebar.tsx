type SidebarProps = {
  sessions: string[];
  hasMessages: boolean;
  onNewSession: () => void;
  isOpen: boolean;
  onToggle: () => void;
};

function ChevronIcon({ direction }: { direction: "left" | "right" }) {
  return (
    <svg aria-hidden="true" className="size-4" fill="none" viewBox="0 0 24 24">
      <path d={direction === "left" ? "m14.5 6-6 6 6 6" : "m9.5 6 6 6-6 6"} stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" />
    </svg>
  );
}

export function Sidebar({ sessions, hasMessages, onNewSession, isOpen, onToggle }: SidebarProps) {
  if (!isOpen) {
    return (
      <aside className="flex h-full w-12 flex-col items-center rounded-[clamp(1rem,1.6vw,1.4rem)] border border-white/[0.07] bg-reiterate-deep/80 py-3 shadow-[0_1.5rem_4rem_rgba(0,0,0,.18)] backdrop-blur-2xl">
        <span className="grid size-8 place-items-center rounded-[0.8rem] border border-reiterate-orange/20 bg-gradient-to-br from-reiterate-orange/20 to-reiterate-red/8 text-sm font-bold" aria-hidden="true">R</span>
        <button
          className="mt-auto grid size-8 place-items-center rounded-xl border border-white/[0.06] text-reiterate-dim transition hover:border-reiterate-orange/20 hover:bg-white/[0.035] hover:text-reiterate-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-reiterate-orange/40"
          type="button"
          onClick={onToggle}
          aria-label="Open sidebar"
          title="Open sidebar"
        >
          <ChevronIcon direction="right" />
        </button>
      </aside>
    );
  }

  return (
    <aside className="flex min-h-0 h-full w-full flex-col rounded-[clamp(1.25rem,1.8vw,1.6rem)] border border-white/[0.07] bg-reiterate-deep/95 p-[clamp(1rem,1.5vw,1.5rem)] shadow-[0_1.5rem_4rem_rgba(0,0,0,.18)] backdrop-blur-2xl lg:w-[clamp(15rem,18vw,18rem)] lg:shrink-0">
      <div className="mb-[clamp(1.25rem,3vh,2.25rem)] flex items-center justify-between gap-3 px-1">
        <div>
          <p className="text-[0.62rem] font-semibold uppercase tracking-[0.24em] text-reiterate-muted/55">Workspace</p>
          <div className="mt-1 text-[clamp(1rem,1.2vw,1.125rem)] font-bold tracking-[-0.03em]">Reiterate</div>
        </div>
        <button
          className="grid size-8 shrink-0 place-items-center rounded-[0.8rem] border border-white/[0.06] text-reiterate-dim transition hover:border-reiterate-orange/20 hover:bg-white/[0.035] hover:text-reiterate-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-reiterate-orange/40"
          type="button"
          onClick={onToggle}
          aria-label="Minimize sidebar"
          title="Minimize sidebar"
        >
          <ChevronIcon direction="left" />
        </button>
      </div>

      <button className="group flex w-full items-center gap-3 rounded-2xl border border-reiterate-orange/15 bg-gradient-to-br from-reiterate-orange/10 to-reiterate-red/5 px-4 py-3 text-left text-sm font-semibold transition duration-200 hover:-translate-y-px hover:border-reiterate-orange/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-reiterate-orange/50" type="button" onClick={onNewSession}>
        <span className="grid size-7 place-items-center rounded-xl bg-reiterate-orange/12 text-lg text-reiterate-orange transition-transform group-hover:rotate-90">+</span>
        New session
      </button>

      <nav className="mt-[clamp(1.25rem,4vh,2.5rem)]" aria-label="Sessions">
        <div className="mb-2 flex items-center justify-between px-2 text-[0.62rem] font-bold uppercase tracking-[0.18em] text-reiterate-dim">
          <span>Recent sessions</span><span>{sessions.length.toString().padStart(2, "0")}</span>
        </div>
        <div className="space-y-1">
          {sessions.map((session, index) => (
            <button className="group flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-[0.8rem] text-reiterate-muted transition hover:bg-white/[0.035] hover:text-reiterate-text focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-reiterate-orange/40" type="button" key={session}>
              <span className="size-1.5 shrink-0 rounded-full bg-reiterate-dim/70 transition group-hover:bg-reiterate-orange" />
              <span className="truncate">{index === 0 && hasMessages ? "Current session" : session}</span>
            </button>
          ))}
        </div>
      </nav>

      <div className="mt-auto border-t border-white/[0.07] pt-3">
        <div className="mb-2 flex items-center gap-3 rounded-xl bg-white/[0.02] px-3 py-2.5">
          <span className="size-1.5 rounded-full bg-reiterate-orange shadow-[0_0_10px_rgba(251,146,60,.6)]" />
          <div><p className="text-xs font-medium">System ready</p><p className="text-[0.62rem] text-reiterate-dim">Reiterate core</p></div>
        </div>
        <button className="w-full rounded-xl px-3 py-2.5 text-left text-xs text-reiterate-dim transition hover:bg-white/[0.035] hover:text-reiterate-muted" type="button">⚙ Settings</button>
      </div>
    </aside>
  );
}
