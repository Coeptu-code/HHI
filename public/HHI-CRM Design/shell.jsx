// Sidebar + Topbar + AppShell, plus the Login screen.

function Sidebar({ theme, active, onNav, collapsed }) {
  const items = [
    { key: 'dashboard',    label: 'Dashboard',   icon: Icons.dashboard },
    { key: 'clients',      label: 'Clients',     icon: Icons.users },
    { key: 'intake',       label: 'New Intake',  icon: Icons.userPlus },
  ];
  const W = collapsed ? 64 : parseInt(theme.metrics.sidebarWidth);
  const isDark = theme.colors.sidebar !== theme.colors.surface;

  return (
    <aside style={{
      width: W, flexShrink: 0,
      background: theme.colors.sidebar,
      borderRight: `1px solid ${theme.colors.sidebarBorder}`,
      display: 'flex', flexDirection: 'column',
      transition: 'width 220ms cubic-bezier(.2,.7,.3,1)',
      overflow: 'hidden',
    }}>
      {/* Logo */}
      <div style={{
        padding: collapsed ? '16px 12px' : '18px 18px',
        display: 'flex', alignItems: 'center', gap: 10,
        borderBottom: `1px solid ${theme.colors.sidebarBorder}`,
        height: theme.metrics.topbarHeight,
        boxSizing: 'border-box',
      }}>
        <Logo theme={theme} size={32}/>
        {!collapsed && (
          <div style={{minWidth: 0}}>
            <div style={{fontFamily: theme.fonts.display, color: isDark ? '#fff' : theme.colors.text, fontSize: 16, fontWeight: 600, lineHeight: 1.1, letterSpacing: '-0.01em', whiteSpace:'nowrap'}}>
              {theme.display.brandName}
            </div>
            <div style={{fontFamily: theme.fonts.ui, color: isDark ? 'rgba(255,255,255,0.52)' : theme.colors.textSubtle, fontSize: 10.5, letterSpacing: '0.08em', textTransform: 'uppercase', marginTop: 2, whiteSpace:'nowrap'}}>
              CRM
            </div>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav style={{padding: '12px 10px', display: 'flex', flexDirection: 'column', gap: 2, flex: 1}}>
        {!collapsed && (
          <div style={{padding:'8px 10px 4px', fontFamily: theme.fonts.ui, fontSize: 10, fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', color: isDark ? 'rgba(255,255,255,0.4)' : theme.colors.textSubtle}}>
            Workspace
          </div>
        )}
        {items.map(it => {
          const isActive = active === it.key;
          return (
            <button key={it.key} onClick={() => onNav(it.key)}
              onMouseEnter={(e) => { if (!isActive) e.currentTarget.style.background = isDark ? 'rgba(255,255,255,0.04)' : theme.colors.surface2; }}
              onMouseLeave={(e) => { if (!isActive) e.currentTarget.style.background = 'transparent'; }}
              style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: collapsed ? '10px' : '10px 12px',
                justifyContent: collapsed ? 'center' : 'flex-start',
                border: 'none', cursor: 'pointer',
                background: isActive ? theme.colors.sidebarActiveBg : 'transparent',
                color: isActive ? theme.colors.sidebarActiveText : theme.colors.sidebarText,
                fontFamily: theme.fonts.ui, fontSize: 13.5, fontWeight: isActive ? 600 : 500,
                borderRadius: theme.radius.md,
                textAlign: 'left', width: '100%',
                transition: 'background 120ms ease, color 120ms ease',
                position: 'relative',
              }}>
              <span style={{display:'inline-flex', color: isActive ? theme.colors.accent : 'currentColor'}}>{it.icon({size: 18})}</span>
              {!collapsed && <span>{it.label}</span>}
              {isActive && !collapsed && <span style={{marginLeft:'auto', color: theme.colors.accent, display:'inline-flex'}}>{Icons.dot()}</span>}
            </button>
          );
        })}
      </nav>

      {/* Footer user */}
      <div style={{padding: 10, borderTop: `1px solid ${theme.colors.sidebarBorder}`}}>
        <div style={{
          display:'flex', alignItems:'center', gap: 10,
          padding: collapsed ? 6 : '8px 10px',
          borderRadius: theme.radius.md,
        }}>
          <Avatar initials="JC" size={32} theme={theme}/>
          {!collapsed && (
            <div style={{minWidth: 0, flex: 1}}>
              <div style={{fontFamily: theme.fonts.ui, fontSize: 12.5, fontWeight: 600, color: isDark ? '#fff' : theme.colors.text, whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis'}}>Jamie Carter</div>
              <div style={{fontFamily: theme.fonts.ui, fontSize: 11, color: isDark ? 'rgba(255,255,255,0.5)' : theme.colors.textSubtle, whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis'}}>Licensed Agent</div>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}

function Topbar({ theme, title, subtitle, breadcrumbs, actions, onToggleSidebar, onGlobalSearch }) {
  return (
    <header style={{
      height: theme.metrics.topbarHeight, flexShrink: 0,
      padding: '0 24px',
      display: 'flex', alignItems: 'center', gap: 16,
      background: theme.colors.surface,
      borderBottom: `1px solid ${theme.colors.border}`,
    }}>
      <div style={{flex: 1, minWidth: 0}}>
        {breadcrumbs ? (
          <div style={{display:'flex', alignItems:'center', gap: 6, fontFamily: theme.fonts.ui, fontSize: 12, color: theme.colors.textMuted, marginBottom: 2}}>
            {breadcrumbs.map((b, i) => (
              <React.Fragment key={i}>
                {i > 0 && <span style={{color: theme.colors.textSubtle, display:'inline-flex'}}>{Icons.chevronRight({size: 12})}</span>}
                {b.onClick ? (
                  <button onClick={b.onClick} style={{background:'none', border:'none', padding: 0, cursor:'pointer', color: theme.colors.textMuted, fontFamily:'inherit', fontSize:'inherit'}}>{b.label}</button>
                ) : <span style={{color: i === breadcrumbs.length-1 ? theme.colors.text : theme.colors.textMuted}}>{b.label}</span>}
              </React.Fragment>
            ))}
          </div>
        ) : null}
        <div style={{display:'flex', alignItems:'baseline', gap: 12}}>
          <h1 style={{margin: 0, fontFamily: theme.fonts.display, fontSize: 20, fontWeight: 600, color: theme.colors.text, letterSpacing: '-0.015em'}}>{title}</h1>
          {subtitle && <span style={{fontFamily: theme.fonts.ui, fontSize: 12.5, color: theme.colors.textMuted}}>{subtitle}</span>}
        </div>
      </div>

      <div style={{width: 280}}>
        <Input theme={theme} size="sm" placeholder="Search clients, policies…" leftIcon={Icons.search} value="" onChange={() => {}} onKeyDown={(e) => { if (e.key === 'Enter') onGlobalSearch?.(e.target.value); }}/>
      </div>

      {actions}

      <button title="Notifications" style={{background:'none', border:`1px solid ${theme.colors.border}`, borderRadius: theme.radius.md, width: 36, height: 36, display:'inline-flex', alignItems:'center', justifyContent:'center', cursor:'pointer', color: theme.colors.textMuted, position:'relative'}}>
        {Icons.bell({size: 16})}
        <span style={{position:'absolute', top: 7, right: 8, width: 6, height: 6, background: theme.colors.accent, borderRadius: '50%'}}/>
      </button>
    </header>
  );
}

function AppShell({ theme, active, onNav, title, subtitle, breadcrumbs, topActions, children, onGlobalSearch }) {
  return (
    <div style={{
      display: 'flex', minHeight: '100%', height: '100%',
      background: theme.colors.bg,
      color: theme.colors.text,
      fontFamily: theme.fonts.ui,
      fontSize: theme.metrics.baseFontSize,
    }}>
      <Sidebar theme={theme} active={active} onNav={onNav}/>
      <main style={{flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', overflow: 'hidden'}}>
        <Topbar theme={theme} title={title} subtitle={subtitle} breadcrumbs={breadcrumbs} actions={topActions} onGlobalSearch={onGlobalSearch}/>
        <div style={{flex: 1, overflow: 'auto', padding: 24}}>{children}</div>
      </main>
    </div>
  );
}

// ─── Login screen ──────────────────────────────────────────────
function LoginScreen({ theme, onLogin }) {
  const [u, setU] = useState('jamie.carter');
  const [p, setP] = useState('demo-password');
  const [err, setErr] = useState(false);
  const [busy, setBusy] = useState(false);

  function submit(e) {
    e?.preventDefault();
    if (!u || !p) { setErr(true); return; }
    setBusy(true);
    setTimeout(() => { setBusy(false); onLogin(); }, 520);
  }

  const navyBg = theme.colors.sidebar !== theme.colors.surface;

  return (
    <div style={{
      display: 'grid', gridTemplateColumns: '1.05fr 1fr',
      minHeight: '100%', height: '100%',
      background: theme.colors.bg, fontFamily: theme.fonts.ui,
    }}>
      {/* Brand column */}
      <div style={{
        background: theme.colors.sidebar !== theme.colors.surface ? theme.colors.sidebar : theme.colors.brand,
        color: theme.colors.brandText,
        padding: '56px 64px',
        display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
        position: 'relative', overflow: 'hidden',
      }}>
        {/* subtle pattern */}
        <div aria-hidden="true" style={{
          position:'absolute', inset: 0, pointerEvents:'none',
          background: `radial-gradient(ellipse 600px 400px at 80% 20%, ${theme.colors.accentSoft}, transparent 70%), repeating-linear-gradient(45deg, transparent, transparent 14px, rgba(255,255,255,0.025) 14px, rgba(255,255,255,0.025) 15px)`,
          opacity: 0.9,
        }}/>
        <div style={{position:'relative', display:'flex', alignItems:'center', gap: 14}}>
          <Logo theme={theme} size={44}/>
          <div>
            <div style={{fontFamily: theme.fonts.display, fontSize: 22, fontWeight: 600, letterSpacing: '-0.01em'}}>{theme.display.brandNameFull}</div>
            <div style={{fontFamily: theme.fonts.ui, fontSize: 12, opacity: 0.65, letterSpacing: '0.06em', textTransform:'uppercase', marginTop: 4}}>CRM Portal</div>
          </div>
        </div>

        <div style={{position:'relative', maxWidth: 520}}>
          <div style={{fontFamily: theme.fonts.ui, fontSize: 11.5, color: theme.colors.accent, letterSpacing: '0.12em', textTransform:'uppercase', fontWeight: 600, marginBottom: 14}}>— {theme.display.tagline}</div>
          <h1 style={{fontFamily: theme.fonts.display, fontSize: 44, fontWeight: 500, lineHeight: 1.08, margin: 0, letterSpacing: '-0.02em'}}>
            Every client,<br/>every policy,<br/><span style={{color: theme.colors.accent, fontStyle: theme.fonts.display.includes('Instrument') ? 'italic' : 'normal'}}>in one place.</span>
          </h1>
          <p style={{fontFamily: theme.fonts.ui, fontSize: 14.5, lineHeight: 1.6, opacity: 0.75, marginTop: 20, maxWidth: 440}}>
            Sign in to manage intake, track who's turning 65, and capture policy documents from anywhere.
          </p>
        </div>

        <div style={{position:'relative', display:'flex', gap: 32, fontFamily: theme.fonts.ui, fontSize: 12, opacity: 0.65}}>
          <div><strong style={{fontWeight: 600, opacity: 1, color: theme.colors.accent}}>1,247</strong><span style={{marginLeft: 8}}>active clients</span></div>
          <div><strong style={{fontWeight: 600, opacity: 1, color: theme.colors.accent}}>98</strong><span style={{marginLeft: 8}}>turning 65 this quarter</span></div>
          <div><strong style={{fontWeight: 600, opacity: 1, color: theme.colors.accent}}>24/7</strong><span style={{marginLeft: 8}}>secure access</span></div>
        </div>
      </div>

      {/* Form column */}
      <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '48px 40px'}}>
        <form onSubmit={submit} style={{width: '100%', maxWidth: 380}}>
          <div style={{marginBottom: 28}}>
            <h2 style={{fontFamily: theme.fonts.display, fontSize: 26, fontWeight: 600, margin: 0, color: theme.colors.text, letterSpacing: '-0.015em'}}>Welcome back</h2>
            <p style={{fontFamily: theme.fonts.ui, fontSize: 13.5, color: theme.colors.textMuted, margin: '6px 0 0'}}>Sign in to the HHI CRM to continue.</p>
          </div>

          {err && (
            <div style={{
              padding: '10px 12px', marginBottom: 14,
              background: theme.colors.dangerSoft, color: theme.colors.danger,
              border: `1px solid ${theme.colors.danger}22`,
              borderRadius: theme.radius.md, fontSize: 13,
            }}>Your username and password didn't match. Please try again.</div>
          )}

          <div style={{display:'flex', flexDirection:'column', gap: 14}}>
            <div>
              <label style={{display:'block', fontFamily: theme.fonts.ui, fontSize: 12.5, fontWeight: 500, color: theme.colors.textMuted, marginBottom: 6}}>Username</label>
              <Input theme={theme} size="lg" value={u} onChange={e => setU(e.target.value)} placeholder="jamie.carter" autoFocus/>
            </div>
            <div>
              <div style={{display:'flex', justifyContent:'space-between', alignItems:'baseline', marginBottom: 6}}>
                <label style={{fontFamily: theme.fonts.ui, fontSize: 12.5, fontWeight: 500, color: theme.colors.textMuted}}>Password</label>
                <a href="#" style={{fontFamily: theme.fonts.ui, fontSize: 12, color: theme.colors.accent, textDecoration: 'none'}}>Forgot?</a>
              </div>
              <Input theme={theme} size="lg" type="password" value={p} onChange={e => setP(e.target.value)} placeholder="••••••••••"/>
            </div>

            <label style={{display:'flex', alignItems:'center', gap: 8, fontFamily: theme.fonts.ui, fontSize: 13, color: theme.colors.textMuted, userSelect:'none', cursor:'pointer', marginTop: 2}}>
              <input type="checkbox" defaultChecked style={{accentColor: theme.colors.accent, width: 14, height: 14}}/>
              Keep me signed in on this device
            </label>

            <Button theme={theme} type="submit" variant="primary" size="lg" disabled={busy} style={{marginTop: 6, width: '100%'}}>
              {busy ? 'Signing in…' : 'Sign in'}
            </Button>
          </div>

          <div style={{marginTop: 24, paddingTop: 20, borderTop: `1px solid ${theme.colors.border}`, fontFamily: theme.fonts.ui, fontSize: 12, color: theme.colors.textSubtle, textAlign: 'center'}}>
            Protected HIPAA workspace · <a href="#" style={{color: theme.colors.textMuted, textDecoration: 'none'}}>Security</a> · <a href="#" style={{color: theme.colors.textMuted, textDecoration: 'none'}}>Support</a>
          </div>
        </form>
      </div>
    </div>
  );
}

Object.assign(window, { Sidebar, Topbar, AppShell, LoginScreen });
