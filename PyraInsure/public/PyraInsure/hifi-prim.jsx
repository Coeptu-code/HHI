/* global React */
const { useState: useS, useEffect: useE, useRef: useR } = React;

// ── Icons (simple inline SVGs, stroke-based) ─────────
window.Icon = function Icon({ name, size = 18, stroke = 1.6, color = "currentColor" }) {
  const props = { width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: color, strokeWidth: stroke, strokeLinecap: "round", strokeLinejoin: "round" };
  const paths = {
    home:    <><path d="M3 11l9-7 9 7v9a2 2 0 0 1-2 2h-4v-7H9v7H5a2 2 0 0 1-2-2v-9z"/></>,
    link:    <><path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1"/><path d="M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1"/></>,
    users:   <><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13A4 4 0 0 1 16 11"/></>,
    notes:   <><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M8 13h8M8 17h6"/></>,
    settings:<><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></>,
    search:  <><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></>,
    plus:    <><path d="M12 5v14M5 12h14"/></>,
    arrow:   <><path d="M5 12h14M13 5l7 7-7 7"/></>,
    arrowL:  <><path d="M19 12H5M11 5l-7 7 7 7"/></>,
    check:   <><path d="m20 6-11 11-5-5"/></>,
    copy:    <><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></>,
    chevron: <><path d="m9 18 6-6-6-6"/></>,
    phone:   <><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></>,
    mail:    <><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 6-10 7L2 6"/></>,
    bell:    <><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10 21a2 2 0 0 0 4 0"/></>,
    calendar:<><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></>,
    sparkles:<><path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8"/></>,
    shield:  <><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></>,
    pill:    <><rect x="2" y="9" width="20" height="6" rx="3" transform="rotate(-45 12 12)"/><path d="m8.5 8.5 7 7"/></>,
    smile:   <><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" x2="9.01" y1="9" y2="9"/><line x1="15" x2="15.01" y1="9" y2="9"/></>,
    play:    <><path d="m6 4 14 8-14 8z"/></>,
    edit:    <><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></>,
    send:    <><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></>,
    google:  <><path d="M21.35 11.1H12.18v3.83h5.27c-.51 2.46-2.61 3.78-5.27 3.78-3.21 0-5.83-2.62-5.83-5.83s2.62-5.83 5.83-5.83c1.4 0 2.66.5 3.65 1.32l2.78-2.78A9.84 9.84 0 0 0 12.18 2C6.66 2 2.18 6.48 2.18 12s4.48 10 10 10c5 0 9.55-3.64 9.55-10 0-.6-.06-1.16-.16-1.7z"/></>,
    apple:   <><path d="M12.95 8.7c-.66 0-1.7-.74-2.78-.71-1.43.02-2.74.83-3.47 2.11-1.48 2.57-.38 6.36 1.07 8.45.71 1.02 1.55 2.16 2.65 2.12 1.06-.04 1.46-.69 2.74-.69s1.65.69 2.78.67c1.15-.02 1.88-1.04 2.58-2.06.81-1.18 1.15-2.33 1.17-2.39-.03-.01-2.24-.86-2.27-3.41-.02-2.13 1.74-3.16 1.82-3.21-1-1.46-2.55-1.62-3.09-1.66-1.4-.11-2.58.78-3.2.78zM15.13 5.2c.58-.7 1.06-1.7.93-2.7-.86.04-1.91.59-2.51 1.29-.54.62-1.02 1.62-.89 2.59.95.07 1.92-.49 2.47-1.18z"/></>,
    eye:     <><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/></>,
    grid:    <><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></>,
    target:  <><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></>,
    info:    <><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></>,
    star:    <><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></>,
    car:     <><path d="M14 16H9m10 0h3v-3.15a1 1 0 0 0-.84-.99L16 11l-2.7-3.6a1 1 0 0 0-.8-.4H5.24a2 2 0 0 0-1.8 1.1l-.8 1.63A6 6 0 0 0 2 12.42V15a1 1 0 0 0 1 1h2"/><circle cx="6.5" cy="16.5" r="2.5"/><circle cx="16.5" cy="16.5" r="2.5"/></>,
    heart:   <><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></>,
    house:   <><path d="M3 9.5 12 2l9 7.5V21a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1V9.5Z"/></>,
    umbrella:<><path d="M12 2v2M3 14a9 9 0 0 1 18 0M12 14v6a2 2 0 0 1-4 0"/></>,
    clock:   <><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></>,
  };
  return <svg {...props}>{paths[name] || null}</svg>;
};

// ── Logo ─────────
window.Logo = function Logo({ size = 20, mark = true, label = "PyraInsure", variant = "real" }) {
  if (variant === "real") {
    const h = size + 10;
    return mark
      ? <img src="pyrainsure-logo-orange-transparent.png" alt="PyraInsure" style={{ height: h, width: "auto", display: "block" }} />
      : <img src="pyrainsure-mark-orange.png" alt="PyraInsure" style={{ height: h, width: "auto", display: "block" }} />;
  }
  return (
    <span className="logo" style={{ fontSize: size + 4 }}>
      {mark && <span className="mark" style={{ width: size + 6, height: size + 6, fontSize: size - 4 }}>P</span>}
      <span>{label}</span>
    </span>
  );
};

// ── Confetti ─────────
window.Confetti = function Confetti({ run = true, count = 28 }) {
  if (!run) return null;
  const colors = ["#e57244","#2d7a7a","#c47a1a","#2f8a5b","#d35a2e","#226363"];
  return (
    <div style={{ position: "absolute", inset: 0, pointerEvents: "none", overflow: "hidden", zIndex: 10 }}>
      {Array.from({ length: count }).map((_, i) => {
        const left = (Math.random() * 100).toFixed(1) + "%";
        const delay = (Math.random() * 0.6).toFixed(2) + "s";
        const rot = (Math.random() * 360).toFixed(0);
        const c = colors[i % colors.length];
        return <span key={i} className="confetti-piece" style={{ left, top: 0, animationDelay: delay, background: c, transform: `rotate(${rot}deg)` }} />;
      })}
    </div>
  );
};

// ── Score ring ─────────
window.Ring = function Ring({ value = 64, size = 220, stroke = 14, color = "var(--orange)", track = "var(--bg-2)", animate = true }) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const [v, setV] = useS(animate ? 0 : value);
  useE(() => {
    if (!animate) return;
    const t = setTimeout(() => setV(value), 150);
    return () => clearTimeout(t);
  }, [value, animate]);
  const offset = c - (v / 100) * c;
  return (
    <svg width={size} height={size} style={{ display: "block" }}>
      <circle cx={size/2} cy={size/2} r={r} stroke={track} strokeWidth={stroke} fill="none" />
      <circle cx={size/2} cy={size/2} r={r} stroke={color} strokeWidth={stroke} fill="none"
              strokeDasharray={c} strokeDashoffset={offset}
              strokeLinecap="round"
              transform={`rotate(-90 ${size/2} ${size/2})`}
              style={{ transition: "stroke-dashoffset 1.2s cubic-bezier(.2,.8,.2,1.0)" }} />
    </svg>
  );
};

// ── Phone frame ─────────
window.Phone = function Phone({ children, time = "9:41" }) {
  return (
    <div className="phone">
      <div className="screen">
        <div className="notch" />
        <div className="status-bar">
          <span>{time}</span>
          <span style={{ display: "inline-flex", gap: 5, alignItems: "center" }}>
            <svg width="16" height="11" viewBox="0 0 16 11" fill="currentColor"><path d="M1 7h2v3H1zM5 5h2v5H5zM9 3h2v7H9zM13 1h2v9h-2z"/></svg>
            <svg width="14" height="10" viewBox="0 0 14 10" fill="none" stroke="currentColor" strokeWidth="1.4"><path d="M1 4a8 8 0 0 1 12 0M3 6a5 5 0 0 1 8 0M6 8a2 2 0 0 1 2 0"/></svg>
            <svg width="22" height="11" viewBox="0 0 22 11" fill="none"><rect x=".5" y=".5" width="18" height="10" rx="2.5" stroke="currentColor"/><rect x="2" y="2" width="14" height="7" rx="1" fill="currentColor"/><rect x="19" y="3.5" width="2" height="4" rx="1" fill="currentColor"/></svg>
          </span>
        </div>
        {children}
      </div>
    </div>
  );
};

// ── Browser frame ─────────
window.Browser = function Browser({ url = "pyrainsure.app", title = "PyraInsure", children, width = 1200, height = 760 }) {
  return (
    <div className="frame-shell" style={{ width }}>
      <div className="chrome">
        <span className="lights">
          <span style={{ background: "#f6685e" }} /><span style={{ background: "#f6c344" }} /><span style={{ background: "#62c554" }} />
        </span>
        <span className="url">🔒 {url}</span>
        <span style={{ fontSize: 12, color: "var(--ink-3)" }}>{title}</span>
      </div>
      <div style={{ height, overflow: "hidden", position: "relative", background: "var(--bg)" }}>
        {children}
      </div>
    </div>
  );
};

// ── Sidebar ─────────
window.Sidebar = function Sidebar({ active = "home" }) {
  const items = [
    { k: "home", label: "Dashboard", icon: "home" },
    { k: "links", label: "Intake links", icon: "link" },
    { k: "customers", label: "Customers", icon: "users" },
    { k: "summaries", label: "Summaries", icon: "notes" },
    { k: "settings", label: "Settings", icon: "settings" },
  ];
  return (
    <aside className="sidebar">
      <div style={{ padding: "0 8px 28px" }}><Logo size={40} /></div>
      <div className="col gap-1" style={{ flex: 1 }}>
        {items.map(it => (
          <div key={it.k} className={`nav-item ${active === it.k ? "active" : ""}`}>
            <Icon name={it.icon} size={17} />
            <span>{it.label}</span>
          </div>
        ))}
      </div>
      <div className="card card-pad-sm" style={{ background: "var(--orange-tint)", border: "1px solid var(--orange-soft)" }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: "var(--orange-2)" }}>Tip of the day</div>
        <div style={{ fontSize: 12, color: "var(--ink-3)", marginTop: 4, lineHeight: 1.4 }}>Use a preset to send 5 intakes in 30 seconds.</div>
      </div>
      <div className="row gap-3" style={{ marginTop: 14, padding: "8px 8px 0", borderTop: "1px solid var(--line)", paddingTop: 14 }}>
        <span className="avatar md bg-jm">JM</span>
        <div className="col" style={{ lineHeight: 1.2, minWidth: 0 }}>
          <span style={{ fontSize: 13, fontWeight: 600 }}>Jane Marlow</span>
          <span style={{ fontSize: 11, color: "var(--ink-3)" }}>Hutchins Health · Agent</span>
        </div>
      </div>
    </aside>
  );
};

// ── Top bar (page header) ─────────
window.TopBar = function TopBar({ title, subtitle, actions }) {
  return (
    <div className="row between" style={{ padding: "20px 32px", borderBottom: "1px solid var(--line)", background: "var(--bg)" }}>
      <div>
        <h1 className="serif" style={{ fontSize: 28, lineHeight: 1.1 }}>{title}</h1>
        {subtitle && <div style={{ fontSize: 13, color: "var(--ink-3)", marginTop: 4 }}>{subtitle}</div>}
      </div>
      {actions && <div className="row gap-3">{actions}</div>}
    </div>
  );
};

Object.assign(window, {
  Icon: window.Icon, Logo: window.Logo, Confetti: window.Confetti, Ring: window.Ring,
  Phone: window.Phone, Browser: window.Browser, Sidebar: window.Sidebar, TopBar: window.TopBar,
});
