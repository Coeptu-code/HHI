// Dashboard screen.

function DashboardScreen({ theme, data, onNav, onOpenClient }) {
  const [range, setRange] = useState('7');

  const turning = data.turning_65.slice(0, 6);
  const recent = data.clients.slice(0, 5);

  return (
    <div style={{display:'flex', flexDirection:'column', gap: 20, maxWidth: 1320, margin: '0 auto'}}>
      {/* Hero strip */}
      <div style={{
        padding: '22px 24px',
        borderRadius: theme.radius.lg,
        background: `linear-gradient(135deg, ${theme.colors.brand} 0%, ${theme.colors.brand} 60%, ${theme.colors.accent} 180%)`,
        color: theme.colors.brandText,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        gap: 20, flexWrap: 'wrap',
        position: 'relative', overflow: 'hidden',
      }}>
        <div aria-hidden="true" style={{position:'absolute', inset: 0, background: `radial-gradient(ellipse 400px 200px at 85% 50%, ${theme.colors.accentSoft}, transparent 70%)`, pointerEvents: 'none'}}/>
        <div style={{position:'relative', minWidth: 0}}>
          <div style={{fontFamily: theme.fonts.ui, fontSize: 11.5, letterSpacing: '0.1em', textTransform:'uppercase', opacity: 0.7, marginBottom: 6, color: theme.colors.accent, fontWeight: 600}}>Thursday · April 23, 2026</div>
          <div style={{fontFamily: theme.fonts.display, fontSize: 24, fontWeight: 600, letterSpacing: '-0.015em', lineHeight: 1.2}}>Good afternoon, Jamie.</div>
          <div style={{fontFamily: theme.fonts.ui, fontSize: 13.5, opacity: 0.72, marginTop: 4}}>You have <strong style={{color: theme.colors.accent, fontWeight: 600}}>{turning.length} clients</strong> turning 65 in the next 90 days and <strong style={{color: theme.colors.accent, fontWeight: 600}}>3 documents</strong> waiting to be filed.</div>
        </div>
        <div style={{position:'relative', display:'flex', gap: 10, flexWrap:'wrap'}}>
          <Button theme={theme} variant="accent" leftIcon={Icons.userPlus} onClick={() => onNav('intake')}>New intake</Button>
          <Button theme={theme} variant="secondary" leftIcon={Icons.camera} style={{background:'rgba(255,255,255,0.12)', borderColor: 'rgba(255,255,255,0.16)', color: theme.colors.brandText}}>Scan document</Button>
        </div>
      </div>

      {/* Stat row */}
      <div style={{display:'grid', gridTemplateColumns:'repeat(4, 1fr)', gap: 14}}>
        {[
          { label: 'Active clients',    value: data.clients.length, delta: '+2 this week', tone: 'brand',   icon: Icons.users },
          { label: 'Turning 65 · 90d',  value: data.turning_65.length, delta: `${data.turning_65.filter(c => c.days_until_65 <= 30).length} in next 30d`, tone: 'accent', icon: Icons.heart },
          { label: 'New this week',     value: data.added_total, delta: 'vs 4 last week', tone: 'success', icon: Icons.activity },
          { label: 'Pending docs',      value: 3, delta: '2 handwritten', tone: 'warning', icon: Icons.fileText },
        ].map(s => (
          <Card key={s.label} theme={theme} padding="18px">
            <div style={{display:'flex', alignItems:'flex-start', justifyContent:'space-between', gap: 12}}>
              <div>
                <div style={{fontFamily: theme.fonts.ui, fontSize: 12, color: theme.colors.textMuted, fontWeight: 500}}>{s.label}</div>
                <div style={{fontFamily: theme.fonts.display, fontSize: 30, fontWeight: 600, color: theme.colors.text, lineHeight: 1, marginTop: 8, letterSpacing:'-0.02em'}}>{s.value}</div>
              </div>
              <div style={{width: 36, height: 36, borderRadius: theme.radius.md, background: s.tone === 'brand' ? theme.colors.brandSoft : s.tone === 'accent' ? theme.colors.accentSoft : s.tone === 'success' ? theme.colors.successSoft : theme.colors.warningSoft, display:'flex', alignItems:'center', justifyContent:'center', color: s.tone === 'brand' ? theme.colors.brand : s.tone === 'accent' ? theme.colors.accentText : s.tone === 'success' ? theme.colors.success : theme.colors.warning}}>
                {s.icon({size: 16})}
              </div>
            </div>
            <div style={{fontFamily: theme.fonts.ui, fontSize: 11.5, color: theme.colors.textSubtle, marginTop: 10}}>{s.delta}</div>
          </Card>
        ))}
      </div>

      {/* Main grid */}
      <div style={{display:'grid', gridTemplateColumns:'1.4fr 1fr', gap: 14}}>
        {/* Clients added chart */}
        <Card theme={theme}>
          <div style={{display:'flex', alignItems:'flex-start', justifyContent:'space-between', gap: 12, marginBottom: 22}}>
            <div>
              <div style={{fontFamily: theme.fonts.ui, fontSize: 11.5, color: theme.colors.textMuted, letterSpacing: '0.06em', textTransform:'uppercase', fontWeight: 600}}>Clients added</div>
              <div style={{fontFamily: theme.fonts.display, fontSize: 20, fontWeight: 600, marginTop: 4, letterSpacing:'-0.01em'}}>Last 7 days</div>
            </div>
            <div style={{display:'flex', gap: 4, padding: 3, background: theme.colors.surface2, borderRadius: theme.radius.pill, border: `1px solid ${theme.colors.border}`}}>
              {['7','30','90'].map(r => (
                <button key={r} onClick={() => setRange(r)} style={{
                  padding: '5px 12px', border: 'none', cursor: 'pointer',
                  background: range === r ? theme.colors.surface : 'transparent',
                  color: range === r ? theme.colors.text : theme.colors.textMuted,
                  fontFamily: theme.fonts.ui, fontSize: 12, fontWeight: 600,
                  borderRadius: theme.radius.pill,
                  boxShadow: range === r ? theme.shadow.sm : 'none',
                }}>{r}d</button>
              ))}
            </div>
          </div>

          <div style={{display:'flex', alignItems:'stretch', gap: 14, height: 220, padding: '0 4px'}}>
            {data.added_series.map((p, i) => (
              <div key={i} style={{flex: 1, display:'flex', flexDirection:'column', alignItems:'center', gap: 6, minWidth: 0}}>
                <div style={{fontFamily: theme.fonts.mono, fontSize: 11, color: theme.colors.textMuted, fontWeight: 500, flexShrink: 0}}>{p.count}</div>
                <div style={{width: '100%', flex: 1, display:'flex', alignItems:'flex-end', minHeight: 0}}>
                  <div style={{
                    width: '100%', height: `${Math.max(p.pct, 4)}%`, minHeight: 3,
                    background: i === data.added_series.length - 1 ? theme.colors.accent : theme.colors.brand,
                    borderRadius: `${parseInt(theme.radius.sm)}px ${parseInt(theme.radius.sm)}px 2px 2px`,
                    opacity: p.count === 0 ? 0.15 : 1,
                    transition: 'height 600ms cubic-bezier(.2,.7,.3,1)',
                  }}/>
                </div>
                <div style={{fontFamily: theme.fonts.ui, fontSize: 11, color: theme.colors.textMuted, fontWeight: 500, flexShrink: 0, marginTop: 4}}>{p.label}</div>
                <div style={{fontFamily: theme.fonts.mono, fontSize: 10, color: theme.colors.textSubtle, flexShrink: 0}}>{p.sublabel}</div>
              </div>
            ))}
          </div>

          <div style={{marginTop: 20, paddingTop: 16, borderTop: `1px solid ${theme.colors.border}`, display:'flex', justifyContent:'space-between', alignItems:'center'}}>
            <div style={{fontFamily: theme.fonts.ui, fontSize: 12.5, color: theme.colors.textMuted}}>
              Total: <strong style={{color: theme.colors.text, fontWeight: 600}}>{data.added_total} clients</strong> added · peak on Wednesday
            </div>
            <button onClick={() => onNav('clients')} style={{background:'none', border:'none', cursor:'pointer', color: theme.colors.accent, fontFamily: theme.fonts.ui, fontSize: 12.5, fontWeight: 600, display:'inline-flex', alignItems:'center', gap: 4}}>
              View all {Icons.chevronRight({size: 12})}
            </button>
          </div>
        </Card>

        {/* Turning 65 */}
        <Card theme={theme} padding="0">
          <div style={{padding: '20px 22px 14px', display:'flex', alignItems:'flex-start', justifyContent:'space-between'}}>
            <div>
              <div style={{fontFamily: theme.fonts.ui, fontSize: 11.5, color: theme.colors.textMuted, letterSpacing: '0.06em', textTransform:'uppercase', fontWeight: 600}}>Priority</div>
              <div style={{fontFamily: theme.fonts.display, fontSize: 20, fontWeight: 600, marginTop: 4, letterSpacing:'-0.01em'}}>Turning 65</div>
            </div>
            <Badge theme={theme} tone="accent">Next 90 days</Badge>
          </div>
          <div style={{padding: '0 10px 10px'}}>
            {turning.map((c, i) => (
              <button key={c.id} onClick={() => onOpenClient(c.id)} style={{
                display:'flex', alignItems:'center', gap: 12, width: '100%',
                padding: '10px 12px', background: 'transparent', border: 'none', cursor: 'pointer',
                borderRadius: theme.radius.md, textAlign:'left',
                transition: 'background 120ms',
              }}
              onMouseEnter={e => e.currentTarget.style.background = theme.colors.surface2}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                <Avatar initials={c.initials} size={34} theme={theme}/>
                <div style={{flex: 1, minWidth: 0}}>
                  <div style={{fontFamily: theme.fonts.ui, fontSize: 13.5, fontWeight: 600, color: theme.colors.text, whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis'}}>{c.full_name}</div>
                  <div style={{fontFamily: theme.fonts.ui, fontSize: 11.5, color: theme.colors.textMuted, display:'flex', gap: 6}}>
                    <span>{c.turns_65_display}</span>
                    <span style={{color: theme.colors.textSubtle}}>·</span>
                    <span>{c.phone}</span>
                  </div>
                </div>
                <Badge theme={theme} tone={c.days_until_65 <= 14 ? 'danger' : c.days_until_65 <= 30 ? 'warning' : 'neutral'}>
                  {c.days_until_65 === 0 ? 'Today' : `${c.days_until_65}d`}
                </Badge>
              </button>
            ))}
          </div>
          <div style={{padding: '12px 22px', borderTop: `1px solid ${theme.colors.border}`, display:'flex', justifyContent:'space-between', alignItems:'center'}}>
            <span style={{fontFamily: theme.fonts.ui, fontSize: 12, color: theme.colors.textMuted}}>Showing {turning.length} of {data.turning_65.length}</span>
            <button onClick={() => onNav('clients')} style={{background:'none', border:'none', cursor:'pointer', color: theme.colors.accent, fontFamily: theme.fonts.ui, fontSize: 12.5, fontWeight: 600, display:'inline-flex', alignItems:'center', gap: 4}}>
              View all {Icons.chevronRight({size: 12})}
            </button>
          </div>
        </Card>
      </div>

      {/* Lower grid */}
      <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap: 14}}>
        <Card theme={theme}>
          <div style={{display:'flex', alignItems:'flex-start', justifyContent:'space-between', marginBottom: 14}}>
            <div>
              <div style={{fontFamily: theme.fonts.ui, fontSize: 11.5, color: theme.colors.textMuted, letterSpacing: '0.06em', textTransform:'uppercase', fontWeight: 600}}>Recently added</div>
              <div style={{fontFamily: theme.fonts.display, fontSize: 18, fontWeight: 600, marginTop: 4}}>New clients</div>
            </div>
          </div>
          <div style={{display:'flex', flexDirection:'column'}}>
            {recent.map((c, i) => (
              <button key={c.id} onClick={() => onOpenClient(c.id)}
                onMouseEnter={e => e.currentTarget.style.background = theme.colors.surface2}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                style={{
                display:'grid', gridTemplateColumns: '1fr auto auto', alignItems:'center', gap: 12,
                padding: '10px 0', borderTop: i === 0 ? 'none' : `1px solid ${theme.colors.border}`,
                background: 'transparent', border: 'none', cursor:'pointer', textAlign:'left',
                transition: 'background 120ms', width: '100%',
              }}>
                <div style={{display:'flex', gap: 10, alignItems:'center', minWidth: 0}}>
                  <Avatar initials={c.initials} size={30} theme={theme}/>
                  <div style={{minWidth: 0}}>
                    <div style={{fontFamily: theme.fonts.ui, fontSize: 13, fontWeight: 600, color: theme.colors.text}}>{c.full_name}</div>
                    <div style={{fontFamily: theme.fonts.ui, fontSize: 11.5, color: theme.colors.textMuted}}>{c.city}, {c.state} · age {c.age}</div>
                  </div>
                </div>
                <span style={{fontFamily: theme.fonts.mono, fontSize: 11, color: theme.colors.textMuted}}>{c.created_display}</span>
                <span style={{color: theme.colors.textSubtle, display:'inline-flex'}}>{Icons.chevronRight({size: 14})}</span>
              </button>
            ))}
          </div>
        </Card>

        <Card theme={theme}>
          <div style={{marginBottom: 14}}>
            <div style={{fontFamily: theme.fonts.ui, fontSize: 11.5, color: theme.colors.textMuted, letterSpacing: '0.06em', textTransform:'uppercase', fontWeight: 600}}>To do</div>
            <div style={{fontFamily: theme.fonts.display, fontSize: 18, fontWeight: 600, marginTop: 4}}>Needs attention</div>
          </div>
          <div style={{display:'flex', flexDirection:'column', gap: 8}}>
            {[
              { icon: Icons.fileText, tone: 'warning', title: '2 handwritten notes to review', sub: 'Dolores Fitzgerald · Evelyn Rodriguez' },
              { icon: Icons.heart, tone: 'danger', title: 'Harold Washington turns 65 in 11 days', sub: 'No policy on file yet' },
              { icon: Icons.phone, tone: 'accent', title: 'Follow up with Linda Brooks', sub: 'Left voicemail 8 days ago' },
              { icon: Icons.paperclip, tone: 'brand', title: 'Patricia Nguyen — missing Part B card', sub: 'Requested 4/17' },
            ].map((t, i) => {
              const toneColor = {
                warning: theme.colors.warning, danger: theme.colors.danger,
                accent: theme.colors.accentText, brand: theme.colors.brand,
              }[t.tone];
              const toneBg = {
                warning: theme.colors.warningSoft, danger: theme.colors.dangerSoft,
                accent: theme.colors.accentSoft, brand: theme.colors.brandSoft,
              }[t.tone];
              return (
                <div key={i} style={{display:'flex', alignItems:'center', gap: 12, padding: '10px 12px', background: theme.colors.surface2, borderRadius: theme.radius.md, border: `1px solid ${theme.colors.border}`}}>
                  <div style={{width: 32, height: 32, borderRadius: theme.radius.md, background: toneBg, color: toneColor, display:'flex', alignItems:'center', justifyContent:'center', flexShrink: 0}}>{t.icon({size: 14})}</div>
                  <div style={{flex: 1, minWidth: 0}}>
                    <div style={{fontFamily: theme.fonts.ui, fontSize: 13, fontWeight: 600, color: theme.colors.text}}>{t.title}</div>
                    <div style={{fontFamily: theme.fonts.ui, fontSize: 11.5, color: theme.colors.textMuted, marginTop: 2}}>{t.sub}</div>
                  </div>
                  <button style={{background:'none', border:'none', cursor:'pointer', color: theme.colors.textSubtle, padding: 6, borderRadius: theme.radius.sm, display:'inline-flex'}}>{Icons.chevronRight({size: 14})}</button>
                </div>
              );
            })}
          </div>
        </Card>
      </div>
    </div>
  );
}

Object.assign(window, { DashboardScreen });
