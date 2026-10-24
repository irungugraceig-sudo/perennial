import { useEffect, useRef, useState } from "react";
import { sendChat, type ChatTurn } from "./api";
import { useScenario } from "./scenario";

const SUGGESTIONS = [
  "Use the 2015 blizzard date",
  "What if we double collection efficiency?",
  "Try the Lowell facility",
  "How does water become CO₂ saved?",
];

/** AI assistant wired to the shared scenario: it reads live results AND changes inputs. */
export default function AssistantChat() {
  const { scenario, set, result, selectedDC } = useScenario();
  const [open, setOpen] = useState(false);
  const [turns, setTurns] = useState<ChatTurn[]>([
    { role: "assistant", content: "Hi, I'm your Perennial guide. I can see your live numbers and change any input, ask me a what-if." },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [mode, setMode] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [turns, open]);

  async function ask(text: string) {
    if (!text.trim() || busy) return;
    const next = [...turns, { role: "user" as const, content: text }];
    setTurns(next);
    setInput("");
    setBusy(true);

    const context = {
      facility: scenario.facility,
      date: scenario.date,
      snowfall_m: scenario.snowfall_m,
      collection_efficiency: scenario.collection_efficiency,
      passive_loss_fraction: scenario.passive_loss_fraction,
      pue: selectedDC?.pue,
      wue_l_per_kwh: selectedDC?.wue_l_per_kwh,
      fresh_water_saved_gallons: result?.fresh_water_saved_gallons,
      co2_avoided_tonnes: result?.co2_avoided_tonnes,
      peak_month_offset_pct: result?.peak_month_offset_pct,
    };

    try {
      const r = await sendChat(text, context, next);
      setMode(r.mode);
      if (r.set_inputs && Object.keys(r.set_inputs).length) {
        set(r.set_inputs as never);  // apply AI's changes to the live scenario
      }
      setTurns((t) => [...t, { role: "assistant", content: r.reply }]);
    } catch {
      setTurns((t) => [...t, { role: "assistant", content: "Sorry, I couldn't reach the assistant." }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <button className={"chat-fab" + (open ? " open" : "")} onClick={() => setOpen((o) => !o)}>
        {open ? "✕" : "✦ Ask AI"}
      </button>
      {open && (
        <div className="chat-panel glass">
          <div className="chat-head">
            <span>Perennial Assistant {mode === "claude" && <i className="live-dot" title="Claude live" />}</span>
            <small>{mode === "claude" ? "Claude" : "guide"}</small>
          </div>
          <div className="chat-body">
            {turns.map((t, i) => <div key={i} className={"bubble " + t.role}>{t.content}</div>)}
            {busy && <div className="bubble assistant typing"><span /><span /><span /></div>}
            <div ref={endRef} />
          </div>
          <div className="chat-suggest">
            {SUGGESTIONS.map((s) => <button key={s} onClick={() => ask(s)}>{s}</button>)}
          </div>
          <form className="chat-input" onSubmit={(e) => { e.preventDefault(); ask(input); }}>
            <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask a what-if…" />
            <button type="submit" disabled={busy}>Send</button>
          </form>
        </div>
      )}
    </>
  );
}
