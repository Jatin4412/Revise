export type Message = {
  id: number;
  role: "user" | "assistant";
  content: string;
};

type ConversationProps = {
  messages: Message[];
  starters: string[];
  onStarterSelect: (starter: string) => void;
};

function EmptyState({ starters, onStarterSelect }: Omit<ConversationProps, "messages">) {
  return (
    <div className="mx-auto flex min-h-0 w-[min(92vw,54rem)] flex-1 flex-col justify-center py-[clamp(1.25rem,3.5vh,3rem)]">
      <div className="relative mx-auto mb-[clamp(.9rem,2vh,1.75rem)]">
        <div className="absolute -inset-7 rounded-full bg-reiterate-orange/6 blur-3xl motion-safe:animate-[reiterate-pulse_4s_ease-in-out_infinite]" />
        <div className="relative grid size-[clamp(3.25rem,5vw,4.5rem)] place-items-center rounded-[clamp(.9rem,1.6vw,1.3rem)] border border-reiterate-orange/20 bg-gradient-to-br from-reiterate-orange/14 via-reiterate-amber/7 to-reiterate-red/3 text-[clamp(1.05rem,1.6vw,1.3rem)] font-bold shadow-[0_1rem_3rem_rgba(239,68,68,.07),inset_0_1px_rgba(255,255,255,.05)] motion-safe:animate-[reiterate-float_6s_ease-in-out_infinite]">R</div>
      </div>

      <div className="mx-auto max-w-[48rem] text-center">
        <p className="mb-2 text-[0.62rem] font-bold uppercase tracking-[0.24em] text-reiterate-orange/70">A workspace for better thinking</p>
        <h1 className="text-[clamp(2rem,4.6vw,4rem)] font-semibold leading-[0.98] tracking-[-0.055em]">What are you<br /><span className="bg-gradient-to-r from-reiterate-orange via-reiterate-amber to-reiterate-red bg-clip-text text-transparent">working on?</span></h1>
        <p className="mx-auto mt-[clamp(.65rem,1.5vh,1.1rem)] max-w-[37rem] text-[clamp(.82rem,1.2vw,.96rem)] leading-6 text-reiterate-muted/70">Bring an idea, question, or half-formed thought. Reiterate helps you push it further.</p>
      </div>

      <div className="mx-auto mt-[clamp(1rem,2.5vh,2rem)] grid w-full max-w-[50rem] grid-cols-1 gap-[clamp(.5rem,1vw,.75rem)] sm:grid-cols-3">
        {starters.map((starter, index) => (
          <button className="group min-h-[clamp(5.5rem,10vh,7rem)] rounded-[1.2rem] border border-white/[0.07] bg-white/[0.018] p-[clamp(.75rem,1.1vw,.95rem)] text-left transition duration-200 hover:-translate-y-0.5 hover:border-reiterate-orange/20 hover:bg-reiterate-orange/[0.03] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-reiterate-orange/40" type="button" key={starter} onClick={() => onStarterSelect(starter)}>
            <span className="mb-3 flex size-6 items-center justify-center rounded-full border border-reiterate-orange/15 bg-reiterate-orange/6 text-[0.58rem] font-bold text-reiterate-orange/70">0{index + 1}</span>
            <span className="block text-[0.8rem] font-medium leading-5 text-reiterate-muted transition group-hover:text-reiterate-text">{starter}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

export function Conversation({ messages, starters, onStarterSelect }: ConversationProps) {
  return (
    <div className="relative flex min-h-0 flex-1 flex-col overflow-y-auto overscroll-contain">
      {messages.length === 0 ? (
        <EmptyState starters={starters} onStarterSelect={onStarterSelect} />
      ) : (
        <div className="mx-auto flex w-[min(92vw,54rem)] flex-col gap-[clamp(1.5rem,4vh,2.5rem)] py-[clamp(1.5rem,4vh,3.5rem)]">
          {messages.map((message) => (
            <article className={message.role === "user" ? "ml-auto w-[min(88%,42rem)]" : "w-[min(92%,46rem)]"} key={message.id}>
              <div className="mb-2 flex items-center gap-2 text-[0.62rem] font-bold uppercase tracking-[0.16em] text-reiterate-dim"><span className={message.role === "user" ? "size-1.5 rounded-full bg-reiterate-amber" : "size-1.5 rounded-full bg-reiterate-orange"} />{message.role === "user" ? "You" : "Reiterate"}</div>
              <div className={message.role === "user" ? "rounded-[1.35rem_1.35rem_.4rem_1.35rem] border border-reiterate-orange/10 bg-reiterate-raised/75 px-5 py-4 shadow-[inset_0_1px_rgba(255,255,255,.03)]" : "rounded-[1.35rem_1.35rem_1.35rem_.4rem] border border-white/[0.06] bg-white/[0.018] px-5 py-4"}>
                <p className="whitespace-pre-wrap text-[0.92rem] leading-7 text-reiterate-text">{message.content}</p>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
