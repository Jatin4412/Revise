export type WorkspaceStatus = "ready" | "processing" | "blocked";

type WorkspaceHeaderProps = {
  status?: WorkspaceStatus;
};

const statusConfig: Record<WorkspaceStatus, { label: string; dotClass: string; glowClass: string }> = {
  ready: { label: "Ready", dotClass: "bg-emerald-400", glowClass: "shadow-[0_0_10px_rgba(52,211,153,.55)]" },
  processing: { label: "In process", dotClass: "bg-reiterate-orange", glowClass: "shadow-[0_0_10px_rgba(251,146,60,.65)]" },
  blocked: { label: "Blocked", dotClass: "bg-red-500", glowClass: "shadow-[0_0_10px_rgba(239,68,68,.6)]" },
};

export function WorkspaceHeader({ status = "ready" }: WorkspaceHeaderProps) {
  const currentStatus = statusConfig[status];

  return (
    <header className="flex min-h-[clamp(3.25rem,7vh,4.25rem)] shrink-0 items-center justify-between border-b border-white/[0.07] bg-reiterate-bg/45 px-[clamp(.75rem,2.5vw,2.5rem)] backdrop-blur-2xl">
      <div className="flex min-w-0 items-center gap-2.5">
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
