/* global React, AgentNav, HatchBox, Annot */

// ============================================================
// AGENT — CREATE INTAKE LINK, CUSTOMER DETAIL, PRE-CALL SUMMARY, LOGIN
// ============================================================

window.CreateLinkA = function CreateLinkA() {
  return (
    <div className="row" style={{ height: "100%", position: "relative" }}>
      <AgentNav active="links" />
      <main style={{ flex: 1, padding: "28px 40px", overflow: "auto" }}>
        <div className="hand-ui muted" style={{ fontSize: 13 }}>Dashboard / Intake Links / <span style={{ color: "#1f2024" }}>New</span></div>
        <div className="hand-title" style={{ fontSize: 36, marginTop: 4, marginBottom: 4 }}>Create intake link</div>
        <div className="hand-ui muted" style={{ fontSize: 15, marginBottom: 22 }}>
          Pick which gap-scoring modules to include. Clients see one blended form — no module sections.
        </div>

        <div className="row gap-4" style={{ alignItems: "flex-start" }}>
          <section className="sk-box sk-fill-paper" style={{ flex: 1.4, padding: 22 }}>
            <div className="hand-title" style={{ fontSize: 22, marginBottom: 8 }}>1. Modules to include</div>
            <div className="hand-ui muted" style={{ fontSize: 13, marginBottom: 14 }}>Internal only · clients won't see this</div>
            <div className="col gap-3">
              {[
                ["health", "Health coverage", "Plan type, gaps, dependents", true],
                ["life", "Life insurance", "Term/whole, beneficiary needs", true],
                ["auto", "Auto", "Liability, drivers, vehicles", true],
                ["home", "Home / renters", "Property, dwelling, contents", false],
                ["umbrella", "Umbrella", "Excess liability over auto/home", false],
              ].map(([k, name, sub, on], i) => (
                <label key={k} className="row gap-3 sk-tap" style={{ padding: "10px 12px", border: "1.8px solid #1f2024", borderRadius: 10, background: on ? "#fde7d6" : "#fafaf6" }}>
                  <span style={{ width: 20, height: 20, border: "2px solid #1f2024", borderRadius: 5, background: on ? "#1f2024" : "transparent", display: "inline-flex", alignItems: "center", justifyContent: "center", color: "#fff", fontSize: 13 }}>{on ? "✓" : ""}</span>
                  <div className="col grow" style={{ lineHeight: 1.15 }}>
                    <span className="hand-title" style={{ fontSize: 18 }}>{name}</span>
                    <span className="hand-ui muted" style={{ fontSize: 13 }}>{sub}</span>
                  </div>
                  <span className="sk-chip muted">{on ? "included" : "off"}</span>
                </label>
              ))}
            </div>

            <div className="hand-title" style={{ fontSize: 22, margin: "22px 0 8px" }}>2. Send to (optional)</div>
            <div className="row gap-3">
              <div className="col grow gap-2">
                <label className="hand-ui" style={{ fontSize: 14 }}>Client name</label>
                <input className="sk-input" placeholder="Maria González" defaultValue="Maria González" />
              </div>
              <div className="col grow gap-2">
                <label className="hand-ui" style={{ fontSize: 14 }}>Email or phone</label>
                <input className="sk-input" placeholder="maria@example.com" />
              </div>
            </div>

            <div className="hand-title" style={{ fontSize: 22, margin: "22px 0 8px" }}>3. Expiration</div>
            <div className="sk-tabs">
              {["24h", "7 days", "30 days", "Never"].map((t, i) => (
                <span key={t} className={`sk-tab ${i === 1 ? "active" : ""}`}>{t}</span>
              ))}
            </div>

            <div className="row between" style={{ marginTop: 26 }}>
              <button className="sk-btn ghost">Cancel</button>
              <div className="row gap-2">
                <button className="sk-btn">Save as draft</button>
                <button className="sk-btn primary">Create link →</button>
              </div>
            </div>
          </section>

          <aside className="sk-box sk-fill-2" style={{ flex: 1, padding: 22 }}>
            <div className="hand-title" style={{ fontSize: 22, marginBottom: 10 }}>Client preview</div>
            <div className="hand-ui muted" style={{ fontSize: 13, marginBottom: 12 }}>What Maria will see when she opens the link</div>
            <div className="sk-box sk-fill-paper" style={{ padding: 14 }}>
              <div className="hand-title" style={{ fontSize: 20, marginBottom: 6 }}>Hi Maria 👋</div>
              <div className="hand-ui" style={{ fontSize: 14, lineHeight: 1.4 }}>
                Let's get you set up. About <strong>5 minutes</strong>, no spam, "not sure" is always fine.
              </div>
              <div className="row gap-2" style={{ marginTop: 14, flexWrap: "wrap" }}>
                <span className="sk-chip accent">Health</span>
                <span className="sk-chip accent">Life</span>
                <span className="sk-chip accent">Auto</span>
              </div>
              <div className="hand-ui muted" style={{ fontSize: 12, marginTop: 14 }}>~24 questions, conversational</div>
            </div>
            <Annot top={120} right={-10} w={140} rotate={4}>
              live preview updates as modules toggle
            </Annot>
          </aside>
        </div>
      </main>
    </div>
  );
};

window.CreateLinkB = function CreateLinkB() {
  return (
    <div className="row" style={{ height: "100%", position: "relative" }}>
      <AgentNav active="links" />
      <main style={{ flex: 1, padding: "28px 40px", overflow: "auto" }}>
        <div className="hand-title" style={{ fontSize: 32, marginBottom: 4 }}>New intake link</div>
        <div className="hand-ui muted" style={{ fontSize: 15, marginBottom: 22 }}>Quick mode — link in 10 seconds.</div>

        {/* Single-row inline form */}
        <section className="sk-box sk-fill-paper" style={{ padding: 18, marginBottom: 18 }}>
          <div className="row gap-3" style={{ alignItems: "flex-end" }}>
            <div className="col gap-2" style={{ flex: 1.2 }}>
              <label className="hand-ui muted" style={{ fontSize: 13 }}>Client</label>
              <input className="sk-input" defaultValue="Maria González" />
            </div>
            <div className="col gap-2" style={{ flex: 1 }}>
              <label className="hand-ui muted" style={{ fontSize: 13 }}>Send via</label>
              <select className="sk-input" style={{ appearance: "none" }} defaultValue="text">
                <option>Email</option><option>Text</option><option>Copy link</option>
              </select>
            </div>
            <div className="col gap-2" style={{ flex: 1.2 }}>
              <label className="hand-ui muted" style={{ fontSize: 13 }}>Expires</label>
              <input className="sk-input" defaultValue="May 5, 2026 (7 days)" />
            </div>
            <button className="sk-btn primary lg">Create →</button>
          </div>
        </section>

        {/* Module preset chips */}
        <section className="sk-box" style={{ padding: 18, marginBottom: 18 }}>
          <div className="row between" style={{ marginBottom: 10 }}>
            <div className="hand-title" style={{ fontSize: 20 }}>Modules</div>
            <div className="hand-ui muted" style={{ fontSize: 13 }}>presets:
              <span className="sk-chip accent" style={{ marginLeft: 8 }}>Full sweep</span>
              <span className="sk-chip muted" style={{ marginLeft: 6 }}>Health only</span>
              <span className="sk-chip muted" style={{ marginLeft: 6 }}>Family bundle</span>
            </div>
          </div>
          <div className="row gap-2" style={{ flexWrap: "wrap" }}>
            {[["Health", true],["Life", true],["Auto", true],["Home", false],["Umbrella", false]].map(([n, on]) => (
              <span key={n} className={`sk-chip ${on ? "accent" : "muted"}`} style={{ fontSize: 15, padding: "6px 14px" }}>
                {on ? "✓ " : "+ "}{n}
              </span>
            ))}
          </div>
        </section>

        {/* Recent links list (compact) */}
        <section>
          <div className="hand-title" style={{ fontSize: 20, marginBottom: 10 }}>Recent links</div>
          <div className="col gap-2">
            {[
              ["Maria González", "active · 2h ago", "active"],
              ["Patel, David", "completed · score 78", "good"],
              ["Vasquez household", "expired · resend?", "muted"],
            ].map(([n, m, t], i) => (
              <div key={i} className="sk-box sk-fill-paper row between" style={{ padding: "10px 14px" }}>
                <div className="col" style={{ lineHeight: 1.15 }}>
                  <span className="hand-title" style={{ fontSize: 18 }}>{n}</span>
                  <span className="hand-ui muted" style={{ fontSize: 13 }}>{m}</span>
                </div>
                <div className="row gap-2">
                  <span className={`sk-chip ${t}`}>{t === "muted" ? "expired" : t === "good" ? "done" : "open"}</span>
                  <button className="sk-btn" style={{ fontSize: 13, padding: "4px 10px" }}>Copy</button>
                </div>
              </div>
            ))}
          </div>
        </section>

        <Annot top={150} right={40} w={150} rotate={-3}>
          one-row express creation — most agents only edit the name
        </Annot>
      </main>
    </div>
  );
};

// ----- CUSTOMER DETAIL -----

window.CustomerDetailA = function CustomerDetailA() {
  return (
    <div className="row" style={{ height: "100%", position: "relative" }}>
      <AgentNav active="customers" />
      <main style={{ flex: 1, padding: "28px 40px", overflow: "auto" }}>
        <div className="hand-ui muted" style={{ fontSize: 13 }}>Customers / <span style={{ color: "#1f2024" }}>Maria González</span></div>

        <div className="row gap-4" style={{ alignItems: "flex-start", marginTop: 8 }}>
          <div className="sk-box sk-fill-paper" style={{ padding: 22, flex: 1.2 }}>
            <div className="row gap-3" style={{ marginBottom: 14 }}>
              <div style={{ width: 64, height: 64, borderRadius: 50, background: "#fde7d6", border: "2px solid #1f2024", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'Caveat'", fontSize: 30, fontWeight: 700 }}>MG</div>
              <div className="col grow" style={{ lineHeight: 1.15 }}>
                <div className="hand-title" style={{ fontSize: 30 }}>Maria González</div>
                <div className="hand-ui muted" style={{ fontSize: 15 }}>maria.g@example.com · (512) 555-0142 · TX</div>
                <div className="row gap-2" style={{ marginTop: 6 }}>
                  <span className="sk-chip accent">prefers texts</span>
                  <span className="sk-chip muted">household of 3</span>
                </div>
              </div>
              <div className="col gap-2">
                <button className="sk-btn primary">Schedule call</button>
                <button className="sk-btn">Send link</button>
              </div>
            </div>

            <div className="hand-title" style={{ fontSize: 22, marginTop: 14, marginBottom: 8 }}>Submissions</div>
            <div className="col gap-2">
              {[
                ["Apr 28, 2026", "Submitted", "score 64", "warn"],
                ["Mar 02, 2026", "Submitted", "score 58", "bad"],
                ["Jan 14, 2026", "In progress", "step 5/8", "muted"],
              ].map(([d, s, sc, t], i) => (
                <div key={i} className="row between sk-box sk-fill-2 sk-tap" style={{ padding: "10px 14px" }}>
                  <span className="hand-ui" style={{ fontSize: 15 }}>{d} · {s}</span>
                  <div className="row gap-3">
                    <span className={`sk-chip ${t}`}>{sc}</span>
                    <span className="hand-ui sk-underline" style={{ fontSize: 14 }}>summary →</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="hand-title" style={{ fontSize: 22, marginTop: 22, marginBottom: 8 }}>Notes</div>
            <div className="sk-box sk-fill-2" style={{ padding: 14, fontFamily: "'Patrick Hand'", fontSize: 15, lineHeight: 1.4 }}>
              Apr 28 — Wants to discuss adding spouse to plan before May open enrollment. <br/>
              Mar 03 — Following up on auto referral; partner agent contacted.
            </div>
          </div>

          <aside className="sk-box sk-fill-accent" style={{ padding: 22, flex: 1 }}>
            <div className="hand-title" style={{ fontSize: 22, marginBottom: 8 }}>Latest CoveraGap™</div>
            <div style={{ display: "flex", justifyContent: "center", margin: "8px 0" }}>
              <div style={{ position: "relative", width: 160, height: 160 }}>
                <SkRing value={64} size={160} stroke={12} animate={false} />
                <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
                  <div className="hand-title" style={{ fontSize: 42, lineHeight: 1 }}>64</div>
                  <div className="hand-ui muted" style={{ fontSize: 12 }}>/ 100</div>
                </div>
              </div>
            </div>
            <div className="col gap-2" style={{ fontFamily: "'Patrick Hand'", fontSize: 15 }}>
              <div className="row between"><span>Health</span><span>72</span></div>
              <div className="row between"><span>Life</span><span>40</span></div>
              <div className="row between"><span>Auto</span><span>65</span></div>
              <div className="row between"><span>Home</span><span>—</span></div>
            </div>
            <Annot top={20} right={-10} w={130} rotate={5}>
              hero score on a customer's record card
            </Annot>
          </aside>
        </div>
      </main>
    </div>
  );
};

window.CustomerDetailB = function CustomerDetailB() {
  return (
    <div className="row" style={{ height: "100%", position: "relative" }}>
      <AgentNav active="customers" />
      <main style={{ flex: 1, padding: "28px 40px", overflow: "auto" }}>
        <div className="row between" style={{ marginBottom: 14 }}>
          <div>
            <div className="hand-title" style={{ fontSize: 32 }}>Maria González</div>
            <div className="hand-ui muted" style={{ fontSize: 15 }}>Customer since Jan 2026 · 3 submissions · last contact 2 days ago</div>
          </div>
          <div className="sk-tabs">
            {["Overview", "Timeline", "Submissions", "Notes", "Files"].map((t, i) => (
              <span key={t} className={`sk-tab ${i === 1 ? "active" : ""}`}>{t}</span>
            ))}
          </div>
        </div>

        {/* Timeline view */}
        <section className="sk-box sk-fill-paper" style={{ padding: 22, position: "relative" }}>
          <div className="hand-title" style={{ fontSize: 22, marginBottom: 14 }}>Timeline</div>
          <div style={{ position: "relative", paddingLeft: 28 }}>
            <div style={{ position: "absolute", left: 9, top: 6, bottom: 6, width: 2, background: "#1f2024", opacity: 0.6 }} />
            {[
              { d: "Apr 28 · 2:14p", title: "Submitted intake", body: "Score 64 · 4 findings · 2 referrals (auto, life)", tone: "warn" },
              { d: "Apr 28 · 1:02p", title: "Opened intake link", body: "Mobile · iOS Safari · ~7 min on form", tone: "muted" },
              { d: "Apr 28 · 9:00a", title: "Intake link sent", body: "Texted to (512) 555-0142", tone: "accent" },
              { d: "Apr 27 · 11:30a", title: "Note added", body: '"Wants to add spouse to plan before May."', tone: "muted" },
              { d: "Mar 02", title: "Earlier intake", body: "Score 58 · referred to partner for auto", tone: "muted" },
              { d: "Jan 14, 2026", title: "Customer created", body: "Imported from open enrollment lead list", tone: "good" },
            ].map((e, i) => (
              <div key={i} style={{ position: "relative", marginBottom: 16 }}>
                <span style={{ position: "absolute", left: -22, top: 4, width: 14, height: 14, borderRadius: 50, background: "#fafaf6", border: "2px solid #1f2024" }} />
                <div className="hand-ui muted" style={{ fontSize: 12 }}>{e.d}</div>
                <div className="row gap-2" style={{ alignItems: "baseline" }}>
                  <span className="hand-title" style={{ fontSize: 18 }}>{e.title}</span>
                  <span className={`sk-chip ${e.tone}`} style={{ fontSize: 11 }}>{e.tone === "warn" ? "needs review" : e.tone === "good" ? "done" : "log"}</span>
                </div>
                <div className="hand-ui" style={{ fontSize: 14, color: "#4a4d55" }}>{e.body}</div>
              </div>
            ))}
          </div>
          <Annot top={20} right={20} w={150} rotate={-2}>
            timeline = single chronological story per customer
          </Annot>
        </section>
      </main>
    </div>
  );
};

// ----- PRE-CALL SUMMARY -----

window.PreCallA = function PreCallA() {
  return (
    <div className="row" style={{ height: "100%", position: "relative" }}>
      <AgentNav active="summaries" />
      <main style={{ flex: 1, padding: "24px 32px", overflow: "auto" }}>
        <div className="row between">
          <div>
            <div className="hand-ui muted" style={{ fontSize: 13 }}>Pre-call summary · Submission #4821</div>
            <div className="hand-title" style={{ fontSize: 32, marginTop: 2 }}>Maria González</div>
          </div>
          <div className="row gap-2">
            <button className="sk-btn">Print</button>
            <button className="sk-btn primary">Start call ▶</button>
          </div>
        </div>

        {/* Score row */}
        <div className="row gap-4" style={{ margin: "18px 0" }}>
          <div className="sk-box sk-fill-accent" style={{ padding: 18, flex: 1 }}>
            <div className="hand-ui muted" style={{ fontSize: 13 }}>Coverage Score</div>
            <div className="hand-title" style={{ fontSize: 50, lineHeight: 1 }}>64<span style={{ fontSize: 22, color: "#4a4d55" }}> / 100</span></div>
          </div>
          <div className="sk-box sk-fill-paper" style={{ padding: 18, flex: 1 }}>
            <div className="hand-ui muted" style={{ fontSize: 13 }}>Gap Risk</div>
            <div className="hand-title" style={{ fontSize: 50, lineHeight: 1 }}>36 pts</div>
          </div>
          <div className="sk-box sk-fill-paper" style={{ padding: 18, flex: 1 }}>
            <div className="hand-ui muted" style={{ fontSize: 13 }}>Findings</div>
            <div className="row gap-2" style={{ marginTop: 6 }}>
              <span className="sk-chip bad">1 critical</span>
              <span className="sk-chip warn">2 high</span>
              <span className="sk-chip muted">1 med</span>
            </div>
          </div>
          <div className="sk-box sk-fill-paper" style={{ padding: 18, flex: 1 }}>
            <div className="hand-ui muted" style={{ fontSize: 13 }}>Referrals</div>
            <div className="row gap-2" style={{ marginTop: 6 }}>
              <span className="sk-chip accent2">Auto</span>
              <span className="sk-chip accent2">Life</span>
            </div>
          </div>
        </div>

        <div className="row gap-4" style={{ alignItems: "flex-start" }}>
          {/* CARDS layout */}
          <div className="col gap-3" style={{ flex: 2 }}>
            <div className="hand-title" style={{ fontSize: 22 }}>Talking points (top 4)</div>
            {[
              { tag: "critical", cat: "Life", title: "No life coverage with 2 dependents under 19", body: "Maria has two kids on her plan. No life policy exists. Suggest a 20-year term quote — partner referral.", tone: "bad" },
              { tag: "high", cat: "Health", title: "Spouse not currently enrolled", body: "Spouse Carlos is uninsured but has employer access. Confirm whether dual coverage makes sense.", tone: "warn" },
              { tag: "high", cat: "Auto", title: "Liability at state minimum", body: "TX 30/60/25 — too low given household assets. Recommend 100/300/100 + umbrella conversation.", tone: "warn" },
              { tag: "medium", cat: "Health", title: "3 chronic-care prescriptions, formulary not verified", body: "Metformin, Lisinopril, Atorvastatin. Verify current plan formulary before renewal.", tone: "muted" },
            ].map((p, i) => (
              <div key={i} className={`sk-box ${p.tone === "bad" ? "sk-fill-bad" : p.tone === "warn" ? "sk-fill-warn" : "sk-fill-2"}`} style={{ padding: 14 }}>
                <div className="row gap-2" style={{ alignItems: "center", marginBottom: 4 }}>
                  <span className={`sk-chip ${p.tone}`}>{p.tag}</span>
                  <span className="hand-ui muted" style={{ fontSize: 12 }}>{p.cat}</span>
                </div>
                <div className="hand-title" style={{ fontSize: 18, lineHeight: 1.15, marginBottom: 4 }}>{p.title}</div>
                <div className="hand-ui" style={{ fontSize: 14, color: "#4a4d55" }}>{p.body}</div>
              </div>
            ))}
          </div>

          <aside className="col gap-3" style={{ flex: 1 }}>
            <div className="sk-box sk-fill-paper" style={{ padding: 14 }}>
              <div className="hand-title" style={{ fontSize: 18, marginBottom: 6 }}>Household</div>
              <div className="hand-ui" style={{ fontSize: 14, lineHeight: 1.5 }}>
                <div>Maria (you) · 38</div>
                <div>Carlos (spouse) · 41 · uninsured</div>
                <div>Sofia · 12</div>
                <div>Diego · 9</div>
              </div>
            </div>
            <div className="sk-box sk-fill-paper" style={{ padding: 14 }}>
              <div className="hand-title" style={{ fontSize: 18, marginBottom: 6 }}>Prescriptions</div>
              <div className="hand-ui" style={{ fontSize: 14, lineHeight: 1.5 }}>
                <div>Maria — Metformin 500 mg</div>
                <div>Maria — Lisinopril 10 mg</div>
                <div>Carlos — Atorvastatin 20 mg</div>
              </div>
            </div>
            <div className="sk-box sk-fill-2" style={{ padding: 14 }}>
              <div className="hand-title" style={{ fontSize: 18, marginBottom: 6 }}>Quick consents</div>
              <div className="hand-ui" style={{ fontSize: 13 }}>
                ✓ Terms ✓ Privacy ✓ Contact ✓ Referral sharing
              </div>
            </div>
          </aside>
        </div>

        <Annot top={150} right={40} w={150} rotate={-3}>
          cards layout — each finding is its own talking point
        </Annot>
      </main>
    </div>
  );
};

window.PreCallB = function PreCallB() {
  return (
    <div className="row" style={{ height: "100%", position: "relative" }}>
      <AgentNav active="summaries" />
      <main style={{ flex: 1, padding: "24px 32px", overflow: "auto" }}>
        <div className="row between">
          <div className="hand-title" style={{ fontSize: 30 }}>Maria González — call brief</div>
          <button className="sk-btn primary">Start call ▶</button>
        </div>
        <div className="hand-ui muted" style={{ fontSize: 14, marginBottom: 18 }}>10 min call · scheduled 11:30 AM today · texted brief 8 min ago</div>

        {/* Module bar table */}
        <section className="sk-box sk-fill-paper" style={{ padding: 18, marginBottom: 18 }}>
          <div className="hand-title" style={{ fontSize: 22, marginBottom: 10 }}>By module</div>
          <table style={{ width: "100%", fontFamily: "'Patrick Hand'", fontSize: 15, borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1.6px dashed #1f2024", textAlign: "left" }}>
                <th style={{ padding: "6px 4px", width: 90 }}>Module</th>
                <th style={{ width: 70 }}>Score</th>
                <th>Distribution</th>
                <th style={{ width: 130 }}>Owner</th>
                <th>Findings</th>
              </tr>
            </thead>
            <tbody>
              {[
                ["Health", 72, "Hutchins", ["1 high"], 0.72, "warn"],
                ["Life",    40, "Partner",  ["1 critical"], 0.40, "bad"],
                ["Auto",    65, "Partner",  ["1 high"], 0.65, "warn"],
                ["Home",    "—", "Skipped", [], 0, "muted"],
              ].map(([mod, sc, owner, findings, frac, tone], i) => (
                <tr key={i} style={{ borderBottom: "1px dotted #c8c5b8" }}>
                  <td style={{ padding: "10px 4px" }}><span className="hand-title" style={{ fontSize: 17 }}>{mod}</span></td>
                  <td><span className="hand-title" style={{ fontSize: 19 }}>{sc}</span></td>
                  <td>
                    <div style={{ position: "relative", height: 14, width: "100%", maxWidth: 320, border: "1.8px solid #1f2024", borderRadius: 6, background: "#fafaf6" }}>
                      <div style={{ height: "100%", width: `${(frac || 0) * 100}%`, background: tone === "bad" ? "#b85544" : tone === "warn" ? "#d97a3c" : tone === "good" ? "#4a8c5c" : "#c8c5b8", borderRight: "1.8px solid #1f2024" }} />
                    </div>
                  </td>
                  <td><span className={`sk-chip ${owner === "Hutchins" ? "good" : owner === "Partner" ? "accent2" : "muted"}`}>{owner}</span></td>
                  <td>{findings.map((f, j) => <span key={j} className={`sk-chip ${tone}`} style={{ marginRight: 4 }}>{f}</span>)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        {/* Talking points: short numbered list */}
        <section className="sk-box sk-fill-2" style={{ padding: 18 }}>
          <div className="hand-title" style={{ fontSize: 22, marginBottom: 10 }}>Recommended talking points</div>
          <ol style={{ fontFamily: "'Patrick Hand'", fontSize: 16, lineHeight: 1.7, paddingLeft: 22 }}>
            <li>Open with life coverage gap — kids are the hook.</li>
            <li>Confirm spouse Carlos's employer plan eligibility before recommending dual.</li>
            <li>Walk through TX auto liability minimums vs. household assets.</li>
            <li>Verify all 3 prescriptions on current formulary; flag if changing plans.</li>
            <li>Get verbal OK to share auto + life with partner agents.</li>
          </ol>
        </section>

        <Annot top={70} right={36} w={150} rotate={-3}>
          table layout — scan modules + scores + owners at a glance
        </Annot>
      </main>
    </div>
  );
};

// ----- LOGIN -----

window.LoginA = function LoginA() {
  return (
    <div style={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center", background: "#faf8ee", position: "relative" }}>
      <div className="row gap-4" style={{ alignItems: "stretch" }}>
        <div className="sk-box sk-fill-paper" style={{ padding: 36, width: 380 }}>
          <div className="hand-title" style={{ fontSize: 36, marginBottom: 6 }}>
            <span style={{ color: "#d97a3c" }}>△</span> PyraInsure
          </div>
          <div className="hand-ui muted" style={{ fontSize: 14, marginBottom: 24 }}>Agent sign-in</div>

          <label className="hand-ui" style={{ fontSize: 13 }}>Email</label>
          <input className="sk-input" defaultValue="jane@hutchinshealth.com" style={{ marginBottom: 14 }} />

          <label className="hand-ui" style={{ fontSize: 13 }}>Password</label>
          <input className="sk-input" type="password" defaultValue="••••••••••" style={{ marginBottom: 18 }} />

          <button className="sk-btn primary full">Sign in</button>
          <div className="row between" style={{ marginTop: 14 }}>
            <span className="hand-ui muted" style={{ fontSize: 13 }}><label><input type="checkbox" defaultChecked style={{ marginRight: 4 }}/> Remember me</label></span>
            <span className="hand-ui sk-underline" style={{ fontSize: 13 }}>Forgot password?</span>
          </div>
        </div>

        <div className="sk-box sk-fill-accent" style={{ padding: 28, width: 320 }}>
          <div className="hand-title" style={{ fontSize: 22, marginBottom: 10 }}>What's new</div>
          <ul className="hand-ui" style={{ fontSize: 14, lineHeight: 1.6, paddingLeft: 18 }}>
            <li>Pre-call summaries now include spouse coverage flags</li>
            <li>Conversational intake (Noom-style) is live</li>
            <li>Bulk re-send for expired links</li>
          </ul>
          <div className="hand-ui muted" style={{ fontSize: 12, marginTop: 12 }}>Build 4.21 · Apr 26, 2026</div>
        </div>
      </div>
      <Annot bottom={30} left={40} w={180} rotate={-2}>
        classic email/password — minimal, branded card on paper background
      </Annot>
    </div>
  );
};

window.LoginB = function LoginB() {
  return (
    <div style={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center", background: "#faf8ee", position: "relative" }}>
      <div className="sk-box sk-fill-paper" style={{ padding: 36, width: 420, textAlign: "center" }}>
        <div className="hand-title" style={{ fontSize: 32, marginBottom: 8 }}>
          <span style={{ color: "#d97a3c" }}>△</span> Welcome back
        </div>
        <div className="hand-ui muted" style={{ fontSize: 14, marginBottom: 24 }}>Sign in to PyraInsure with one tap</div>

        <button className="sk-btn full" style={{ marginBottom: 10, justifyContent: "flex-start", padding: "10px 14px" }}>
          <span style={{ width: 22, height: 22, background: "#fff", border: "1.6px solid #1f2024", borderRadius: 50, display: "inline-flex", alignItems: "center", justifyContent: "center", fontSize: 13 }}>G</span>
          Continue with Google
        </button>
        <button className="sk-btn full" style={{ marginBottom: 10, justifyContent: "flex-start", padding: "10px 14px" }}>
          <span style={{ width: 22, height: 22, background: "#1f2024", color: "#fff", borderRadius: 50, display: "inline-flex", alignItems: "center", justifyContent: "center", fontSize: 13 }}>🍎</span>
          Continue with Apple
        </button>
        <button className="sk-btn full" style={{ marginBottom: 16, justifyContent: "flex-start", padding: "10px 14px" }}>
          <span style={{ width: 22, height: 22, background: "#fde7d6", border: "1.6px solid #1f2024", borderRadius: 50, display: "inline-flex", alignItems: "center", justifyContent: "center", fontSize: 13 }}>✉</span>
          Email me a magic link
        </button>

        <div className="row gap-2" style={{ alignItems: "center", margin: "10px 0" }}>
          <div style={{ flex: 1, height: 1, background: "#c8c5b8" }} />
          <span className="hand-ui muted" style={{ fontSize: 12 }}>or with password</span>
          <div style={{ flex: 1, height: 1, background: "#c8c5b8" }} />
        </div>

        <input className="sk-input" placeholder="email" style={{ marginBottom: 8 }} />
        <input className="sk-input" placeholder="password" type="password" style={{ marginBottom: 14 }} />
        <button className="sk-btn primary full">Sign in</button>
      </div>
      <Annot bottom={30} right={40} w={180} rotate={2}>
        SSO-first — agents on company Google sign in 1 tap
      </Annot>
    </div>
  );
};

Object.assign(window, {
  CreateLinkA: window.CreateLinkA, CreateLinkB: window.CreateLinkB,
  CustomerDetailA: window.CustomerDetailA, CustomerDetailB: window.CustomerDetailB,
  PreCallA: window.PreCallA, PreCallB: window.PreCallB,
  LoginA: window.LoginA, LoginB: window.LoginB,
});
