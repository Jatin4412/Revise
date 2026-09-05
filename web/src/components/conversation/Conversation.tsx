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
    <div className="mx-auto flex min-h-full w-[min(92vw,54rem)] flex-1 flex-col justify-center py-[clamp(2rem,6vh,5rem)]">
      <div className="relative mx-auto mb-[clamp(1.25rem,3vh,2rem)]">
        <div className="absolute -inset-8 rounded-full bg-reiterate-orange/7 blur-3xl motion-safe:animate-[reiterate-pulse_4s_ease-in-out_infinite]" />
        <div className="relative grid size-[clamp(3.75rem,6vw,5rem)] place-items-center rounded-[clamp(1rem,1.8vw,1.4rem)] border border-reiterate-orange/20 bg-gradient-to-br from-reiterate-orange/16 via-reiterate-amber/8 to-reiterate-red/4 text-[clamp(1.15rem,1.8vw,1.4rem)] font-bold shadow-[0_1rem_3rem_rgba(239,68,68,.08),inset_0_1px_rgba(255,255,255,.06)] motion-safe:animate-[reiterate-float_6s_ease-in-out_infinite]">R</div>
      </div>

      <div className="mx-auto max-w-[48rem] text-center">
        <p className="mb-2.5 text-[0.64rem] font-bold uppercase tracking-[0.26em] text-reiterate-orange/75">A workspace for better thinking</p>
        <h1 className="text-[clamp(2.2rem,5vw,4.25rem)] font-semibold leading-[0.98] tracking-[-0.055em]">What are you<br /><span className="bg-gradient-to-r from-reiterate-orange via-reiterate-amber to-reiterate-red bg-clip-text text-transparent">working on?</span></h1>
        <p className="mx-auto mt-[clamp(.9rem,2vh,1.35rem)] max-w-[37rem] text-[clamp(.85rem,1.3vw,.98rem)] leading-6 text-reiterate-muted/75">Bring an idea, question, or half-formed thought. Reiterate helps you push it further.</p>
      </div>

      <div className="mx-auto mt-[clamp(1.5rem,4vh,2.75rem)] grid w-full max-w-[50rem] grid-cols-1 gap-[clamp(.6rem,1vw,.8rem)] sm:grid-cols-3">
        {starters.map((starter, index) => (
          <button className="group min-h-[clamp(6.25rem,12vh,7.75rem)] rounded-[1.25rem] border border-white/[0.07] bg-white/[0.02] p-[clamp(.8rem,1.2vw,1rem)] text-left transition duration-200 hover:-translate-y-0.5 hover:border-reiterate-orange/20 hover:bg-reiterate-orange/[0.035] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-reiterate-orange/40" type="button" key={starter} onClick={() => onStarterSelect(starter)}>
            <span className="mb-4 flex size-7 items-center justify-center rounded-full border border-reiterate-orange/15 bg-reiterate-orange/7 text-[0.62rem] font-bold text-reiterate-orange/75">0{index + 1}</span>
            <span className="block text-[0.82rem] font-medium leading-5 text-reiterate-muted transition group-hover:text-reiterate-text">{starter}</span>
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
