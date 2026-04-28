/* global React, Sidebar, TopBar, Icon, Logo, Ring */
const { useState: useSa, useEffect: useEa } = React;

// ============================================================
// LOGIN A — full fidelity
// ============================================================
window.HiLoginA = function HiLoginA() {
  return (
    <div style={{ height: "100%", display: "grid", gridTemplateColumns: "1fr 1fr", background: "var(--bg)" }}>
      {/* Left: form */}
      <div className="col center" style={{ padding: "60px" }}>
        <div style={{ width: 380 }}>
          <Logo size={48} />
          <h1 className="serif" style={{ fontSize: 38, lineHeight: 1.05, marginTop: 36 }}>Welcome back.</h1>
          <p style={{ color: "var(--ink-3)", fontSize: 15, marginTop: 8, marginBottom: 28 }}>
            Sign in to keep prepping calls, sending intakes, and closing gaps.
          </p>

          <div className="col gap-4">
            <label className="field">
              <span>Email</span>
              <input className="input" defaultValue="jane@hutchinshealth.com" />
            </label>
            <label className="field">
              <span>Password</span>
              <input className="input" type="password" defaultValue="••••••••••••" />
            </label>
            <div className="row between" style={{ fontSize: 13 }}>
              <label className="row gap-2"><input type="checkbox" defaultChecked /> <span style={{ color: "var(--ink-2)" }}>Remember me</span></label>
              <a href="#" style={{ color: "var(--orange-2)", fontWeight: 500, textDecoration: "none" }}>Forgot password?</a>
            </div>
            <button className="btn brand lg full">Sign in <Icon name="arrow" size={16} /></button>
            <div className="row gap-3" style={{ alignItems: "center", marginTop: 4 }}>
              <div className="divider" style={{ flex: 1 }} />
              <span style={{ fontSize: 11, color: "var(--ink-4)", letterSpacing: "0.06em", textTransform: "uppercase" }}>or continue with</span>
              <div className="divider" style={{ flex: 1 }} />
            </div>
            <div className="row gap-3">
              <button className="btn outline full"><Icon name="google" size={16} color="#e57244" /> Google</button>
              <button className="btn outline full"><Icon name="apple" size={16} /> Apple</button>
            </div>
          </div>

          <div style={{ fontSize: 13, color: "var(--ink-3)", marginTop: 32, textAlign: "center" }}>
            New agent here? <a href="#" style={{ color: "var(--orange-2)", fontWeight: 500, textDecoration: "none" }}>Request access</a>
          </div>
        </div>
      </div>

      {/* Right: marketing */}
      <div className="login-aurora" style={{ background: "linear-gradient(155deg, #fdf1e8 0%, #ecf6f4 80%)", padding: 60, position: "relative", overflow: "hidden" }}>
        <div className="blob blob-1" />
        <div className="blob blob-2" />
        <div className="blob blob-3" />
        <div className="blob blob-4" />
        <div className="sheen" />
        <div className="sparkle s1" />
        <div className="sparkle s2" />
        <div className="sparkle s3" />
        <div className="sparkle s4" />

        <div className="col gap-8" style={{ position: "relative", minHeight: "100%", justifyContent: "flex-start" }}>
          <div className="chip orange dot"><span>What's new · Build 4.21</span></div>
          <div>
            <h2 className="serif" style={{ fontSize: 32, lineHeight: 1.15, color: "var(--ink)" }}>
              Conversational intake is live. Clients finish in under 5 minutes.
            </h2>
            <p style={{ color: "var(--ink-3)", fontSize: 15, marginTop: 14, maxWidth: 380 }}>
              Avery — your client's prep coach — walks them through household, coverage, and prescriptions one question at a time.
            </p>
            <div className="row gap-3" style={{ marginTop: 20 }}>
              <span className="chip teal dot">Avg time 4m 12s</span>
              <span className="chip orange dot">+38% completions</span>
            </div>
          </div>
          <div className="card card-pad" style={{ background: "rgba(255,255,255,0.6)", backdropFilter: "blur(8px)" }}>
            <div className="row gap-3">
              <span className="avatar md bg-cg">CG</span>
              <div className="col" style={{ lineHeight: 1.4 }}>
                <span style={{ fontSize: 14, fontWeight: 600 }}>"It honestly felt like texting a friend."</span>
                <span style={{ fontSize: 12, color: "var(--ink-3)" }}>Carlos G., client · Austin, TX</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// ============================================================
// DASHBOARD A
// ============================================================
function StatCard({ label, value, delta, deltaTone = "good", spark }) {
  return (
    <div className="card card-pad" style={{ flex: 1, minWidth: 0 }}>
      <div className="row between">
        <span style={{ fontSize: 12, color: "var(--ink-3)", fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.06em" }}>{label}</span>
        {delta && <span className={`chip ${deltaTone}`} style={{ fontSize: 11 }}>{delta}</span>}
      </div>
      <div className="serif" style={{ fontSize: 36, marginTop: 8, lineHeight: 1 }}>{value}</div>
      {spark && <div style={{ marginTop: 10 }}>{spark}</div>}
    </div>
  );
}

function MiniSpark({ points = [10, 12, 9, 14, 16, 13, 18], color = "var(--orange)" }) {
  const max = Math.max(...points), min = Math.min(...points);
  const w = 120, h = 32;
  const step = w / (points.length - 1);
  const path = points.map((p, i) => `${i === 0 ? "M" : "L"} ${i * step} ${h - ((p - min) / (max - min || 1)) * h}`).join(" ");
  return (
    <svg width={w} height={h}><path d={path} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
  );
}

window.HiDashA = function HiDashA() {
  return (
    <div className="row" style={{ height: "100%" }}>
      <Sidebar active="home" />
      <main style={{ flex: 1, overflow: "auto", background: "var(--bg)" }}>
        <TopBar
          title="Good afternoon, Jane."
          subtitle="Tuesday, April 28 · 3 calls scheduled · 4 submissions waiting"
          actions={
            <>
              <button className="btn ghost icon-only"><Icon name="search" /></button>
              <button className="btn ghost icon-only"><Icon name="bell" /></button>
              <button className="btn brand"><Icon name="plus" size={16} /> New intake link</button>
            </>
          }
        />
        <div style={{ padding: "24px 32px" }}>
          <div className="row gap-4" style={{ marginBottom: 24 }}>
            <StatCard label="Total submissions" value="124" delta="↑ 12 wk" deltaTone="good" spark={<MiniSpark points={[6,8,7,10,9,12,12]} />} />
            <StatCard label="Referral opportunities" value="38" delta="9 partner" deltaTone="orange" spark={<MiniSpark points={[3,4,5,4,6,7,9]} color="#2d7a7a" />} />
            <StatCard label="Avg coverage score" value="71" delta="↑ 6 pts" deltaTone="good" spark={<MiniSpark points={[64,66,65,68,70,69,71]} color="#2f8a5b" />} />
            <StatCard label="Open intake links" value="14" delta="3 expiring" deltaTone="warn" spark={<MiniSpark points={[10,11,9,12,13,14,14]} color="#c47a1a" />} />
          </div>

          <div className="row gap-4" style={{ alignItems: "stretch" }}>
            <section className="card" style={{ flex: 2, padding: 0 }}>
              <div className="row between" style={{ padding: "18px 22px 12px" }}>
                <div>
                  <h2 className="serif" style={{ fontSize: 20 }}>Recent intake links</h2>
                  <div style={{ fontSize: 12, color: "var(--ink-3)", marginTop: 2 }}>14 open · 3 expiring within 24h</div>
                </div>
                <button className="btn outline sm">View all <Icon name="chevron" size={14} /></button>
              </div>
              <table className="tbl">
                <thead><tr><th>Created</th><th>Client</th><th>Status</th><th>Channel</th><th>Token</th><th></th></tr></thead>
                <tbody>
                  {[
                    ["Apr 28 · 2:14p", "Maria González", "active", "orange", "Text", "9k2-fT3wQ"],
                    ["Apr 28 · 11:02a", "David Patel",   "completed", "good", "Email", "2pB-aL9vE"],
                    ["Apr 27 · 4:55p", "The Chen family","active", "orange", "Text", "HhX-7nMrR"],
                    ["Apr 27 · 9:30a", "Vasquez household","expired","outline","Email", "Vd4-bQz1S"],
                    ["Apr 26 · 3:18p", "Reggie Thomas",   "completed", "good", "Text", "Mk9-yT0pN"],
                  ].map(([when, who, status, tone, ch, token], i) => (
                    <tr key={i} className="hover-row">
                      <td style={{ color: "var(--ink-3)", fontSize: 13 }}>{when}</td>
                      <td style={{ fontWeight: 500, color: "var(--ink)" }}>{who}</td>
                      <td><span className={`chip ${tone} dot`}>{status}</span></td>
                      <td style={{ color: "var(--ink-3)" }}>{ch}</td>
                      <td><code style={{ fontFamily: "ui-monospace, monospace", fontSize: 12, color: "var(--ink-3)" }}>{token}</code></td>
                      <td style={{ textAlign: "right" }}>
                        <button className="btn ghost sm"><Icon name="copy" size={14} /> Copy</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>

            <section className="card card-pad" style={{ flex: 1.1 }}>
              <div className="row between" style={{ marginBottom: 14 }}>
                <h2 className="serif" style={{ fontSize: 20 }}>Recent submissions</h2>
                <button className="btn ghost sm">All</button>
              </div>
              <div className="col gap-3">
                {[
                  ["MG", "bg-mg", "Maria González", "Submitted · 2h ago", 64, "warn"],
                  ["DP", "bg-cg", "David Patel",     "In progress · step 4 of 8", null, "outline"],
                  ["CC", "bg-sf", "The Chen family", "Submitted · 6h ago", 82, "good"],
                  ["RT", "bg-dg", "Reggie Thomas",   "Submitted · yesterday", 41, "bad"],
                ].map(([ini, bg, name, st, score, tone], i) => (
                  <div key={i} className="row gap-3 tap" style={{ padding: "8px 10px", margin: "0 -10px", borderRadius: 12 }}>
                    <span className={`avatar md ${bg}`}>{ini}</span>
                    <div className="col grow" style={{ lineHeight: 1.25 }}>
                      <span style={{ fontSize: 14, fontWeight: 600 }}>{name}</span>
                      <span style={{ fontSize: 12, color: "var(--ink-3)" }}>{st}</span>
                    </div>
                    {score != null
                      ? <span className={`chip ${tone}`} style={{ fontWeight: 600 }}>{score}</span>
                      : <span className="chip outline">—</span>}
                  </div>
                ))}
              </div>
            </section>
          </div>
        </div>
      </main>
    </div>
  );
};

Object.assign(window, { HiLoginA: window.HiLoginA, HiDashA: window.HiDashA });
