// Shared shell pieces: Sidebar, Topbar, Avatar, Badge, Button, Input,
// Card, Toast, Modal. Each reads the `theme` token object.
//
// No "styles" object to avoid global name collisions; inline styles only.

const { useState, useEffect, useRef, useMemo, useCallback } = React;

// ── Avatar: initials on a themed square ─────────────────────────
function Avatar({ name, initials, size = 36, theme, style }) {
  const init = initials || (name || '??').split(/\s+/).map(p => p[0]).slice(0,2).join('').toUpperCase();
  return (
    <div style={{
      width: size, height: size, flexShrink: 0,
      background: theme.colors.avatarBg,
      color: theme.colors.avatarText,
      borderRadius: theme.radius.md,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontFamily: theme.fonts.ui,
      fontSize: size * 0.36, fontWeight: 600, letterSpacing: '0.02em',
      ...style,
    }}>{init}</div>
  );
}

// ── Button ─────────────────────────────────────────────────────
function Button({ children, variant = 'primary', size = 'md', theme, leftIcon, rightIcon, onClick, type, disabled, style, title, as, href }) {
  const [hover, setHover] = useState(false);
  const [active, setActive] = useState(false);
  const sizes = {
    sm: { height: 30, padX: 10, font: 12.5, gap: 6, iconSize: 14 },
    md: { height: 38, padX: 14, font: 13.5, gap: 8, iconSize: 16 },
    lg: { height: 46, padX: 18, font: 14.5, gap: 10, iconSize: 18 },
  }[size];
  const variants = {
    primary: {
      bg: theme.colors.brand, color: theme.colors.brandText,
      border: theme.colors.brand,
      hoverBg: theme.colors.accent, hoverColor: theme.colors.brandText,
    },
    accent: {
      bg: theme.colors.accent, color: '#fff',
      border: theme.colors.accent,
      hoverBg: theme.colors.accentText, hoverColor: '#fff',
    },
    secondary: {
      bg: theme.colors.surface, color: theme.colors.text,
      border: theme.colors.border,
      hoverBg: theme.colors.surface2, hoverColor: theme.colors.text,
    },
    ghost: {
      bg: 'transparent', color: theme.colors.textMuted,
      border: 'transparent',
      hoverBg: theme.colors.brandSoft, hoverColor: theme.colors.text,
    },
    danger: {
      bg: 'transparent', color: theme.colors.danger,
      border: theme.colors.border,
      hoverBg: theme.colors.dangerSoft, hoverColor: theme.colors.danger,
    },
  }[variant];
  const Comp = as || 'button';
  return (
    <Comp type={type || (as ? undefined : 'button')} onClick={onClick} title={title} href={href}
      disabled={disabled}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => { setHover(false); setActive(false); }}
      onMouseDown={() => setActive(true)}
      onMouseUp={() => setActive(false)}
      style={{
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: sizes.gap,
        height: sizes.height, padding: `0 ${sizes.padX}px`,
        fontFamily: theme.fonts.ui, fontSize: sizes.font, fontWeight: 550,
        borderRadius: theme.radius.md,
        background: hover && !disabled ? variants.hoverBg : variants.bg,
        color: hover && !disabled ? variants.hoverColor : variants.color,
        border: `1px solid ${variants.border === 'transparent' ? 'transparent' : (hover ? variants.hoverBg : variants.border)}`,
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.55 : 1,
        transition: 'background 140ms ease, color 140ms ease, border-color 140ms ease, transform 80ms ease',
        transform: active ? 'translateY(1px)' : 'none',
        whiteSpace: 'nowrap', textDecoration: 'none',
        ...style,
      }}>
      {leftIcon && <span style={{display:'inline-flex'}}>{leftIcon({size: sizes.iconSize})}</span>}
      {children}
      {rightIcon && <span style={{display:'inline-flex'}}>{rightIcon({size: sizes.iconSize})}</span>}
    </Comp>
  );
}

// ── Input ──────────────────────────────────────────────────────
function Input({ value, onChange, placeholder, type = 'text', theme, leftIcon, rightAdornment, style, onKeyDown, autoFocus, id, name, disabled, size = 'md' }) {
  const [focus, setFocus] = useState(false);
  const H = size === 'lg' ? 46 : size === 'sm' ? 32 : 40;
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 8,
      height: H, padding: '0 12px',
      background: theme.colors.surface,
      border: `1px solid ${focus ? theme.colors.accent : theme.colors.border}`,
      boxShadow: focus ? `0 0 0 3px ${theme.colors.accentSoft}` : 'none',
      borderRadius: theme.radius.md,
      fontFamily: theme.fonts.ui,
      transition: 'border-color 120ms ease, box-shadow 120ms ease',
      ...style,
    }}>
      {leftIcon && <span style={{display:'inline-flex', color: theme.colors.textSubtle}}>{leftIcon({size: 16})}</span>}
      <input id={id} name={name} type={type} value={value} onChange={onChange} placeholder={placeholder}
        onFocus={() => setFocus(true)} onBlur={() => setFocus(false)}
        autoFocus={autoFocus} disabled={disabled} onKeyDown={onKeyDown}
        style={{
          flex: 1, minWidth: 0,
          border: 'none', outline: 'none', background: 'transparent',
          fontFamily: 'inherit', fontSize: 14, color: theme.colors.text,
          padding: 0,
        }}/>
      {rightAdornment}
    </div>
  );
}

// ── Textarea ───────────────────────────────────────────────────
function Textarea({ value, onChange, placeholder, theme, rows = 4, style, name, id }) {
  const [focus, setFocus] = useState(false);
  return (
    <textarea id={id} name={name} value={value} onChange={onChange} placeholder={placeholder} rows={rows}
      onFocus={() => setFocus(true)} onBlur={() => setFocus(false)}
      style={{
        width: '100%', resize: 'vertical',
        padding: '10px 12px', boxSizing: 'border-box',
        background: theme.colors.surface,
        border: `1px solid ${focus ? theme.colors.accent : theme.colors.border}`,
        boxShadow: focus ? `0 0 0 3px ${theme.colors.accentSoft}` : 'none',
        borderRadius: theme.radius.md,
        fontFamily: theme.fonts.ui, fontSize: 14, color: theme.colors.text,
        outline: 'none',
        transition: 'border-color 120ms ease, box-shadow 120ms ease',
        ...style,
      }}/>
  );
}

// ── Select ──────────────────────────────────────────────────────
function Select({ value, onChange, options, theme, style, size = 'md' }) {
  const [focus, setFocus] = useState(false);
  const H = size === 'sm' ? 32 : 40;
  return (
    <div style={{position: 'relative', ...style}}>
      <select value={value} onChange={onChange}
        onFocus={() => setFocus(true)} onBlur={() => setFocus(false)}
        style={{
          width: '100%', height: H, padding: '0 34px 0 12px',
          appearance: 'none', WebkitAppearance: 'none', MozAppearance: 'none',
          background: theme.colors.surface,
          border: `1px solid ${focus ? theme.colors.accent : theme.colors.border}`,
          boxShadow: focus ? `0 0 0 3px ${theme.colors.accentSoft}` : 'none',
          borderRadius: theme.radius.md,
          fontFamily: theme.fonts.ui, fontSize: 14, color: theme.colors.text,
          outline: 'none', cursor: 'pointer',
          transition: 'border-color 120ms ease, box-shadow 120ms ease',
        }}>
        {options.map(o => (
          typeof o === 'string'
            ? <option key={o} value={o}>{o}</option>
            : <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
      <span style={{position:'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', pointerEvents:'none', color: theme.colors.textSubtle, display:'inline-flex'}}>
        {Icons.chevronDown({size: 14})}
      </span>
    </div>
  );
}

// ── Badge / Pill ────────────────────────────────────────────────
function Badge({ children, tone = 'neutral', theme, style, leftIcon }) {
  const tones = {
    neutral: { bg: theme.colors.surface2, color: theme.colors.textMuted, border: theme.colors.border },
    brand:   { bg: theme.colors.brandSoft, color: theme.colors.brand, border: 'transparent' },
    accent:  { bg: theme.colors.accentSoft, color: theme.colors.accentText, border: 'transparent' },
    success: { bg: theme.colors.successSoft, color: theme.colors.success, border: 'transparent' },
    warning: { bg: theme.colors.warningSoft, color: theme.colors.warning, border: 'transparent' },
    danger:  { bg: theme.colors.dangerSoft, color: theme.colors.danger, border: 'transparent' },
  }[tone];
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      padding: '3px 9px',
      fontFamily: theme.fonts.ui, fontSize: 11.5, fontWeight: 550,
      color: tones.color, background: tones.bg,
      border: `1px solid ${tones.border}`,
      borderRadius: theme.radius.pill,
      letterSpacing: '0.01em',
      ...style,
    }}>
      {leftIcon && <span style={{display:'inline-flex'}}>{leftIcon({size: 11})}</span>}
      {children}
    </span>
  );
}

// ── Card ────────────────────────────────────────────────────────
function Card({ children, theme, style, padding }) {
  return (
    <div style={{
      background: theme.colors.surface,
      border: `1px solid ${theme.colors.border}`,
      borderRadius: theme.radius.lg,
      boxShadow: theme.shadow.card,
      padding: padding ?? theme.metrics.cardPad,
      ...style,
    }}>{children}</div>
  );
}

// ── Toast ──────────────────────────────────────────────────────
function Toast({ message, tone = 'success', theme, visible }) {
  if (!visible) return null;
  return (
    <div style={{
      position: 'absolute', left: '50%', bottom: 24, transform: 'translateX(-50%)',
      padding: '10px 16px', display: 'flex', alignItems: 'center', gap: 10,
      background: theme.colors.text, color: theme.colors.surface,
      borderRadius: theme.radius.pill,
      fontFamily: theme.fonts.ui, fontSize: 13, fontWeight: 500,
      boxShadow: theme.shadow.lg, zIndex: 50,
      animation: 'hhi-toast-in 260ms cubic-bezier(.2,.7,.3,1)',
    }}>
      <span style={{color: tone === 'success' ? '#8ee3b4' : '#ffd38a', display: 'inline-flex'}}>{Icons.check({size: 14})}</span>
      {message}
    </div>
  );
}

Object.assign(window, { Avatar, Button, Input, Textarea, Select, Badge, Card, Toast });
