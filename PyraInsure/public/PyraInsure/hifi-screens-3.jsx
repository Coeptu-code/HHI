/* global React, Phone, Icon, Logo, Ring, Confetti */
const { useState: useSc, useEffect: useEc, useRef: useRc } = React;

// ============================================================
// INTAKE CHAT A — full Noom-style coach flow, interactive
// ============================================================

// Conversation script
const SCRIPT = [
  { from: "coach", text: "Hi Maria! 👋 I'm Avery, your prep coach for Thursday's call with Jane." },
  { from: "coach", text: "I'll ask a handful of questions — should take about 4 minutes. Sound good?" },
  { from: "user-choice", q: "ready", choices: [["Let's do it ✨", "lets-go"], ["Maybe later", "later"]] },
  { from: "coach", text: "Amazing. First, the easy stuff — who's in your household?" },
  { from: "user-input", q: "household", placeholder: "How many people?", kind: "number", suffix: "people" },
  { from: "coach", text: "A family of 4 — beautiful. And the kids' ages?" },
  { from: "user-input", q: "ages", placeholder: "e.g. 8 and 4", kind: "text" },
  { from: "coach", text: "Got it. Quick check on coverage — what do you currently have?" },
  { from: "user-multi", q: "coverage", choices: [
    { v: "med", l: "Medical", i: "shield" },
    { v: "den", l: "Dental", i: "smile" },
    { v: "vis", l: "Vision", i: "eye" },
    { v: "life", l: "Life insurance", i: "heart" },
    { v: "auto", l: "Auto", i: "car" },
    { v: "home", l: "Home", i: "house" },
  ]},
  { from: "coach", text: "Thanks for sharing 🙏 One more — anything big change in the last year?" },
  { from: "user-multi", q: "events", choices: [
    { v: "marriage", l: "Got married" },
    { v: "baby", l: "New baby" },
    { v: "moved", l: "Moved house" },
    { v: "job", l: "New job" },
    { v: "none", l: "Nothing major" },
  ]},
  { from: "coach", text: "Perfect — that's everything I need. Let's see your coverage picture..." },
  { from: "done" },
];

window.HiIntakeA = function HiIntakeA() {
  const [step, setStep] = useSc(0);
  const [answers, setAnswers] = useSc({});
  const [typing, setTyping] = useSc(false);
  const scrollRef = useRc(null);

  // auto-advance through coach bubbles with typing
  useEc(() => {
    const cur = SCRIPT[step];
    if (!cur) return;
    if (cur.from === "coach") {
      setTyping(true);
      const t = setTimeout(() => { setTyping(false); setStep(s => s + 1); }, 1000);
      return () => clearTimeout(t);
    }
  }, [step]);

  // auto-scroll
  useEc(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [step, typing]);

  const visible = SCRIPT.slice(0, step);
  const cur = SCRIPT[step];
  const totalQuestions = SCRIPT.filter(s => s.from && s.from.startsWith("user-")).length;
  const answered = Object.keys(answers).length;
  const progress = Math.min(100, (answered / totalQuestions) * 100);

  const answer = (q, v) => { setAnswers(a => ({ ...a, [q]: v })); setStep(s => s + 1); };

  return (
    <Phone>
      {/* Header */}
      <div style={{ paddingTop: 50, paddingBottom: 12 }}>
        <div className="row between" style={{ padding: "0 22px 12px" }}>
          <div className="row gap-3">
            <span className="avatar md bg-mg" style={{ position: "relative" }}>
              A
              <span style={{ position: "absolute", bottom: -2, right: -2, width: 12, height: 12, borderRadius: "50%", background: "var(--good)", border: "2px solid var(--bg)" }} />
            </span>
            <div className="col" style={{ lineHeight: 1.2 }}>
              <span style={{ fontSize: 14, fontWeight: 700 }}>Avery</span>
              <span style={{ fontSize: 11, color: "var(--ink-3)" }}>Your prep coach · PyraInsure</span>
            </div>
          </div>
          <button className="btn ghost icon-only" style={{ width: 32, height: 32 }}><Icon name="info" size={16} color="var(--ink-3)"/></button>
        </div>
        <div style={{ padding: "0 22px" }}>
          <div className="progress" style={{ height: 5 }}>
            <div className="fill" style={{ width: `${progress}%` }} />
          </div>
          <div style={{ fontSize: 10, color: "var(--ink-4)", marginTop: 6, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em" }}>
            {answered}/{totalQuestions} answered · ~{Math.max(1, 4 - Math.round(answered * 0.7))}m left
          </div>
        </div>
      </div>

      {/* Chat scroll */}
      <div ref={scrollRef} style={{ flex: 1, overflow: "auto", padding: "8px 18px 16px", height: 540, background: "var(--bg)" }}>
        <div className="col gap-2" style={{ paddingBottom: 12 }}>
          {visible.map((m, i) => {
            if (m.from === "coach") return <div key={i} className="bubble coach fade-up">{m.text}</div>;
            if (m.from === "user-choice" && answers[m.q]) {
              const lbl = m.choices.find(c => c[1] === answers[m.q])?.[0] || answers[m.q];
              return <div key={i} className="bubble user brand fade-up">{lbl}</div>;
            }
            if (m.from === "user-input" && answers[m.q] != null) {
              return <div key={i} className="bubble user brand fade-up">{answers[m.q]}{m.suffix ? ` ${m.suffix}` : ""}</div>;
            }
            if (m.from === "user-multi" && answers[m.q]) {
              const labels = m.choices.filter(c => answers[m.q].includes(c.v)).map(c => c.l).join(", ") || "None";
              return <div key={i} className="bubble user brand fade-up">{labels}</div>;
            }
            return null;
          })}
          {typing && (
            <div className="bubble coach fade-up" style={{ padding: "8px 14px" }}>
              <div className="typing-dots"><span/><span/><span/></div>
            </div>
          )}
        </div>
      </div>

      {/* Input area */}
      <div style={{ padding: "10px 18px 28px", borderTop: "1px solid var(--line)", background: "var(--surface)", minHeight: 110 }}>
        {!cur || cur.from === "coach" ? (
          <div style={{ fontSize: 12, color: "var(--ink-4)", textAlign: "center", padding: 14 }}>Avery is typing…</div>
        ) : cur.from === "done" ? (
          <button className="btn brand full lg" onClick={() => window.dispatchEvent(new CustomEvent("intake-done"))}>See my coverage <Icon name="arrow" size={16}/></button>
        ) : cur.from === "user-choice" ? (
          <div className="col gap-2">
            {cur.choices.map(([label, v]) => (
              <button key={v} className="btn outline full" style={{ justifyContent: "flex-start", padding: "12px 16px", fontSize: 14, fontWeight: 500 }} onClick={() => answer(cur.q, v)}>
                <span>{label}</span>
              </button>
            ))}
          </div>
        ) : cur.from === "user-input" ? (
          <InputRow cur={cur} onSubmit={(v) => answer(cur.q, v)} />
        ) : cur.from === "user-multi" ? (
          <MultiRow cur={cur} onSubmit={(arr) => answer(cur.q, arr)} />
        ) : null}
      </div>
    </Phone>
  );
};

function InputRow({ cur, onSubmit }) {
  const [v, setV] = useSc("");
  return (
    <form className="row gap-2" onSubmit={(e) => { e.preventDefault(); if (v) onSubmit(v); }}>
      <input className="input" autoFocus type={cur.kind === "number" ? "number" : "text"} placeholder={cur.placeholder} value={v} onChange={(e) => setV(e.target.value)} style={{ borderRadius: 999 }} />
      <button type="submit" className="btn brand icon-only" style={{ width: 44, height: 44 }} disabled={!v}><Icon name="send" size={16}/></button>
    </form>
  );
}

function MultiRow({ cur, onSubmit }) {
  const [sel, setSel] = useSc(new Set());
  const toggle = (v) => { const n = new Set(sel); n.has(v) ? n.delete(v) : n.add(v); setSel(n); };
  return (
    <div className="col gap-2">
      <div style={{ display: "grid", gridTemplateColumns: cur.choices.length > 4 ? "1fr 1fr" : "1fr", gap: 6, maxHeight: 180, overflow: "auto" }}>
        {cur.choices.map(c => {
          const on = sel.has(c.v);
          return (
            <button key={c.v} type="button" className="row gap-2 tap" onClick={() => toggle(c.v)} style={{
              padding: "9px 12px", border: `1.5px solid ${on ? "var(--orange)" : "var(--line-2)"}`,
              borderRadius: 999, background: on ? "var(--orange-tint)" : "var(--surface)",
              fontSize: 13, fontWeight: 500, color: on ? "var(--orange-2)" : "var(--ink-2)",
              justifyContent: "flex-start", cursor: "pointer",
            }}>
              {c.i && <Icon name={c.i} size={13} />}
              <span>{c.l}</span>
              {on && <Icon name="check" size={13} color="var(--orange-2)"/>}
            </button>
          );
        })}
      </div>
      <button className="btn brand full" onClick={() => onSubmit(Array.from(sel))} disabled={!sel.size}>Continue ({sel.size}) <Icon name="arrow" size={14}/></button>
    </div>
  );
}

// ============================================================
// GAP SCORE A — animated ring + module breakdown + confetti
// ============================================================
window.HiGapA = function HiGapA() {
  const [reveal, setReveal] = useSc(false);
  const [score, setScore] = useSc(0);
  const target = 64;

  useEc(() => {
    const t1 = setTimeout(() => setReveal(true), 300);
    const t2 = setTimeout(() => {
      // animate count
      let s = 0;
      const id = setInterval(() => {
        s += 2;
        if (s >= target) { s = target; clearInterval(id); }
        setScore(s);
      }, 28);
    }, 600);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, []);

  return (
    <Phone>
      {reveal && score === target && <Confetti run={true} count={36} />}

      <div style={{ paddingTop: 50, paddingBottom: 8 }}>
        <div className="row between" style={{ padding: "0 22px" }}>
          <button className="btn ghost icon-only" style={{ width: 32, height: 32 }}><Icon name="arrowL" size={16} color="var(--ink-2)"/></button>
          <Logo size={14} mark={false} />
          <button className="btn ghost icon-only" style={{ width: 32, height: 32 }}><Icon name="info" size={16} color="var(--ink-3)"/></button>
        </div>
      </div>

      <div style={{ height: "calc(100% - 70px)", overflow: "auto", padding: "0 22px 28px" }}>
        {/* Hero */}
        <div className="col center fade-up" style={{ paddingTop: 18, textAlign: "center" }}>
          <span className="chip teal dot">Your coverage snapshot</span>
          <h1 className="serif" style={{ fontSize: 26, marginTop: 14, lineHeight: 1.2, maxWidth: 280 }}>Nice work, Maria.</h1>
          <p style={{ fontSize: 14, color: "var(--ink-3)", marginTop: 6, maxWidth: 280, lineHeight: 1.5 }}>
            Here's where your family stands today.
          </p>
        </div>

        {/* Ring */}
        <div className="col center" style={{ marginTop: 22, position: "relative" }}>
          <div className="score-aurora">
            <div className="blob blob-1" />
            <div className="blob blob-2" />
            <div className="blob blob-3" />
            <div className="blob blob-4" />
          </div>
          <div className="ring-wrap" style={{ position: "relative", zIndex: 2 }}>
            <Ring value={score} size={220} stroke={16} animate={false} />
            <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", lineHeight: 1 }}>
              <span style={{ fontSize: 11, color: "var(--ink-4)", textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 700 }}>Score</span>
              <span className="serif" style={{ fontSize: 64, marginTop: 4, color: "#000" }}>{score}</span>
              <span className="chip warn" style={{ marginTop: 8 }}>Moderate gap</span>
            </div>
          </div>
        </div>

        <p style={{ fontSize: 13, color: "var(--ink-3)", textAlign: "center", marginTop: 16, maxWidth: 300, marginLeft: "auto", marginRight: "auto", lineHeight: 1.5 }}>
          You're doing better than <b style={{ color: "var(--ink)" }}>61%</b> of families like yours. Two opportunities stand out.
        </p>

        {/* Module breakdown */}
        <div className="col gap-3" style={{ marginTop: 24 }}>
          {[
            { name: "Medical", pct: 92, tone: "good", note: "Strong PPO · all 4 covered" },
            { name: "Dental",  pct: 88, tone: "good", note: "Family covered" },
            { name: "Vision",  pct: 22, tone: "warn", note: "Gap — kids not covered" },
            { name: "Life",    pct: 38, tone: "bad",  note: "Carlos covered, you aren't" },
            { name: "Auto + Home", pct: 50, tone: "warn", note: "Not on file" },
          ].map((m, i) => {
            const c = m.tone === "good" ? "var(--good)" : m.tone === "warn" ? "var(--warn)" : "var(--bad)";
            return (
              <div key={i} className="card card-pad-sm fade-up" style={{ animationDelay: `${0.1 * i + 0.3}s` }}>
                <div className="row between" style={{ marginBottom: 8 }}>
                  <span style={{ fontSize: 14, fontWeight: 600 }}>{m.name}</span>
                  <span className={`chip ${m.tone}`} style={{ fontSize: 11 }}>{m.pct}%</span>
                </div>
                <div className="sev-bar"><div style={{ width: reveal ? `${m.pct}%` : 0, background: c }} /></div>
                <div style={{ fontSize: 12, color: "var(--ink-3)", marginTop: 8 }}>{m.note}</div>
              </div>
            );
          })}
        </div>

        {/* CTA */}
        <div className="card card-pad" style={{ marginTop: 22, background: "linear-gradient(155deg, #fdf1e8, #ecf6f4)", textAlign: "center" }}>
          <Icon name="sparkles" size={22} color="var(--orange-2)" />
          <h3 className="serif" style={{ fontSize: 18, marginTop: 8 }}>Ready for Thursday?</h3>
          <p style={{ fontSize: 13, color: "var(--ink-3)", marginTop: 4, lineHeight: 1.5 }}>
            Jane will walk you through your two opportunities. You'll come out ahead.
          </p>
          <button className="btn brand full lg" style={{ marginTop: 14 }}>See Jane's call notes <Icon name="arrow" size={14}/></button>
          <button className="btn ghost full sm" style={{ marginTop: 6 }}>Send myself a copy</button>
        </div>
      </div>
    </Phone>
  );
};

Object.assign(window, { HiIntakeA: window.HiIntakeA, HiGapA: window.HiGapA });
