/* global React */
const { useState, useEffect, useRef, useMemo } = React;

// ============================================================
// Shared sketch primitives
// ============================================================

window.SkFilters = function SkFilters() {
  return (
    <svg width="0" height="0" style={{ position: "absolute" }} aria-hidden="true">
      <defs>
        <filter id="sk-wobble">
          <feTurbulence type="fractalNoise" baseFrequency="0.022" numOctaves="2" seed="3" />
          <feDisplacementMap in="SourceGraphic" scale="1.4" />
        </filter>
        <filter id="sk-wobble-strong">
          <feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="2" seed="7" />
          <feDisplacementMap in="SourceGraphic" scale="2.2" />
        </filter>
      </defs>
    </svg>
  );
};

// Hand-drawn rectangle SVG outline for emphasized cards
window.SkRect = function SkRect({ width = 300, height = 100, stroke = "#1f2024", fill = "transparent", className = "", strokeWidth = 2.2 }) {
  const w = width, h = height;
  // Two slightly-jittered overlapping rectangles to mimic pen overshoot
  const path1 = `M 4 ${5} Q ${w*0.3} 2 ${w-6} 4 Q ${w-1} ${h*0.4} ${w-3} ${h-5} Q ${w*0.6} ${h-1} 5 ${h-3} Q 1 ${h*0.5} 4 5 Z`;
  return (
    <svg width={w} height={h} className={className} style={{ display: "block" }}>
      <path d={path1} fill={fill} stroke={stroke} strokeWidth={strokeWidth} strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
};

window.SkArrow = function SkArrow({ d, color = "#d97a3c", strokeWidth = 1.8, head = true, ...rest }) {
  // d is a path string. We add a simple arrowhead at the end.
  return (
    <svg style={{ position: "absolute", overflow: "visible", pointerEvents: "none", ...rest.style }} {...rest}>
      <defs>
        <marker id={`ah-${color.replace("#","")}`} markerWidth="10" markerHeight="10" refX="6" refY="3" orient="auto">
          <path d="M0,0 L6,3 L0,6 z" fill={color} />
        </marker>
      </defs>
      <path d={d} fill="none" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"
            markerEnd={head ? `url(#ah-${color.replace("#","")})` : undefined} />
    </svg>
  );
};

window.HatchBox = function HatchBox({ label = "image", w = "100%", h = 140, accent = false, style = {} }) {
  return (
    <div className={`sk-box tight ${accent ? "sk-hatch-accent" : "sk-hatch"}`}
         style={{ width: w, height: h, display: "flex", alignItems: "center", justifyContent: "center", ...style }}>
      <span className="hand-tight" style={{ fontSize: 13, color: "#4a4d55", letterSpacing: 0.5 }}>{label}</span>
    </div>
  );
};

window.Annot = function Annot({ children, top, left, right, bottom, rotate = -3, w = 160, arrow }) {
  return (
    <div className="sk-annot" style={{ top, left, right, bottom, width: w, transform: `rotate(${rotate}deg)` }}>
      <div>{children}</div>
      {arrow}
    </div>
  );
};

window.PhoneFrame = function PhoneFrame({ children, time = "9:41" }) {
  return (
    <div className="sk-phone">
      <div className="screen">
        <div className="sk-status-bar">
          <span>{time}</span>
          <span style={{ display: "inline-flex", gap: 4 }}>
            <span>•••</span><span>◐</span><span>▮</span>
          </span>
        </div>
        {children}
      </div>
    </div>
  );
};

window.ChromeBar = function ChromeBar({ url = "pyrainsure.app/dashboard", title = "PyraInsure" }) {
  return (
    <div className="row gap-2" style={{ padding: "10px 14px", borderBottom: "2px solid #1f2024", background: "#f3f1e8", borderRadius: "12px 12px 0 0" }}>
      <span style={{ display: "inline-flex", gap: 5 }}>
        <span style={{ width: 10, height: 10, border: "1.6px solid #1f2024", borderRadius: 50, background: "#f5dcd6" }} />
        <span style={{ width: 10, height: 10, border: "1.6px solid #1f2024", borderRadius: 50, background: "#f7e6c5" }} />
        <span style={{ width: 10, height: 10, border: "1.6px solid #1f2024", borderRadius: 50, background: "#dcecdf" }} />
      </span>
      <div className="sk-box tight" style={{ flex: 1, padding: "3px 10px", background: "#fafaf6", fontFamily: "'Patrick Hand'", fontSize: 13 }}>
        🔒 {url}
      </div>
      <span className="hand-ui" style={{ fontSize: 12, color: "#4a4d55" }}>{title}</span>
    </div>
  );
};

window.DesktopFrame = function DesktopFrame({ children, url, title, width = 1180, height = 720 }) {
  return (
    <div className="sk-box" style={{ width, padding: 0, overflow: "hidden", background: "#fafaf6" }}>
      <ChromeBar url={url} title={title} />
      <div style={{ width: "100%", height, overflow: "hidden", position: "relative" }}>
        {children}
      </div>
    </div>
  );
};

// Sidebar nav for agent surfaces
window.AgentNav = function AgentNav({ active = "dashboard" }) {
  const items = [
    { k: "dashboard", label: "Dashboard", icon: "▦" },
    { k: "links",     label: "Intake Links", icon: "🔗" },
    { k: "customers", label: "Customers",  icon: "👥" },
    { k: "summaries", label: "Summaries",  icon: "📋" },
    { k: "settings",  label: "Settings",   icon: "⚙" },
  ];
  return (
    <aside style={{ width: 200, borderRight: "2px dashed #1f2024", padding: "20px 14px", background: "#faf8ee", height: "100%" }}>
      <div className="hand-title" style={{ fontSize: 28, marginBottom: 24 }}>
        <span style={{ color: "#d97a3c" }}>△</span> PyraInsure
      </div>
      <div className="col gap-2">
        {items.map(it => (
          <div key={it.k} className="hand-ui sk-tap" style={{
            padding: "6px 10px",
            borderRadius: 8,
            background: it.k === active ? "#fde7d6" : "transparent",
            border: it.k === active ? "1.8px solid #d97a3c" : "1.8px solid transparent",
            fontSize: 16,
          }}>
            <span style={{ marginRight: 8 }}>{it.icon}</span>{it.label}
          </div>
        ))}
      </div>
      <div style={{ position: "absolute", bottom: 18, left: 14, right: 14 }} className="hand-ui muted" >
        <div className="row gap-2">
          <div style={{ width: 28, height: 28, borderRadius: 50, background: "#d8ebe9", border: "1.8px solid #1f2024", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13 }}>JM</div>
          <div className="col" style={{ lineHeight: 1.1 }}>
            <span style={{ fontSize: 14 }}>Jane Marlow</span>
            <span style={{ fontSize: 12, color: "#8a8d96" }}>Hutchins Health</span>
          </div>
        </div>
      </div>
    </aside>
  );
};

// Confetti burst
window.ConfettiBurst = function ConfettiBurst({ run = true, count = 18 }) {
  if (!run) return null;
  const colors = ["#d97a3c","#4a8c8c","#4a8c5c","#c8893a","#b85544"];
  const pieces = Array.from({ length: count }).map((_, i) => {
    const left = (Math.random() * 100).toFixed(1) + "%";
    const delay = (Math.random() * 0.5).toFixed(2) + "s";
    const rot = (Math.random() * 360).toFixed(0);
    const c = colors[i % colors.length];
    return (
      <span key={i} className="confetti-piece" style={{
        left, animationDelay: delay, background: c, transform: `rotate(${rot}deg)`,
      }} />
    );
  });
  return <div style={{ position: "absolute", inset: 0, pointerEvents: "none", overflow: "hidden" }}>{pieces}</div>;
};

// Hand-drawn ring used by gap score variation A
window.SkRing = function SkRing({ value = 72, size = 200, stroke = 14, color = "#d97a3c", trackColor = "#efece1", animate = true }) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const [v, setV] = useState(animate ? 0 : value);
  useEffect(() => {
    if (!animate) return;
    const t = setTimeout(() => setV(value), 120);
    return () => clearTimeout(t);
  }, [value, animate]);
  const offset = c - (v / 100) * c;
  return (
    <svg width={size} height={size} className="sk-wobble" style={{ display: "block" }}>
      <circle cx={size/2} cy={size/2} r={r} stroke={trackColor} strokeWidth={stroke} fill="none" />
      <circle cx={size/2} cy={size/2} r={r} stroke={color} strokeWidth={stroke} fill="none"
              strokeDasharray={c} strokeDashoffset={offset}
              strokeLinecap="round"
              transform={`rotate(-90 ${size/2} ${size/2})`}
              style={{ transition: "stroke-dashoffset 1.1s cubic-bezier(.2,.8,.2,1.05)" }} />
    </svg>
  );
};

Object.assign(window, {
  SkFilters: window.SkFilters,
  SkRect: window.SkRect,
  SkArrow: window.SkArrow,
  HatchBox: window.HatchBox,
  Annot: window.Annot,
  PhoneFrame: window.PhoneFrame,
  ChromeBar: window.ChromeBar,
  DesktopFrame: window.DesktopFrame,
  AgentNav: window.AgentNav,
  ConfettiBurst: window.ConfettiBurst,
  SkRing: window.SkRing,
});
