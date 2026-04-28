/* global React, PhoneFrame, ConfettiBurst, SkRing, Annot */
const { useState: useStateM, useEffect: useEffectM, useRef: useRefM } = React;

// ============================================================
// CLIENT INTAKE — VARIATION A: chat-bubble flow (Noom-style)
// ============================================================

// The full conversation script. mixes coach messages, multiple-choice, text input, household builder.
// "kind" controls the input UI rendered after the coach speaks.
const CHAT_SCRIPT_A = [
  { who: "coach", text: "Hi! I'm Avery, your prep coach 👋", delay: 600 },
  { who: "coach", text: "I'll get you ready for your call with Hutchins in about 5 minutes.", delay: 900 },
  { who: "coach", text: "First — what should I call you?", input: { kind: "text", placeholder: "First name", key: "first_name" } },
  // After name -> dynamic warm reply (handled in render)
  { who: "coach", text: "Lovely. Quick consents before we start — you in?", input: { kind: "consents", key: "consents" } },
  { who: "coach", text: "What state do you live in?", input: { kind: "select", key: "state", options: ["Texas", "California", "Florida", "New York", "Other"] } },
  { who: "coach", text: "How would you describe your current health coverage?", input: { kind: "choice", key: "coverage", options: ["I have a plan I like", "I have one but it's not great", "I don't have coverage right now", "Not sure"] } },
  { who: "coach", text: "Anyone else live with you that you file taxes with?", input: { kind: "household", key: "household" } },
  { who: "coach", text: "Does anyone in the household take prescriptions?", input: { kind: "yesno", key: "rx" } },
  { who: "coach", text: "Last bit — anything you'd like your agent to know?", input: { kind: "text", placeholder: "Optional · skip if nothing comes to mind", key: "note" } },
  { who: "coach", text: "All set! Generating your CoveraGap™ score now…", final: true },
];

function ChatTurn({ msg, onAnswer, value, name }) {
  if (msg.final) {
    return (
      <div className="row gap-2" style={{ padding: "8px 14px", alignItems: "flex-end", animation: "pop-in .35s both" }}>
        <div className="coach-avatar">A</div>
        <div className="sk-bubble coach">
          <span>All set, {name || "friend"}! 🎉 Generating your CoveraGap™ score…</span>
        </div>
      </div>
    );
  }

  const inp = msg.input;
  return (
    <div className="col gap-2" style={{ padding: "0 14px" }}>
      <div className="row gap-2" style={{ alignItems: "flex-end" }}>
        <div className="coach-avatar">A</div>
        <div className="sk-bubble coach pop-in">{msg.text.replace("Lovely.", name ? `Nice to meet you, ${name}.` : "Lovely.")}</div>
      </div>

      {inp && !value && (
        <div className="col gap-2" style={{ alignItems: "flex-end", marginTop: 4 }}>
          {inp.kind === "text" && (
            <div className="sk-bubble user" style={{ background: "#fff", padding: 6, width: "85%" }}>
              <input
                className="sk-input"
                placeholder={inp.placeholder}
                style={{ border: "none", boxShadow: "none", padding: "6px 8px", fontSize: 16 }}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && e.currentTarget.value.trim()) {
                    onAnswer(e.currentTarget.value.trim());
                  }
                }}
              />
              <div className="row between" style={{ marginTop: 4, paddingLeft: 8 }}>
                <span className="hand-ui muted" style={{ fontSize: 11 }}>press enter ↵</span>
                <button className="sk-btn primary" style={{ padding: "4px 12px", fontSize: 13 }}
                  onClick={(e) => {
                    const inputEl = e.currentTarget.parentElement.parentElement.querySelector("input");
                    if (inputEl.value.trim()) onAnswer(inputEl.value.trim());
                    else onAnswer("(skipped)");
                  }}>send →</button>
              </div>
            </div>
          )}
          {inp.kind === "consents" && (
            <div className="sk-bubble user pop-in" style={{ width: "90%", padding: "10px 12px" }}>
              <div className="col gap-2 hand-ui" style={{ fontSize: 13, color: "#1f2024" }}>
                {[
                  "Terms of service",
                  "Privacy policy",
                  "Contact about insurance",
                  "Share answers with partner agents (with consent)",
                ].map((c, i) => (
                  <label key={i} className="row gap-2"><input type="checkbox" defaultChecked /> <span>{c}</span></label>
                ))}
              </div>
              <button className="sk-btn primary" style={{ marginTop: 10, padding: "4px 14px", fontSize: 13 }} onClick={() => onAnswer("✓ all 4")}>I'm in →</button>
            </div>
          )}
          {inp.kind === "select" && (
            <div className="col gap-2" style={{ alignItems: "flex-end" }}>
              {inp.options.map(o => (
                <button key={o} className="sk-btn sk-tap" style={{ padding: "6px 14px" }} onClick={() => onAnswer(o)}>{o}</button>
              ))}
            </div>
          )}
          {inp.kind === "choice" && (
            <div className="col gap-2" style={{ alignItems: "flex-end", maxWidth: "90%" }}>
              {inp.options.map(o => (
                <button key={o} className="sk-btn sk-tap" style={{ padding: "8px 14px", textAlign: "right" }} onClick={() => onAnswer(o)}>{o}</button>
              ))}
            </div>
          )}
          {inp.kind === "yesno" && (
            <div className="row gap-2" style={{ alignSelf: "flex-end" }}>
              <button className="sk-btn sk-tap" onClick={() => onAnswer("No")}>No</button>
              <button className="sk-btn primary sk-tap" onClick={() => onAnswer("Yes")}>Yes</button>
            </div>
          )}
          {inp.kind === "household" && (
            <div className="sk-bubble user pop-in" style={{ width: "92%", padding: 12 }}>
              <div className="hand-ui" style={{ fontSize: 13, marginBottom: 6 }}>tap to add:</div>
              <div className="row gap-2" style={{ flexWrap: "wrap", marginBottom: 8 }}>
                <span className="sk-chip accent">+ Spouse</span>
                <span className="sk-chip accent">+ Child</span>
                <span className="sk-chip muted">+ Other</span>
              </div>
              <div className="hand-ui muted" style={{ fontSize: 12 }}>added: Carlos · Sofia · Diego</div>
              <button className="sk-btn primary" style={{ marginTop: 10, padding: "4px 14px", fontSize: 13 }} onClick={() => onAnswer("3 added")}>Looks good →</button>
            </div>
          )}
        </div>
      )}

      {value && (
        <div className="row" style={{ justifyContent: "flex-end", paddingRight: 6 }}>
          <div className="sk-bubble user pop-in">{value}</div>
        </div>
      )}
    </div>
  );
}

window.IntakeChatA = function IntakeChatA() {
  const [step, setStep] = useStateM(0);
  const [answers, setAnswers] = useStateM({});
  const [typing, setTyping] = useStateM(true);
  const scrollRef = useRefM(null);

  // Reveal each turn one at a time, with typing indicator
  useEffectM(() => {
    setTyping(true);
    const t = setTimeout(() => setTyping(false), 700);
    return () => clearTimeout(t);
  }, [step]);

  useEffectM(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [step, typing, answers]);

  const visible = CHAT_SCRIPT_A.slice(0, step + 1);
  const current = CHAT_SCRIPT_A[step];

  const handleAnswer = (val) => {
    const k = current?.input?.key;
    if (k) setAnswers(a => ({ ...a, [k]: val }));
    if (step < CHAT_SCRIPT_A.length - 1) setStep(s => s + 1);
  };

  // Auto-advance for messages with no input (back-to-back coach lines)
  useEffectM(() => {
    if (current && !current.input && !current.final && step < CHAT_SCRIPT_A.length - 1) {
      const t = setTimeout(() => setStep(s => s + 1), current.delay || 1200);
      return () => clearTimeout(t);
    }
  }, [step]);

  const total = CHAT_SCRIPT_A.length - 1;
  const pct = Math.min(100, Math.round((step / total) * 100));

  const isFinal = current?.final;

  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      {/* Header */}
      <div className="row between" style={{ padding: "6px 18px 10px", borderBottom: "1.5px dashed #c8c5b8" }}>
        <div className="row gap-2">
          <div className="coach-avatar" style={{ width: 26, height: 26, fontSize: 14 }}>A</div>
          <div className="col" style={{ lineHeight: 1.05 }}>
            <span className="hand-title" style={{ fontSize: 16 }}>Avery</span>
            <span className="hand-ui muted" style={{ fontSize: 11 }}>your prep coach</span>
          </div>
        </div>
        <span className="hand-ui muted" style={{ fontSize: 12 }}>{pct}% done</span>
      </div>
      <div style={{ padding: "8px 18px 4px" }}>
        <div className="sk-progress"><div className="fill" style={{ width: `${pct}%` }} /></div>
      </div>

      {/* Scroll area */}
      <div ref={scrollRef} style={{ flex: 1, overflowY: "auto", padding: "12px 0 18px", display: "flex", flexDirection: "column", gap: 10 }}>
        {visible.map((m, i) => (
          <ChatTurn
            key={i}
            msg={m}
            value={i < step ? answers[m.input?.key] : null}
            name={answers.first_name}
            onAnswer={handleAnswer}
          />
        ))}
        {typing && step > 0 && !isFinal && (
          <div className="row gap-2" style={{ padding: "0 14px", alignItems: "flex-end" }}>
            <div className="coach-avatar">A</div>
            <div className="sk-bubble coach" style={{ padding: 0 }}>
              <div className="typing"><span /><span /><span /></div>
            </div>
          </div>
        )}
        {isFinal && (
          <div style={{ padding: "0 14px" }}>
            <button className="sk-btn primary full lg" style={{ marginTop: 12 }}>See my CoveraGap™ score →</button>
          </div>
        )}
      </div>
    </div>
  );
};

// ============================================================
// CLIENT INTAKE — VARIATION B: card-swipe wizard
// ============================================================

const CARDS_B = [
  { kind: "welcome" },
  { kind: "name" },
  { kind: "consents" },
  { kind: "coverage" },
  { kind: "household" },
  { kind: "rx" },
  { kind: "celebrate" },
];

window.IntakeChatB = function IntakeChatB() {
  const [step, setStep] = useStateM(0);
  const [name, setName] = useStateM("");
  const [coverage, setCoverage] = useStateM(null);
  const card = CARDS_B[step];
  const total = CARDS_B.length - 1;
  const pct = Math.round((step / total) * 100);

  const next = () => setStep(s => Math.min(total, s + 1));
  const back = () => setStep(s => Math.max(0, s - 1));

  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      {/* Compact top bar with dots */}
      <div className="row between" style={{ padding: "4px 18px 10px", alignItems: "center" }}>
        <span className="hand-ui muted" style={{ fontSize: 13, cursor: "pointer" }} onClick={back}>{step > 0 ? "← back" : ""}</span>
        <div className="sk-dots">
          {CARDS_B.map((_, i) => (
            <span key={i} className={`dot ${i < step ? "done" : i === step ? "cur" : ""}`} />
          ))}
        </div>
        <span className="hand-ui muted" style={{ fontSize: 13 }}>{step + 1}/{CARDS_B.length}</span>
      </div>

      {/* Card stage */}
      <div style={{ flex: 1, position: "relative" }}>
        <div className="swipe-stack" style={{ position: "absolute", inset: "8px 14px" }}>
          <div key={step} className="sk-box sk-fill-paper swipe-card pop-in" style={{ position: "absolute", inset: 0 }}>
            {card.kind === "welcome" && (
              <div className="col gap-3" style={{ height: "100%", justifyContent: "center", textAlign: "center" }}>
                <div style={{ fontSize: 56 }}>👋</div>
                <div className="hand-title" style={{ fontSize: 32, lineHeight: 1.1 }}>Let's prep for your call</div>
                <div className="hand-ui muted" style={{ fontSize: 15 }}>About 5 minutes. "Not sure" is fine.</div>
                <button className="sk-btn primary lg" style={{ alignSelf: "center", marginTop: 8 }} onClick={next}>Start →</button>
              </div>
            )}
            {card.kind === "name" && (
              <div className="col gap-3" style={{ justifyContent: "center", height: "100%" }}>
                <div className="hand-title" style={{ fontSize: 28, lineHeight: 1.1 }}>What should we call you?</div>
                <input className="sk-input" placeholder="First name" value={name} onChange={e => setName(e.target.value)} style={{ fontSize: 22, padding: "10px 14px" }} />
                <button className="sk-btn primary full lg" disabled={!name} onClick={next}>Continue</button>
              </div>
            )}
            {card.kind === "consents" && (
              <div className="col gap-3" style={{ justifyContent: "center", height: "100%" }}>
                <div className="hand-title" style={{ fontSize: 26, lineHeight: 1.1 }}>Quick consents</div>
                <div className="col gap-2 hand-ui" style={{ fontSize: 14 }}>
                  {["Terms of service", "Privacy policy", "Contact me about insurance", "Share with partner agents"].map((c, i) => (
                    <label key={i} className="row gap-2 sk-box sk-fill-2" style={{ padding: "8px 12px" }}>
                      <input type="checkbox" defaultChecked /> <span>{c}</span>
                    </label>
                  ))}
                </div>
                <button className="sk-btn primary full lg" onClick={next}>I agree →</button>
              </div>
            )}
            {card.kind === "coverage" && (
              <div className="col gap-3" style={{ justifyContent: "center", height: "100%" }}>
                <div className="hand-title" style={{ fontSize: 24, lineHeight: 1.1 }}>How's your current health coverage?</div>
                <div className="hand-ui muted" style={{ fontSize: 13 }}>Pick whichever feels closest.</div>
                <div className="col gap-2">
                  {[
                    ["love", "I have a plan I like", "🥰"],
                    ["meh", "I have one but it's not great", "😐"],
                    ["none", "I don't have coverage right now", "😬"],
                    ["unsure", "Not sure", "🤔"],
                  ].map(([k, label, emoji]) => (
                    <button key={k} className={`sk-btn sk-tap ${coverage === k ? "primary" : ""}`}
                            style={{ justifyContent: "flex-start", padding: "10px 14px", fontSize: 16 }}
                            onClick={() => { setCoverage(k); setTimeout(next, 250); }}>
                      <span style={{ marginRight: 10, fontSize: 22 }}>{emoji}</span>{label}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {card.kind === "household" && (
              <div className="col gap-3" style={{ justifyContent: "center", height: "100%" }}>
                <div className="hand-title" style={{ fontSize: 26, lineHeight: 1.1 }}>Who's in your household?</div>
                <div className="hand-ui muted" style={{ fontSize: 13 }}>People you file taxes with.</div>
                <div className="col gap-2">
                  {[
                    ["MG", "Maria · You", "primary", true],
                    ["CG", "Carlos · Spouse · 41", "spouse", true],
                    ["SF", "Sofia · Child · 12", "dependent", true],
                    ["DG", "Diego · Child · 9", "dependent", true],
                  ].map(([init, label, role, on], i) => (
                    <div key={i} className="sk-box sk-fill-2 row gap-3" style={{ padding: "8px 12px", alignItems: "center" }}>
                      <span style={{ width: 30, height: 30, borderRadius: 50, background: "#fde7d6", border: "1.6px solid #1f2024", display: "inline-flex", alignItems: "center", justifyContent: "center", fontFamily: "'Caveat'", fontWeight: 700 }}>{init}</span>
                      <span className="hand-ui grow" style={{ fontSize: 14 }}>{label}</span>
                      <span className="sk-chip muted">{role}</span>
                    </div>
                  ))}
                </div>
                <div className="row gap-2" style={{ justifyContent: "center" }}>
                  <button className="sk-btn">+ Add spouse</button>
                  <button className="sk-btn">+ Add child</button>
                </div>
                <button className="sk-btn primary full lg" onClick={next}>Looks good →</button>
              </div>
            )}
            {card.kind === "rx" && (
              <div className="col gap-3" style={{ justifyContent: "center", height: "100%" }}>
                <div className="hand-title" style={{ fontSize: 26, lineHeight: 1.1 }}>Any prescriptions?</div>
                <div className="hand-ui muted" style={{ fontSize: 13 }}>Your agent will check formulary coverage.</div>
                <div className="row gap-2">
                  <button className="sk-btn full lg" onClick={next}>No</button>
                  <button className="sk-btn primary full lg" onClick={next}>Yes</button>
                </div>
                <div className="hand-ui muted" style={{ fontSize: 12, textAlign: "center", marginTop: 6 }}>You can add them on the next screen.</div>
              </div>
            )}
            {card.kind === "celebrate" && (
              <div className="col gap-3" style={{ justifyContent: "center", height: "100%", textAlign: "center", position: "relative" }}>
                <ConfettiBurst run count={20} />
                <div style={{ fontSize: 60 }}>🎉</div>
                <div className="hand-title" style={{ fontSize: 28, lineHeight: 1.1 }}>That's it, {name || "friend"}!</div>
                <div className="hand-ui muted" style={{ fontSize: 14 }}>Your CoveraGap™ score is being prepared.</div>
                <button className="sk-btn primary lg" style={{ alignSelf: "center", marginTop: 8 }}>See my score →</button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// ============================================================
// COVERAGE GAP SCORE — VARIATION A: animated ring + celebrations
// ============================================================

window.GapScoreA = function GapScoreA({ value = 64 }) {
  const [showConfetti, setShowConfetti] = useStateM(true);
  useEffectM(() => {
    const t = setTimeout(() => setShowConfetti(false), 2000);
    return () => clearTimeout(t);
  }, []);
  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column", padding: "6px 18px 14px", overflowY: "auto" }}>
      <ConfettiBurst run={showConfetti} />
      <div className="hand-ui muted" style={{ fontSize: 13 }}>CoveraGap™ Score</div>
      <div className="hand-title" style={{ fontSize: 22, lineHeight: 1.1, marginBottom: 4 }}>You're doing okay, Maria.</div>
      <div className="hand-ui muted" style={{ fontSize: 13, marginBottom: 6 }}>4 areas to discuss with your agent.</div>

      <div style={{ display: "flex", justifyContent: "center", marginTop: 6, position: "relative" }}>
        <div style={{ position: "relative", width: 200, height: 200 }}>
          <SkRing value={value} size={200} stroke={14} />
          <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
            <div className="hand-title" style={{ fontSize: 60, lineHeight: 1 }}>{value}</div>
            <div className="hand-ui muted" style={{ fontSize: 13 }}>out of 100</div>
            <span className="sk-chip warn" style={{ marginTop: 6 }}>moderate gap</span>
          </div>
        </div>
      </div>

      <div className="hand-ui muted" style={{ fontSize: 12, textAlign: "center", margin: "8px 0 14px" }}>
        Healthy range 60–85 · Educational only
      </div>

      <div className="hand-title" style={{ fontSize: 18, marginBottom: 8 }}>Module breakdown</div>
      <div className="col gap-2">
        {[
          ["Health", 72, "Mostly covered — check spouse", "good"],
          ["Life",   40, "No policy with kids at home",  "bad"],
          ["Auto",   65, "Liability is at TX minimum",   "warn"],
        ].map(([m, sc, note, t], i) => (
          <div key={i} className="sk-box sk-fill-paper row gap-3" style={{ padding: "10px 12px", alignItems: "center" }}>
            <div style={{ position: "relative", width: 44, height: 44 }}>
              <SkRing value={sc} size={44} stroke={5} animate={false} color={t === "bad" ? "#b85544" : t === "warn" ? "#d97a3c" : "#4a8c5c"} />
              <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'Caveat'", fontWeight: 700, fontSize: 14 }}>{sc}</div>
            </div>
            <div className="col grow" style={{ lineHeight: 1.15 }}>
              <span className="hand-title" style={{ fontSize: 16 }}>{m}</span>
              <span className="hand-ui muted" style={{ fontSize: 12 }}>{note}</span>
            </div>
            <span className="hand-ui faint">›</span>
          </div>
        ))}
      </div>

      <button className="sk-btn primary full lg" style={{ marginTop: 14 }}>Schedule call with agent</button>
      <div className="hand-ui muted" style={{ fontSize: 11, textAlign: "center", marginTop: 8, lineHeight: 1.4 }}>
        Educational estimate. Not a coverage determination, recommendation, or quote.
      </div>
    </div>
  );
};

// ============================================================
// COVERAGE GAP SCORE — VARIATION B: stacked module bars (no ring)
// ============================================================

window.GapScoreB = function GapScoreB() {
  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column", padding: "6px 18px 14px", overflowY: "auto" }}>
      <div className="hand-ui muted" style={{ fontSize: 13 }}>Your Coverage Snapshot</div>
      <div className="hand-title" style={{ fontSize: 26, lineHeight: 1.1, marginTop: 2 }}>3 wins · 2 gaps to talk about</div>

      <div className="sk-box sk-fill-accent" style={{ padding: 12, margin: "12px 0" }}>
        <div className="row between" style={{ alignItems: "baseline" }}>
          <span className="hand-ui" style={{ fontSize: 14 }}>Overall Coverage Score</span>
          <span className="hand-title" style={{ fontSize: 30 }}>64<span style={{ fontSize: 14, color: "#4a4d55" }}> /100</span></span>
        </div>
        <div className="sk-progress" style={{ marginTop: 8 }}><div className="fill" style={{ width: "64%" }} /></div>
        <div className="hand-ui muted" style={{ fontSize: 11, marginTop: 4 }}>Gap Risk: 36 pts</div>
      </div>

      <div className="hand-title" style={{ fontSize: 18, marginBottom: 8 }}>Module breakdown</div>
      <div className="col gap-3">
        {[
          { m: "Health", sc: 72, tone: "good", items: ["Strong primary plan", "Spouse not enrolled — discuss"] },
          { m: "Life",   sc: 40, tone: "bad",  items: ["No life policy", "2 dependents under 19"] },
          { m: "Auto",   sc: 65, tone: "warn", items: ["At state minimum liability"] },
        ].map((r, i) => (
          <div key={i} className="sk-box sk-fill-paper" style={{ padding: 12 }}>
            <div className="row between">
              <span className="hand-title" style={{ fontSize: 17 }}>{r.m}</span>
              <span className="hand-title" style={{ fontSize: 18 }}>{r.sc}/100</span>
            </div>
            <div style={{ height: 12, border: "1.8px solid #1f2024", borderRadius: 6, background: "#fafaf6", marginTop: 6, overflow: "hidden" }}>
              <div style={{ height: "100%", width: `${r.sc}%`, background: r.tone === "bad" ? "#b85544" : r.tone === "warn" ? "#d97a3c" : "#4a8c5c" }} />
            </div>
            <ul className="hand-ui" style={{ fontSize: 13, paddingLeft: 18, marginTop: 8, lineHeight: 1.5 }}>
              {r.items.map((it, j) => (<li key={j}>{it}</li>))}
            </ul>
          </div>
        ))}
      </div>

      <button className="sk-btn primary full lg" style={{ marginTop: 14 }}>Schedule call with agent</button>
      <div className="hand-ui muted" style={{ fontSize: 11, textAlign: "center", marginTop: 8 }}>
        Educational estimate. Not a quote.
      </div>
    </div>
  );
};

Object.assign(window, {
  IntakeChatA: window.IntakeChatA,
  IntakeChatB: window.IntakeChatB,
  GapScoreA: window.GapScoreA,
  GapScoreB: window.GapScoreB,
});
