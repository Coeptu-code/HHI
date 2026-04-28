/* global React, AgentNav, HatchBox, Annot, SkRing, ConfettiBurst, PhoneFrame */
const { useState: useStateA, useEffect: useEffectA, useMemo: useMemoA } = React;

// ============================================================
// AGENT — DASHBOARD
// ============================================================

function StatCard({ label, value, sub, accent }) {
  return (
    <div className={`sk-box ${accent ? "sk-fill-accent" : "sk-fill-paper"}`} style={{ padding: 16, flex: 1, minWidth: 0 }}>
      <div className="hand-ui muted" style={{ fontSize: 14 }}>{label}</div>
      <div className="hand-title" style={{ fontSize: 38, lineHeight: 1.1, margin: "4px 0" }}>{value}</div>
      {sub && <div className="hand-ui faint" style={{ fontSize: 13 }}>{sub}</div>}
    </div>
  );
}

window.AgentDashboardA = function AgentDashboardA() {
  return (
    <div className="row" style={{ height: "100%", position: "relative" }}>
      <AgentNav active="dashboard" />
      <main style={{ flex: 1, padding: "24px 32px", overflow: "auto" }}>
        <div className="row between" style={{ marginBottom: 20 }}>
          <div>
            <div className="hand-title" style={{ fontSize: 38, lineHeight: 1 }}>Dashboard</div>
            <div className="hand-ui muted" style={{ fontSize: 15 }}>Tuesday, April 28 · Good afternoon, Jane</div>
          </div>
          <div className="row gap-3">
            <button className="sk-btn ghost"><span>🔍</span> Search</button>
            <button className="sk-btn primary">+ New intake link</button>
          </div>
        </div>

        <div className="row gap-4" style={{ marginBottom: 24 }}>
          <StatCard label="Total submissions" value="124" sub="↑ 12 this week" />
          <StatCard label="Referral opportunities" value="38" sub="9 partner-eligible" accent />
          <StatCard label="Avg coverage score" value="71" sub="Healthy range 60–85" />
          <StatCard label="Open intake links" value="14" sub="3 expire today" />
        </div>

        <div className="row gap-4" style={{ alignItems: "stretch" }}>
          <section className="sk-box sk-fill-paper" style={{ flex: 2, padding: 18 }}>
            <div className="row between" style={{ marginBottom: 10 }}>
              <div className="hand-title" style={{ fontSize: 24 }}>Recent intake links</div>
              <span className="hand-ui muted" style={{ fontSize: 13 }}>view all →</span>
            </div>
            <table style={{ width: "100%", fontFamily: "'Patrick Hand'", fontSize: 15, borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "1.6px dashed #1f2024", textAlign: "left" }}>
                  <th style={{ padding: "6px 4px" }}>Created</th>
                  <th>Status</th>
                  <th>Intake URL</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {[
                  ["Apr 28, 2:14p", "active", "/intake/9k2-fT3wQ"],
                  ["Apr 28, 11:02a", "completed", "/intake/2pB-aL9vE"],
                  ["Apr 27, 4:55p", "active", "/intake/HhX-7nMrR"],
                  ["Apr 27, 9:30a", "expired", "/intake/Vd4-bQz1S"],
                  ["Apr 26, 3:18p", "completed", "/intake/Mk9-yT0pN"],
                ].map(([when, status, url], i) => (
                  <tr key={i} style={{ borderBottom: "1px dotted #c8c5b8" }}>
                    <td style={{ padding: "8px 4px" }}>{when}</td>
                    <td><span className={`sk-chip ${status === "completed" ? "good" : status === "expired" ? "muted" : "accent"}`}>{status}</span></td>
                    <td><span className="sk-underline">{url}</span></td>
                    <td><button className="sk-btn" style={{ padding: "3px 10px", fontSize: 13 }}>Copy</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="sk-box sk-fill-2" style={{ flex: 1.2, padding: 18 }}>
            <div className="hand-title" style={{ fontSize: 24, marginBottom: 10 }}>Recent submissions</div>
            <div className="col gap-3">
              {[
                ["Maria González", "Submitted", "score 64", "warn"],
                ["David Patel", "In progress", "step 4 of 8", "muted"],
                ["The Chen family", "Submitted", "score 82", "good"],
                ["Reggie Thomas", "Submitted", "score 41", "bad"],
              ].map(([name, st, sub, tone], i) => (
                <div key={i} className="row between sk-tap" style={{ padding: "8px 10px", borderBottom: "1px dotted #c8c5b8" }}>
                  <div className="col" style={{ lineHeight: 1.15 }}>
                    <span className="hand-ui" style={{ fontSize: 16 }}>{name}</span>
                    <span className="hand-ui muted" style={{ fontSize: 13 }}>{st}</span>
                  </div>
                  <span className={`sk-chip ${tone}`}>{sub}</span>
                </div>
              ))}
            </div>
          </section>
        </div>

        <Annot top={70} right={32} w={170} rotate={-2}>
          search jumps to any client / link / submission
        </Annot>
        <Annot top={210} left={420} w={150} rotate={2}>
          accent card = the metric Jane cares about most
        </Annot>
      </main>
    </div>
  );
};

window.AgentDashboardB = function AgentDashboardB() {
  return (
    <div className="row" style={{ height: "100%", position: "relative" }}>
      <AgentNav active="dashboard" />
      <main style={{ flex: 1, padding: "24px 32px", overflow: "auto" }}>
        <div className="hand-title" style={{ fontSize: 32, marginBottom: 4 }}>Today</div>
        <div className="hand-ui muted" style={{ fontSize: 15, marginBottom: 20 }}>3 calls scheduled · 4 new submissions waiting for review</div>

        {/* Hero: today's queue, calendar style */}
        <section className="sk-box sk-fill-accent" style={{ padding: 20, marginBottom: 24 }}>
          <div className="row between" style={{ marginBottom: 14 }}>
            <div className="hand-title" style={{ fontSize: 24 }}>Your call queue</div>
            <button className="sk-btn">Sync calendar</button>
          </div>
          <div className="row gap-3" style={{ overflowX: "auto" }}>
            {[
              { time: "10:00 AM", name: "Maria González", score: 64, tag: "high gap" },
              { time: "11:30 AM", name: "David Patel", score: null, tag: "intake in progress" },
              { time: "2:00 PM", name: "The Chen family", score: 82, tag: "review" },
              { time: "3:30 PM", name: "Reggie Thomas", score: 41, tag: "critical" },
            ].map((c, i) => (
              <div key={i} className="sk-box sk-fill-paper" style={{ padding: 14, minWidth: 200 }}>
                <div className="hand-ui muted" style={{ fontSize: 13 }}>{c.time}</div>
                <div className="hand-title" style={{ fontSize: 20, lineHeight: 1.1, margin: "2px 0 8px" }}>{c.name}</div>
                <div className="row between">
                  <span className={`sk-chip ${i === 3 ? "bad" : i === 0 ? "warn" : i === 2 ? "good" : "muted"}`}>{c.tag}</span>
                  <span className="hand-title" style={{ fontSize: 22 }}>{c.score ?? "—"}</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        <div className="row gap-4">
          <section className="sk-box" style={{ flex: 1, padding: 18 }}>
            <div className="hand-title" style={{ fontSize: 22, marginBottom: 10 }}>This week</div>
            {/* Sketch sparkline */}
            <svg width="100%" height="100" className="sk-wobble">
              <polyline fill="none" stroke="#1f2024" strokeWidth="1.6"
                        points="10,80 60,72 110,55 160,62 210,38 260,45 310,28 360,36" />
              <polyline fill="none" stroke="#d97a3c" strokeWidth="2.2"
                        points="10,82 60,70 110,58 160,60 210,40 260,48 310,30 360,38" />
              {[10,60,110,160,210,260,310,360].map((x, i) => (
                <circle key={i} cx={x} cy={[82,70,58,60,40,48,30,38][i]} r="3" fill="#d97a3c" />
              ))}
            </svg>
            <div className="row between hand-ui muted" style={{ fontSize: 12, marginTop: 4 }}>
              <span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span><span></span>
            </div>
            <div className="row gap-2 hand-ui muted" style={{ fontSize: 13, marginTop: 10 }}>
              <span className="sk-chip accent">submissions ↑ 22%</span>
              <span className="sk-chip good">avg score ↑ 6 pts</span>
            </div>
          </section>

          <section className="sk-box sk-fill-2" style={{ flex: 1, padding: 18 }}>
            <div className="hand-title" style={{ fontSize: 22, marginBottom: 10 }}>Action items</div>
            <div className="col gap-2 hand-ui" style={{ fontSize: 15 }}>
              <div className="row gap-2"><span style={{ width: 16, height: 16, border: "1.8px solid #1f2024", borderRadius: 3, display: "inline-block" }}></span> Review Reggie Thomas (critical gaps)</div>
              <div className="row gap-2"><span style={{ width: 16, height: 16, border: "1.8px solid #1f2024", borderRadius: 3, background: "#1f2024", display: "inline-block" }}></span> <span className="sk-strike muted">Send Patel intake link</span></div>
              <div className="row gap-2"><span style={{ width: 16, height: 16, border: "1.8px solid #1f2024", borderRadius: 3, display: "inline-block" }}></span> Refer Chen family — auto + umbrella</div>
              <div className="row gap-2"><span style={{ width: 16, height: 16, border: "1.8px solid #1f2024", borderRadius: 3, display: "inline-block" }}></span> Re-send expired link to Vasquez</div>
            </div>
          </section>
        </div>

        <Annot top={150} right={40} w={180} rotate={-2}>
          queue replaces the table — agents work top-down through their day
        </Annot>
      </main>
    </div>
  );
};

Object.assign(window, {
  AgentDashboardA: window.AgentDashboardA,
  AgentDashboardB: window.AgentDashboardB,
});
