export type WorkspaceStatus = "ready" | "processing" | "blocked";

type WorkspaceHeaderProps = {
  status?: WorkspaceStatus;
  onMenu?: () => void;
};

const statusConfig: Record<WorkspaceStatus, { label: string; dotClass: string; glowClass: string }> = {
  ready: { label: "Ready", dotClass: "bg-emerald-400", glowClass: "shadow-[0_0_10px_rgba(52,211,153,.55)]" },
  processing: { label: "In process", dotClass: "bg-reiterate-orange", glowClass: "shadow-[0_0_10px_rgba(251,146,60,.65)]" },
  blocked: { label: "Blocked", dotClass: "bg-red-500", glowClass: "shadow-[0_0_10px_rgba(239,68,68,.6)]" },
};

function MenuIcon() {
  return <svg aria-hidden="true" className="size-[1.05rem]" fill="none" viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" strokeLinecap="round" strokeWidth="1.7" /></svg>;
}

export function WorkspaceHeader({ status = "ready", onMenu }: WorkspaceHeaderProps) {
  const currentStatus = statusConfig[status];

  return (
    <header className="flex min-h-[clamp(3.25rem,7vh,4.25rem)] shrink-0 items-center justify-between border-b border-white/[0.07] bg-reiterate-bg/45 px-[clamp(.7rem,2.5vw,2.5rem)] backdrop-blur-2xl">
      <div className="flex min-w-0 items-center gap-2.5">
        {onMenu && <button className="mr-1 grid size-8 shrink-0 place-items-center rounded-lg text-reiterate-muted transition hover:bg-white/[0.045] hover:text-reiterate-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-reiterate-orange/40 lg:hidden" type="button" onClick={onMenu} aria-label="Open sidebar"><MenuIcon /></button>}
        <span className="text-sm font-semibold tracking-[-0.02em] max-[360px]:hidden">Reiterate</span>
        <span className="hidden text-reiterate-dim sm:inline">/</span>
        <span className="hidden max-w-[18rem] truncate text-xs text-reiterate-dim sm:inline">Untitled session</span>
      </div>
      <div className="flex items-center gap-2 rounded-full border border-white/[0.07] bg-white/[0.02] px-3 py-1.5 text-[0.65rem] text-reiterate-muted max-[360px]:px-2">
        <span className={`size-1.5 rounded-full ${currentStatus.dotClass} ${currentStatus.glowClass}`} />
        <span className="max-[360px]:hidden">{currentStatus.label}</span>
      </div>
    </header>
  );
}
