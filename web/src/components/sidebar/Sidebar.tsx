type SidebarProps = {
  sessions: string[];
  hasMessages: boolean;
  onNewSession: () => void;
  isOpen: boolean;
  onToggle: () => void;
};

function Icon({ name, className = "size-5" }: { name: "chevron-left" | "chevron-right" | "edit" | "grid" | "settings"; className?: string }) {
  const paths = {
    "chevron-left": "m14.5 6-6 6 6 6",
    "chevron-right": "m9.5 6 6 6-6 6",
    edit: "M12 20h9M16.5 3.5a2.12 2.12 0 0 1 3 3L8 18l-4 1 1-4Z",
    grid: "M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z",
    settings: "M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7",
  } as const;

  return <svg aria-hidden="true" className={className} fill="none" viewBox="0 0 24 24"><path d={paths[name]} stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.7" /></svg>;
}

export function Sidebar({ sessions, hasMessages, onNewSession, isOpen, onToggle }: SidebarProps) {
  if (!isOpen) {
    return (
      <aside className="flex h-full w-full flex-col items-center bg-reiterate-deep/90 py-3">
        <div className="flex w-full flex-col items-center gap-2 px-1.5">
          <button
            className="grid size-9 place-items-center rounded-[0.85rem] border border-reiterate-orange/20 bg-gradient-to-br from-reiterate-orange/15 to-reiterate-red/5 text-sm font-bold text-reiterate-text transition hover:border-reiterate-orange/35 hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-reiterate-orange/40"
            type="button"
            onClick={onToggle}
            aria-label="Open sidebar"
            title="Open sidebar"
          >
            R
          </button>
          <span className="my-1 h-px w-6 bg-white/[0.07]" aria-hidden="true" />
          <button className="grid size-9 place-items-center rounded-xl text-reiterate-muted transition hover:bg-white/[0.045] hover:text-reiterate-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-reiterate-orange/40" type="button" onClick={onNewSession} aria-label="New session" title="New session"><Icon name="edit" /></button>
          <button className="grid size-9 place-items-center rounded-xl text-reiterate-dim transition hover:bg-white/[0.045] hover:text-reiterate-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-reiterate-orange/40" type="button" onClick={onToggle} aria-label="Open sessions" title="Open sessions"><Icon name="grid" /></button>
        </div>
        <div className="mt-auto flex flex-col items-center gap-3">
          <span className="size-1.5 rounded-full bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,.55)]" aria-label="System ready" title="System ready" />
          <button className="grid size-9 place-items-center rounded-xl text-reiterate-dim transition hover:bg-white/[0.045] hover:text-reiterate-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-reiterate-orange/40" type="button" onClick={onToggle} aria-label="Expand sidebar" title="Expand sidebar"><Icon name="chevron-right" className="size-4" /></button>
        </div>
      </aside>
    );
  }

  return (
    <aside className="flex h-full min-h-0 w-full flex-col bg-reiterate-deep/98 p-[clamp(1rem,1.5vw,1.5rem)] shadow-[1.5rem_0_4rem_rgba(0,0,0,.2)] lg:shadow-none">
      <div className="mb-[clamp(1.25rem,3vh,2.25rem)] flex items-center justify-between gap-3 px-1">
        <div className="flex min-w-0 items-center gap-3">
          <span className="grid size-9 shrink-0 place-items-center rounded-[0.8rem] border border-reiterate-orange/20 bg-gradient-to-br from-reiterate-orange/15 to-reiterate-red/5 text-sm font-bold">R</span>
          <div className="min-w-0"><span className="block text-[0.58rem] font-semibold uppercase tracking-[0.22em] text-reiterate-muted/50">Workspace</span><span className="mt-0.5 block truncate text-[1.05rem] font-bold tracking-[-0.03em]">Reiterate</span></div>
        </div>
        <button className="grid size-9 shrink-0 place-items-center rounded-xl border border-white/[0.06] text-reiterate-dim transition hover:border-reiterate-orange/20 hover:bg-white/[0.035] hover:text-reiterate-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-reiterate-orange/40" type="button" onClick={onToggle} aria-label="Minimize sidebar" title="Minimize sidebar"><Icon name="chevron-left" className="size-4" /></button>
      </div>

      <button className="group flex w-full items-center gap-3 rounded-[1rem] border border-reiterate-orange/15 bg-gradient-to-br from-reiterate-orange/10 to-reiterate-red/4 px-3.5 py-3 text-left text-sm font-semibold transition hover:-translate-y-px hover:border-reiterate-orange/25 hover:bg-reiterate-orange/[0.08] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-reiterate-orange/40" type="button" onClick={onNewSession}><span className="grid size-8 place-items-center rounded-[0.7rem] bg-reiterate-orange/10 text-lg text-reiterate-orange">+</span><span>New session</span></button>

      <nav className="mt-[clamp(1.25rem,4vh,2.5rem)]" aria-label="Sessions">
        <div className="mb-2 flex items-center justify-between px-2 text-[0.58rem] font-bold uppercase tracking-[0.2em] text-reiterate-dim"><span>Recent sessions</span><span>{sessions.length.toString().padStart(2, "0")}</span></div>
        <div className="space-y-0.5">{sessions.map((session, index) => <button className="group flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-[0.8rem] text-reiterate-muted transition hover:bg-white/[0.035] hover:text-reiterate-text focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-reiterate-orange/40" type="button" key={session}><span className="size-1.5 shrink-0 rounded-full bg-reiterate-dim/70 transition group-hover:bg-reiterate-orange" /><span className="truncate">{index === 0 && hasMessages ? "Current session" : session}</span></button>)}</div>
      </nav>

      <div className="mt-auto border-t border-white/[0.06] pt-3"><div className="mb-1 flex items-center gap-3 rounded-xl px-3 py-2.5"><span className="size-1.5 rounded-full bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,.55)]" /><div><p className="text-xs font-medium">System ready</p><p className="text-[0.62rem] text-reiterate-dim">Reiterate core</p></div></div><button className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-xs text-reiterate-dim transition hover:bg-white/[0.035] hover:text-reiterate-muted" type="button"><Icon name="settings" className="size-4" />Settings</button></div>
    </aside>
  );
}
