/* global React, Sidebar, TopBar, Icon, Logo */
const { useState: useSb, useEffect: useEb } = React;

// ============================================================
// CREATE INTAKE LINK A — guided 3-step wizard with live preview
// ============================================================
window.HiCreateA = function HiCreateA() {
  const [step, setStep] = useSb(2);
  return (
    <div className="row" style={{ height: "100%" }}>
      <Sidebar active="links" />
      <main style={{ flex: 1, overflow: "auto", background: "var(--bg)" }}>
        <TopBar
          title="New intake link"
          subtitle="Send a personalized intake to your client in under a minute."
          actions={<><button className="btn ghost">Cancel</button><button className="btn outline">Save draft</button></>}
        />
        <div style={{ padding: "24px 32px", display: "grid", gridTemplateColumns: "1fr 420px", gap: 24 }}>
          <section className="card card-pad-lg">
            {/* Stepper */}
            <div className="row gap-4" style={{ marginBottom: 28 }}>
              {["Client", "Customize", "Send"].map((s, i) => {
                const n = i + 1;
                const state = n < step ? "done" : n === step ? "cur" : "todo";
                return (
                  <div key={s} className="row gap-3" style={{ flex: 1 }}>
                    <span style={{
                      width: 32, height: 32, borderRadius: "50%",
                      display: "inline-flex", alignItems: "center", justifyContent: "center",
                      fontWeight: 700, fontSize: 13,
                      background: state === "cur" ? "var(--orange)" : state === "done" ? "var(--ink)" : "var(--bg-2)",
                      color: state === "todo" ? "var(--ink-3)" : "#fff",
                      border: state === "todo" ? "1px solid var(--line-2)" : "none",
                    }}>{state === "done" ? <Icon name="check" size={14} /> : n}</span>
                    <div className="col" style={{ lineHeight: 1.2 }}>
                      <span style={{ fontSize: 11, color: "var(--ink-4)", textTransform: "uppercase", letterSpacing: "0.06em" }}>Step {n}</span>
                      <span style={{ fontSize: 14, fontWeight: 600, color: state === "todo" ? "var(--ink-3)" : "var(--ink)" }}>{s}</span>
                    </div>
                    {i < 2 && <div className="divider" style={{ flex: 1, marginLeft: 8 }} />}
                  </div>
                );
              })}
            </div>

            {/* Step 2: Customize */}
            <h2 className="serif" style={{ fontSize: 22 }}>Customize for Maria</h2>
            <p style={{ color: "var(--ink-3)", fontSize: 14, marginTop: 4 }}>Pick what to ask. We've pre-selected based on her profile.</p>

            <div className="col gap-4" style={{ marginTop: 22 }}>
              <label className="field"><span>Greeting from you</span>
                <input className="input" defaultValue="Hi Maria — taking 5 mins now will save us 20 on Thursday's call. — Jane" />
              </label>

              <div className="col gap-2">
                <span style={{ fontSize: 13, color: "var(--ink-2)", fontWeight: 500 }}>Modules to include</span>
                <div className="col gap-2">
                  {[
                    ["Household & dependents", true, "users"],
                    ["Current coverage (medical, dental, vision)", true, "shield"],
                    ["Prescriptions & ongoing care", true, "pill"],
                    ["Major life events (last 12 mo.)", true, "sparkles"],
                    ["Auto & home (referral)", false, "car"],
                    ["Retirement planning (referral)", false, "umbrella"],
                  ].map(([label, on, ico], i) => (
                    <label key={i} className="row between hover-row" style={{ padding: "10px 12px", border: "1px solid var(--line)", borderRadius: 12, background: on ? "var(--orange-tint)" : "var(--surface)" }}>
                      <span className="row gap-3">
                        <Icon name={ico} size={16} color={on ? "var(--orange-2)" : "var(--ink-3)"} />
                        <span style={{ fontSize: 14, fontWeight: 500, color: on ? "var(--ink)" : "var(--ink-2)" }}>{label}</span>
                      </span>
                      <input type="checkbox" defaultChecked={on} />
                    </label>
                  ))}
                </div>
              </div>

              <div className="row gap-4">
                <label className="field" style={{ flex: 1 }}><span>Expires</span>
                  <select className="select" defaultValue="7"><option value="3">3 days</option><option value="7">7 days</option><option value="14">14 days</option></select>
                </label>
                <label className="field" style={{ flex: 1 }}><span>Reminder</span>
                  <select className="select" defaultValue="48h"><option>None</option><option value="24h">After 24 hours</option><option value="48h">After 48 hours</option></select>
                </label>
              </div>
            </div>

            <div className="row between" style={{ marginTop: 28, paddingTop: 18, borderTop: "1px solid var(--line)" }}>
              <button className="btn ghost" onClick={() => setStep(Math.max(1, step - 1))}><Icon name="arrowL" size={14} /> Back</button>
              <div className="row gap-3">
                <span style={{ fontSize: 12, color: "var(--ink-3)" }}>Estimated time for client: <b style={{ color: "var(--ink)" }}>4m 30s</b></span>
                <button className="btn brand" onClick={() => setStep(Math.min(3, step + 1))}>Continue <Icon name="arrow" size={14} /></button>
              </div>
            </div>
          </section>

          {/* Live preview */}
          <aside className="col gap-3" style={{ position: "sticky", top: 0, alignSelf: "start" }}>
            <div className="row between">
              <span style={{ fontSize: 12, color: "var(--ink-4)", textTransform: "uppercase", letterSpacing: "0.06em", fontWeight: 600 }}>Live preview</span>
              <span className="chip outline"><Icon name="phone" size={11} /> iPhone</span>
            </div>
            <div className="card" style={{ padding: 0, overflow: "hidden", background: "linear-gradient(160deg, #fdf1e8, #ecf6f4)" }}>
              <div style={{ padding: 22 }}>
                <div className="row gap-3" style={{ marginBottom: 14 }}>
                  <span className="avatar md bg-mg">A</span>
                  <div className="col" style={{ lineHeight: 1.2 }}>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>Avery from PyraInsure</span>
                    <span style={{ fontSize: 11, color: "var(--ink-3)" }}>Texting · just now</span>
                  </div>
                </div>
                <div className="col gap-2">
                  <div className="bubble coach" style={{ fontSize: 13 }}>Hi Maria! I'm Avery, prepping you for your call with Jane on Thursday 👋</div>
                  <div className="bubble coach" style={{ fontSize: 13 }}>This'll take about 4 min and saves a ton of time on the call. Ready?</div>
                  <div className="row gap-2" style={{ alignSelf: "flex-end" }}>
                    <button className="btn outline sm">Not now</button>
                    <button className="btn brand sm">Let's go →</button>
                  </div>
                </div>
              </div>
              <div style={{ padding: "14px 22px", background: "rgba(255,255,255,0.6)", borderTop: "1px solid var(--line)", fontSize: 12, color: "var(--ink-3)" }}>
                <div className="row between">
                  <span>6 modules · ~4m 30s</span>
                  <span>Expires in 7 days</span>
                </div>
              </div>
            </div>
            <div className="card card-pad-sm">
              <div className="row gap-2" style={{ fontSize: 12, color: "var(--ink-3)" }}>
                <Icon name="info" size={14} color="var(--teal-2)" />
                <span>Maria opted in to SMS on Mar 14. Link will be sent via text.</span>
              </div>
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
};

// ============================================================
// CUSTOMER DETAIL A — record + score card on right
// ============================================================
window.HiCustomerA = function HiCustomerA() {
  return (
    <div className="row" style={{ height: "100%" }}>
      <Sidebar active="customers" />
      <main style={{ flex: 1, overflow: "auto", background: "var(--bg)" }}>
        <div style={{ padding: "20px 32px 0" }}>
          <div style={{ fontSize: 12, color: "var(--ink-3)" }}>Customers <span style={{ color: "var(--ink-4)" }}>›</span> <span style={{ color: "var(--ink)" }}>Maria González</span></div>
        </div>
        <TopBar
          title="Maria González"
          subtitle="Client since Jan 2023 · Austin, TX · maria.g@email.com"
          actions={<><button className="btn outline"><Icon name="mail" size={14}/> Email</button><button className="btn outline"><Icon name="phone" size={14}/> Call</button><button className="btn brand"><Icon name="play" size={14}/> Pre-call summary</button></>}
        />
        <div style={{ padding: "24px 32px", display: "grid", gridTemplateColumns: "1fr 360px", gap: 24 }}>
          {/* Left: record */}
          <div className="col gap-4">
            <section className="card card-pad">
              <div className="row between">
                <h3 className="serif" style={{ fontSize: 18 }}>Household</h3>
                <button className="btn ghost sm"><Icon name="edit" size={13}/> Edit</button>
              </div>
              <div className="row gap-3" style={{ marginTop: 14, flexWrap: "wrap" }}>
                {[
                  ["Maria González", "37 · Self", "bg-mg", "MG"],
                  ["Carlos González", "39 · Spouse", "bg-cg", "CG"],
                  ["Sofia González", "8 · Dependent", "bg-sf", "SG"],
                  ["Diego González", "4 · Dependent", "bg-dg", "DG"],
                ].map(([n, r, bg, ini], i) => (
                  <div key={i} className="card card-pad-sm row gap-3" style={{ flex: "1 1 220px", background: "var(--bg)" }}>
                    <span className={`avatar md ${bg}`}>{ini}</span>
                    <div className="col" style={{ lineHeight: 1.25 }}>
                      <span style={{ fontSize: 14, fontWeight: 600 }}>{n}</span>
                      <span style={{ fontSize: 12, color: "var(--ink-3)" }}>{r}</span>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="card card-pad">
              <h3 className="serif" style={{ fontSize: 18, marginBottom: 14 }}>Current coverage</h3>
              <div className="col gap-3">
                {[
                  ["Medical", "BlueCross PPO · $2,400 deductible", "good", "Active", "shield"],
                  ["Dental", "Delta Dental Premier", "good", "Active", "smile"],
                  ["Vision", "Not covered", "warn", "Gap", "eye"],
                  ["Life (term)", "$250k · Carlos only", "warn", "Spouse uncovered", "heart"],
                  ["Auto + Home", "Not on file", "outline", "Referral opportunity", "car"],
                ].map(([type, detail, tone, label, ico], i) => (
                  <div key={i} className="row between" style={{ padding: "10px 14px", borderRadius: 12, background: i % 2 ? "var(--bg)" : "transparent" }}>
                    <div className="row gap-3">
                      <span style={{ width: 36, height: 36, borderRadius: 10, background: "var(--bg-2)", display: "inline-flex", alignItems: "center", justifyContent: "center" }}><Icon name={ico} size={17} color="var(--ink-2)"/></span>
                      <div className="col" style={{ lineHeight: 1.25 }}>
                        <span style={{ fontSize: 14, fontWeight: 600 }}>{type}</span>
                        <span style={{ fontSize: 12, color: "var(--ink-3)" }}>{detail}</span>
                      </div>
                    </div>
                    <span className={`chip ${tone} dot`}>{label}</span>
                  </div>
                ))}
              </div>
            </section>

            <section className="card card-pad">
              <h3 className="serif" style={{ fontSize: 18, marginBottom: 14 }}>Recent activity</h3>
              <div className="col" style={{ paddingLeft: 14, borderLeft: "2px solid var(--line)", gap: 18, position: "relative" }}>
                {[
                  ["Apr 28, 2:14p", "Avery sent intake link via SMS", "orange"],
                  ["Apr 22, 9:05a", "Annual review scheduled · Thursday 10am", "teal"],
                  ["Mar 14, 4:30p", "Carlos turned 39 · life event flagged", "good"],
                  ["Jan 2, 11:20a", "Onboarded · medical + dental added", null],
                ].map(([t, msg, tone], i) => (
                  <div key={i} style={{ position: "relative" }}>
                    <span className={`tl-dot ${tone || ""}`} />
                    <div style={{ fontSize: 11, color: "var(--ink-4)", textTransform: "uppercase", letterSpacing: "0.05em" }}>{t}</div>
                    <div style={{ fontSize: 14, color: "var(--ink-2)", marginTop: 2 }}>{msg}</div>
                  </div>
                ))}
              </div>
            </section>
          </div>

          {/* Right: score */}
          <aside className="col gap-4" style={{ position: "sticky", top: 0, alignSelf: "start" }}>
            <section className="card card-pad" style={{ background: "linear-gradient(160deg, #fdf1e8 0%, #ecf6f4 90%)" }}>
              <div style={{ fontSize: 11, color: "var(--ink-3)", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em" }}>Coverage gap score</div>
              <div className="row gap-4" style={{ marginTop: 12, alignItems: "center" }}>
                <Ring value={64} size={108} stroke={11} animate={true} />
                <div className="col" style={{ lineHeight: 1.05 }}>
                  <span className="serif" style={{ fontSize: 44 }}>64</span>
                  <span className="chip warn" style={{ marginTop: 6, alignSelf: "flex-start" }}>Moderate gap</span>
                </div>
              </div>
              <div style={{ fontSize: 12, color: "var(--ink-3)", marginTop: 14, lineHeight: 1.45 }}>
                Up <b style={{ color: "var(--good)" }}>+6</b> since January. Two open opportunities — vision and spouse life coverage.
              </div>
            </section>

            <section className="card card-pad">
              <h4 className="serif" style={{ fontSize: 16, marginBottom: 12 }}>Top 3 talking points</h4>
              <div className="col gap-3">
                {[
                  ["Vision plan for the family", "$0 today · ~$28/mo. Adds Sofia + Diego.", "warn", "eye"],
                  ["Term life for Maria", "Carlos covered, Maria not. ~$22/mo for $250k.", "bad", "heart"],
                  ["Bundle auto + home", "Partner referral · est. 12% household savings.", "teal", "house"],
                ].map(([t, sub, tone, ico], i) => (
                  <div key={i} className="row gap-3" style={{ padding: "10px 12px", border: "1px solid var(--line)", borderRadius: 12 }}>
                    <span style={{ width: 32, height: 32, borderRadius: 9, background: "var(--bg-2)", display: "inline-flex", alignItems: "center", justifyContent: "center" }}><Icon name={ico} size={15} color="var(--ink-2)"/></span>
                    <div className="col grow" style={{ lineHeight: 1.3 }}>
                      <span style={{ fontSize: 13, fontWeight: 600 }}>{t}</span>
                      <span style={{ fontSize: 12, color: "var(--ink-3)" }}>{sub}</span>
                    </div>
                    <span className={`chip ${tone}`} style={{ fontSize: 10 }}>•</span>
                  </div>
                ))}
              </div>
            </section>
          </aside>
        </div>
      </main>
    </div>
  );
};

// ============================================================
// PRE-CALL SUMMARY A — talking-point cards
// ============================================================
window.HiPrecallA = function HiPrecallA() {
  return (
    <div className="row" style={{ height: "100%" }}>
      <Sidebar active="summaries" />
      <main style={{ flex: 1, overflow: "auto", background: "var(--bg)" }}>
        <TopBar
          title="Pre-call · Maria González"
          subtitle="Thursday, May 1 · 10:00 AM · 30 min · Annual review"
          actions={<><button className="btn outline"><Icon name="calendar" size={14}/> Reschedule</button><button className="btn brand"><Icon name="sparkles" size={14}/> Open during call</button></>}
        />
        <div style={{ padding: "24px 32px", maxWidth: 1100 }}>
          {/* Snapshot */}
          <div className="card card-pad-lg" style={{ background: "linear-gradient(155deg, #fdf1e8 0%, #ecf6f4 100%)", marginBottom: 24 }}>
            <div className="row between" style={{ alignItems: "flex-start" }}>
              <div className="row gap-4">
                <span className="avatar xl bg-mg">MG</span>
                <div>
                  <h2 className="serif" style={{ fontSize: 26 }}>Maria González</h2>
                  <div style={{ fontSize: 13, color: "var(--ink-3)", marginTop: 4 }}>Family of 4 · Austin, TX · client since Jan 2023</div>
                  <div className="row gap-2" style={{ marginTop: 12 }}>
                    <span className="chip warn dot">2 gaps</span>
                    <span className="chip teal dot">1 referral</span>
                    <span className="chip outline">Score 64</span>
                    <span className="chip outline"><Icon name="clock" size={11}/> Submitted 2h ago</span>
                  </div>
                </div>
              </div>
              <div className="col" style={{ alignItems: "flex-end", lineHeight: 1.2 }}>
                <span style={{ fontSize: 11, color: "var(--ink-4)", textTransform: "uppercase", letterSpacing: "0.06em" }}>Avg call · gap closed</span>
                <span className="serif" style={{ fontSize: 26, marginTop: 4 }}>+12 pts</span>
              </div>
            </div>

            <div className="divider" style={{ margin: "20px 0" }} />

            <div style={{ fontSize: 14, color: "var(--ink-2)", lineHeight: 1.55 }}>
              <b>Avery's read:</b> Maria mentioned the kids' eye exams getting expensive last fall — vision is the warmest opener.
              Lead with the family vision plan, then circle to her own term-life gap (sensitive — she brought it up unprompted).
              Auto + home is a soft referral; only raise if she opens the door.
            </div>
          </div>

          {/* Talking-point cards */}
          <h3 className="serif" style={{ fontSize: 20, marginBottom: 12 }}>Talking points, in order</h3>
          <div className="col gap-3">
            {[
              {
                n: 1, tone: "warn", ico: "eye", title: "Vision plan for the whole family",
                hook: "She mentioned 'Sofia's glasses again' in intake.",
                ask: "Would adding vision for the kids make sense at $28/mo?",
                facts: ["No vision today", "Sofia: 2nd pair this year", "BlueCross add-on available"],
              },
              {
                n: 2, tone: "bad", ico: "heart", title: "Term life for Maria",
                hook: "Carlos has $250k term; Maria has nothing.",
                ask: "Have you thought about your own coverage now that the kids are older?",
                facts: ["~$22/mo for $250k", "Healthy non-smoker bracket", "Match Carlos's policy term"],
              },
              {
                n: 3, tone: "teal", ico: "house", title: "Auto + home bundle (referral)",
                hook: "Mentioned 'shopping insurance' in last note.",
                ask: "Want me to introduce you to our partner at Hutchins P&C?",
                facts: ["Est. 12% household savings", "Partner: David Liu", "Warm intro available"],
              },
            ].map((t) => (
              <article key={t.n} className="card card-pad" style={{ display: "grid", gridTemplateColumns: "auto 1fr 220px", gap: 20, alignItems: "start" }}>
                <div className="col center" style={{ width: 56 }}>
                  <span style={{ width: 44, height: 44, borderRadius: 12, background: "var(--bg-2)", display: "inline-flex", alignItems: "center", justifyContent: "center" }}><Icon name={t.ico} size={20} color="var(--ink-2)"/></span>
                  <span style={{ fontSize: 11, color: "var(--ink-4)", marginTop: 8, fontWeight: 600 }}>#{t.n}</span>
                </div>
                <div>
                  <div className="row gap-2">
                    <span className={`chip ${t.tone} dot`} style={{ fontSize: 11 }}>{t.tone === "bad" ? "high" : t.tone === "warn" ? "med" : "opportunity"}</span>
                  </div>
                  <h4 className="serif" style={{ fontSize: 19, marginTop: 6 }}>{t.title}</h4>
                  <div style={{ fontSize: 13, color: "var(--ink-3)", marginTop: 4 }}><b style={{ color: "var(--ink-2)" }}>Hook:</b> {t.hook}</div>
                  <div style={{ fontSize: 14, color: "var(--ink)", marginTop: 10, padding: "10px 14px", background: "var(--orange-tint)", borderRadius: 10, borderLeft: "3px solid var(--orange)", fontStyle: "italic" }}>"{t.ask}"</div>
                </div>
                <div className="col gap-2" style={{ paddingTop: 4 }}>
                  <span style={{ fontSize: 11, color: "var(--ink-4)", textTransform: "uppercase", letterSpacing: "0.06em", fontWeight: 600 }}>Quick facts</span>
                  {t.facts.map((f, i) => (
                    <div key={i} className="row gap-2" style={{ fontSize: 12, color: "var(--ink-2)" }}>
                      <Icon name="check" size={12} color="var(--good)"/> <span>{f}</span>
                    </div>
                  ))}
                </div>
              </article>
            ))}
          </div>

          <div className="row between" style={{ marginTop: 28, padding: "16px 20px", border: "1px dashed var(--line-2)", borderRadius: 14, background: "var(--surface-2)" }}>
            <div className="row gap-3">
              <Icon name="info" size={18} color="var(--teal-2)" />
              <div className="col" style={{ lineHeight: 1.3 }}>
                <span style={{ fontSize: 13, fontWeight: 600 }}>Don't bring up:</span>
                <span style={{ fontSize: 12, color: "var(--ink-3)" }}>Recent layoff at Carlos's company — she flagged it as private context.</span>
              </div>
            </div>
            <button className="btn ghost sm">Got it</button>
          </div>
        </div>
      </main>
    </div>
  );
};

Object.assign(window, { HiCreateA: window.HiCreateA, HiCustomerA: window.HiCustomerA, HiPrecallA: window.HiPrecallA });
