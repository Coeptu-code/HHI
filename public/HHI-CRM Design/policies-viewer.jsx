// Policies tab + Document Viewer screen.

// ── Shared editorial hairline divider ────────────────────────
function Hairline({ theme, label, style }) {
  return (
    <div style={{display:'flex', alignItems:'center', gap: 12, ...style}}>
      <div style={{flex: 1, height: 1, background: theme.colors.accent, opacity: 0.35}}/>
      {label && <span style={{fontFamily: theme.fonts.ui, fontSize: 10.5, letterSpacing: '0.14em', textTransform:'uppercase', color: theme.colors.accentText || theme.colors.accent, fontWeight: 600}}>{label}</span>}
      {label && <div style={{flex: 1, height: 1, background: theme.colors.accent, opacity: 0.35}}/>}
    </div>
  );
}

// ── Striped page placeholder (for scan previews) ─────────────
function PagePlaceholder({ width = 220, height = 280, theme, n, title, kind = 'policy', style, compact }) {
  const isHW = kind === 'handwritten';
  // Handwritten = warm cream page with "ink" scribble stripes
  const bg = isHW ? '#fbf5e6' : theme.colors.surface;
  const stripe = isHW ? 'rgba(91, 60, 27, 0.14)' : 'rgba(20, 37, 74, 0.07)';
  const stripeColor2 = isHW ? 'rgba(91, 60, 27, 0.07)' : 'rgba(20, 37, 74, 0.03)';
  return (
    <div style={{
      width, height, position: 'relative',
      background: bg,
      border: `1px solid ${theme.colors.borderStrong}`,
      borderRadius: theme.radius.sm,
      boxShadow: '0 1px 0 rgba(17,26,46,0.04), 0 6px 18px rgba(17,26,46,0.06)',
      overflow:'hidden', flexShrink: 0,
      ...style,
    }}>
      {/* paper "content" stripes */}
      <div aria-hidden="true" style={{
        position: 'absolute', inset: isHW ? '18% 14% 18% 14%' : '14% 12% 14% 12%',
        background: isHW
          ? `repeating-linear-gradient(8deg, transparent 0 6px, ${stripe} 6px 7px, transparent 7px 14px, ${stripe} 14px 15px, transparent 15px 26px, ${stripe} 26px 27px, transparent 27px 34px)`
          : `repeating-linear-gradient(transparent 0 10px, ${stripe} 10px 11px, transparent 11px 22px, ${stripeColor2} 22px 23px)`,
      }}/>
      {/* top-left page number */}
      {!compact && (
        <div style={{
          position:'absolute', top: 8, left: 10,
          fontFamily: theme.fonts.mono, fontSize: 9.5, letterSpacing:'0.12em',
          color: isHW ? '#5b3c1b' : theme.colors.textSubtle, opacity: 0.7,
        }}>p. {String(n).padStart(2, '0')}</div>
      )}
      {/* watermark label */}
      {title && !compact && (
        <div style={{
          position:'absolute', bottom: 12, left: 12, right: 12,
          fontFamily: theme.fonts.mono, fontSize: 10, letterSpacing:'0.08em',
          color: isHW ? '#5b3c1b' : theme.colors.textSubtle, opacity: 0.75,
          whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis',
        }}>[ {title.toLowerCase()} ]</div>
      )}
      {isHW && !compact && (
        <div style={{
          position:'absolute', top: 10, right: 12,
          fontFamily: '"Caveat", "Bradley Hand", cursive', fontSize: 13,
          color: '#5b3c1b', opacity: 0.6, transform: 'rotate(-4deg)',
        }}>✎ note</div>
      )}
    </div>
  );
}

// ─── Policies Tab ─────────────────────────────────────────────
function PoliciesTab({ theme, client, data }) {
  const pols = data.policies[client.id] || [];
  const [selectedId, setSelectedId] = useState(pols[0]?.id);
  const sel = pols.find(p => p.id === selectedId) || pols[0];

  if (pols.length === 0) {
    return (
      <Card theme={theme}>
        <div style={{padding: '60px 20px', textAlign:'center'}}>
          <div style={{width: 64, height: 64, margin: '0 auto 16px', borderRadius: theme.radius.lg, background: theme.colors.brandSoft, color: theme.colors.brand, display:'flex', alignItems:'center', justifyContent:'center'}}>{Icons.shield({size: 28})}</div>
          <div style={{fontFamily: theme.fonts.display, fontSize: 20, fontWeight: 600, color: theme.colors.text}}>No policies on file yet</div>
          <div style={{fontFamily: theme.fonts.ui, fontSize: 13.5, color: theme.colors.textMuted, marginTop: 6, maxWidth: 380, marginLeft:'auto', marginRight:'auto'}}>When {client.full_name.split(' ')[0]} enrolls, policies added here will appear in the dashboard renewal tracker.</div>
          <div style={{marginTop: 20, display:'inline-flex', gap: 8}}>
            <Button theme={theme} variant="primary" leftIcon={Icons.plus}>Add policy</Button>
            <Button theme={theme} variant="secondary" leftIcon={Icons.upload}>Import from document</Button>
          </div>
        </div>
      </Card>
    );
  }

  const totalPremium = pols.reduce((s, p) => s + (p.premium || 0), 0);

  return (
    <div style={{display:'grid', gridTemplateColumns: '1fr 1.6fr', gap: 14}}>
      {/* Left: policy list */}
      <Card theme={theme} padding="0">
        <div style={{padding: '18px 20px 12px', borderBottom: `1px solid ${theme.colors.border}`}}>
          <div style={{display:'flex', justifyContent:'space-between', alignItems:'flex-start', gap: 10}}>
            <div>
              <div style={{fontFamily: theme.fonts.ui, fontSize: 10.5, color: theme.colors.textMuted, letterSpacing: '0.14em', textTransform:'uppercase', fontWeight: 600}}>Coverage</div>
              <div style={{fontFamily: theme.fonts.display, fontSize: 22, fontWeight: 600, color: theme.colors.text, letterSpacing:'-0.01em'}}>{pols.length} {pols.length === 1 ? 'policy' : 'policies'}</div>
            </div>
            <Button theme={theme} variant="ghost" size="sm" leftIcon={Icons.plus}>Add</Button>
          </div>
          <div style={{display:'flex', gap: 16, marginTop: 10, fontFamily: theme.fonts.ui, fontSize: 12, color: theme.colors.textMuted}}>
            <div>Monthly premium <strong style={{color: theme.colors.text, fontFamily: theme.fonts.mono, fontWeight: 600}}>${totalPremium.toFixed(2)}</strong></div>
          </div>
        </div>
        <div style={{padding: 8}}>
          {pols.map(p => {
            const active = p.id === sel.id;
            return (
              <button key={p.id} onClick={() => setSelectedId(p.id)}
                onMouseEnter={e => { if (!active) e.currentTarget.style.background = theme.colors.surface2; }}
                onMouseLeave={e => { if (!active) e.currentTarget.style.background = 'transparent'; }}
                style={{
                  display:'block', width: '100%', textAlign:'left',
                  padding: '12px 14px',
                  background: active ? theme.colors.brandSoft : 'transparent',
                  border: 'none', cursor:'pointer',
                  borderRadius: theme.radius.md, marginBottom: 2,
                  borderLeft: `3px solid ${active ? theme.colors.accent : 'transparent'}`,
                  transition: 'background 120ms',
                }}>
                <div style={{display:'flex', justifyContent:'space-between', alignItems:'flex-start', gap: 8}}>
                  <div style={{minWidth: 0, flex: 1}}>
                    <div style={{fontFamily: theme.fonts.display, fontSize: 14.5, fontWeight: 600, color: theme.colors.text, letterSpacing:'-0.005em'}}>{p.plan}</div>
                    <div style={{fontFamily: theme.fonts.ui, fontSize: 11.5, color: theme.colors.textMuted, marginTop: 2}}>{p.carrier}</div>
                  </div>
                  <Badge theme={theme} tone={p.status === 'Active' ? 'success' : p.status === 'Pending' ? 'accent' : 'warning'}>{p.status}</Badge>
                </div>
                <div style={{display:'flex', justifyContent:'space-between', marginTop: 8, fontFamily: theme.fonts.mono, fontSize: 11, color: theme.colors.textSubtle}}>
                  <span>{p.type}</span>
                  <span style={{color: theme.colors.text}}>${p.premium.toFixed(2)}/mo</span>
                </div>
              </button>
            );
          })}
        </div>
      </Card>

      {/* Right: selected policy detail */}
      <Card theme={theme} padding="0">
        {/* Policy header band */}
        <div style={{
          padding: '20px 26px', position:'relative', overflow:'hidden',
          background: theme.colors.brand, color: theme.colors.brandText,
        }}>
          <div aria-hidden="true" style={{position:'absolute', inset: 0, background: `radial-gradient(ellipse 400px 200px at 100% 0%, ${theme.colors.accentSoft}, transparent 70%)`, pointerEvents:'none'}}/>
          <div style={{position:'relative', display:'flex', justifyContent:'space-between', alignItems:'flex-start', gap: 16, flexWrap:'wrap'}}>
            <div>
              <div style={{fontFamily: theme.fonts.ui, fontSize: 10.5, color: theme.colors.accent, letterSpacing: '0.14em', textTransform:'uppercase', fontWeight: 600}}>{sel.type}</div>
              <div style={{fontFamily: theme.fonts.display, fontSize: 26, fontWeight: 600, marginTop: 4, letterSpacing:'-0.015em'}}>{sel.plan}</div>
              <div style={{fontFamily: theme.fonts.ui, fontSize: 13, opacity: 0.78, marginTop: 4, display:'flex', alignItems:'center', gap: 8}}>
                <span style={{display:'inline-flex', alignItems:'center', gap: 5}}>{Icons.shield({size: 12})} {sel.carrier}</span>
                <span style={{opacity: 0.4}}>·</span>
                <span style={{fontFamily: theme.fonts.mono, fontSize: 11.5, letterSpacing: '0.04em'}}>{sel.policy_number}</span>
              </div>
            </div>
            <div style={{textAlign:'right'}}>
              <div style={{fontFamily: theme.fonts.ui, fontSize: 10.5, opacity: 0.7, letterSpacing:'0.14em', textTransform:'uppercase', fontWeight: 600}}>Monthly premium</div>
              <div style={{fontFamily: theme.fonts.display, fontSize: 32, fontWeight: 600, letterSpacing:'-0.02em'}}>
                ${sel.premium.toFixed(2)}
              </div>
              <div style={{fontFamily: theme.fonts.mono, fontSize: 11, opacity: 0.6}}>Commission: {sel.agent_commission}</div>
            </div>
          </div>
        </div>

        {/* Meta grid */}
        <div style={{padding: '20px 26px'}}>
          <div style={{display:'grid', gridTemplateColumns:'repeat(4, 1fr)', gap: '16px 20px'}}>
            {[
              ['Status', <Badge key="s" theme={theme} tone={sel.status === 'Active' ? 'success' : sel.status === 'Pending' ? 'accent' : 'warning'}>{sel.status}</Badge>],
              ['Effective', data.mdy(sel.effective)],
              ['Renewal', data.mdy(sel.renewal)],
              ['Policy #', <span key="p" style={{fontFamily: theme.fonts.mono}}>{sel.policy_number}</span>],
            ].map(([k, v]) => (
              <div key={k}>
                <div style={{fontFamily: theme.fonts.ui, fontSize: 10.5, color: theme.colors.textMuted, letterSpacing:'0.1em', textTransform:'uppercase', fontWeight: 600, marginBottom: 6}}>{k}</div>
                <div style={{fontFamily: theme.fonts.ui, fontSize: 13.5, color: theme.colors.text, fontWeight: 500}}>{v}</div>
              </div>
            ))}
          </div>

          <Hairline theme={theme} label="Coverage snapshot" style={{margin: '24px 0 16px'}}/>

          {/* Coverage items — sample illustrative */}
          <div style={{display:'grid', gridTemplateColumns:'repeat(2, 1fr)', gap: 12}}>
            {sel.type === 'Medicare Supplement' && [
              ['Part A deductible', 'Covered 100%'],
              ['Part B coinsurance', 'Covered 100%'],
              ['Skilled nursing', 'Covered 100%'],
              ['Foreign travel', 'Covered 80% (up to plan limit)'],
            ].map(([k, v]) => <CoverageRow key={k} theme={theme} k={k} v={v}/>)}
            {sel.type === 'Part D' && [
              ['Monthly premium', `$${sel.premium.toFixed(2)}`],
              ['Annual deductible', '$545'],
              ['Preferred pharmacy', 'In network'],
              ['Formulary match', '5 of 6 medications covered'],
            ].map(([k, v]) => <CoverageRow key={k} theme={theme} k={k} v={v}/>)}
            {sel.type === 'Medicare Advantage' && [
              ['Monthly premium', '$0.00'],
              ['Max out-of-pocket', '$4,900/yr'],
              ['Primary care visit', '$0 copay'],
              ['Specialist visit', '$35 copay'],
            ].map(([k, v]) => <CoverageRow key={k} theme={theme} k={k} v={v}/>)}
            {sel.type === 'Employer Group' && [
              ['In-network deductible', '$1,500/yr'],
              ['Coinsurance', '20% after deductible'],
              ['Out-of-pocket max', '$4,000/yr'],
              ['Ending', `${data.mdy(sel.renewal)} (retirement)`],
            ].map(([k, v]) => <CoverageRow key={k} theme={theme} k={k} v={v}/>)}
            {sel.type === 'Dental, Vision, Hearing' && [
              ['Annual dental max', '$1,500'],
              ['Vision exam', '$0 copay'],
              ['Hearing aid benefit', '$1,200 / 3 yrs'],
              ['Waiting period', 'Waived'],
            ].map(([k, v]) => <CoverageRow key={k} theme={theme} k={k} v={v}/>)}
          </div>

          <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginTop: 22, paddingTop: 18, borderTop: `1px solid ${theme.colors.border}`}}>
            <div style={{fontFamily: theme.fonts.ui, fontSize: 12, color: theme.colors.textMuted}}>
              {Icons.fileText({size: 12})} Linked to <a href="#" style={{color: theme.colors.accent, textDecoration:'none'}}>Current BCBS Policy.pdf</a>
            </div>
            <div style={{display:'flex', gap: 8}}>
              <Button theme={theme} variant="ghost" size="sm" leftIcon={Icons.download}>Export PDF</Button>
              <Button theme={theme} variant="secondary" size="sm" leftIcon={Icons.edit}>Edit</Button>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}

function CoverageRow({ theme, k, v }) {
  return (
    <div style={{display:'flex', justifyContent:'space-between', alignItems:'baseline', padding: '10px 12px', background: theme.colors.surface2, borderRadius: theme.radius.sm, border: `1px solid ${theme.colors.border}`}}>
      <span style={{fontFamily: theme.fonts.ui, fontSize: 12.5, color: theme.colors.textMuted}}>{k}</span>
      <span style={{fontFamily: theme.fonts.ui, fontSize: 13, color: theme.colors.text, fontWeight: 600}}>{v}</span>
    </div>
  );
}

// ─── Document Viewer ──────────────────────────────────────────
function DocumentViewerScreen({ theme, doc, client, data, onClose }) {
  const [pageIdx, setPageIdx] = useState(0);
  const [zoom, setZoom] = useState(1);
  const page = doc.pages[pageIdx];
  const isHW = page?.kind === 'handwritten';

  useEffect(() => {
    function key(e) {
      if (e.key === 'ArrowRight') setPageIdx(i => Math.min(i + 1, doc.pages.length - 1));
      if (e.key === 'ArrowLeft')  setPageIdx(i => Math.max(i - 1, 0));
      if (e.key === 'Escape')     onClose?.();
      if (e.key === '+' || e.key === '=') setZoom(z => Math.min(z + 0.1, 2.5));
      if (e.key === '-')          setZoom(z => Math.max(z - 0.1, 0.5));
    }
    window.addEventListener('keydown', key);
    return () => window.removeEventListener('keydown', key);
  }, [doc, onClose]);

  return (
    <div style={{
      display:'grid', gridTemplateColumns: '220px 1fr 320px',
      gap: 0, height: 'calc(100vh - 64px - 48px)', minHeight: 560, maxHeight: 900,
      background: theme.colors.surface, border: `1px solid ${theme.colors.border}`,
      borderRadius: theme.radius.lg, overflow:'hidden',
      boxShadow: theme.shadow.card,
    }}>
      {/* LEFT: thumbnail rail */}
      <div style={{background: theme.colors.surface2, borderRight: `1px solid ${theme.colors.border}`, display:'flex', flexDirection:'column', minHeight: 0}}>
        <div style={{padding: '14px 16px 10px', borderBottom: `1px solid ${theme.colors.border}`}}>
          <div style={{fontFamily: theme.fonts.ui, fontSize: 10.5, color: theme.colors.textMuted, letterSpacing: '0.12em', textTransform:'uppercase', fontWeight: 600}}>{doc.pages.length} pages</div>
          <div style={{fontFamily: theme.fonts.display, fontSize: 14, fontWeight: 600, color: theme.colors.text, marginTop: 3, whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis'}}>{doc.display_name}</div>
        </div>
        <div style={{flex: 1, overflow:'auto', padding: '12px 14px', display:'flex', flexDirection:'column', gap: 10}}>
          {doc.pages.map((p, i) => (
            <button key={i} onClick={() => setPageIdx(i)} style={{
              all: 'unset', cursor:'pointer', position:'relative',
              borderRadius: theme.radius.sm,
              outline: i === pageIdx ? `2px solid ${theme.colors.accent}` : 'none',
              outlineOffset: 3,
            }}>
              <PagePlaceholder theme={theme} width={172} height={222} n={p.n} title={p.title} kind={p.kind} compact/>
              <div style={{
                position:'absolute', left: 6, bottom: 6,
                padding: '2px 6px', background: theme.colors.text, color: theme.colors.surface,
                borderRadius: theme.radius.sm, fontFamily: theme.fonts.mono, fontSize: 10, fontWeight: 600,
              }}>{String(p.n).padStart(2, '0')}</div>
            </button>
          ))}
        </div>
      </div>

      {/* CENTER: page viewport */}
      <div style={{display:'flex', flexDirection:'column', minWidth: 0, minHeight: 0}}>
        {/* Viewer toolbar */}
        <div style={{height: 48, padding: '0 16px', borderBottom: `1px solid ${theme.colors.border}`, display:'flex', alignItems:'center', gap: 12, background: theme.colors.surface}}>
          <button onClick={onClose} style={{background:'none', border: `1px solid ${theme.colors.border}`, borderRadius: theme.radius.md, padding: '6px 10px', cursor:'pointer', color: theme.colors.textMuted, display:'inline-flex', alignItems:'center', gap: 6, fontFamily: theme.fonts.ui, fontSize: 12}}>
            {Icons.chevronLeft({size: 14})} Back
          </button>
          <div style={{width: 1, height: 20, background: theme.colors.border}}/>

          <div style={{display:'flex', alignItems:'center', gap: 2}}>
            <IconBtn theme={theme} disabled={pageIdx === 0} onClick={() => setPageIdx(i => Math.max(i - 1, 0))} icon={Icons.chevronLeft}/>
            <div style={{minWidth: 80, textAlign:'center', fontFamily: theme.fonts.mono, fontSize: 12, color: theme.colors.text}}>{pageIdx + 1} / {doc.pages.length}</div>
            <IconBtn theme={theme} disabled={pageIdx === doc.pages.length - 1} onClick={() => setPageIdx(i => Math.min(i + 1, doc.pages.length - 1))} icon={Icons.chevronRight}/>
          </div>

          <div style={{width: 1, height: 20, background: theme.colors.border}}/>

          <div style={{display:'flex', alignItems:'center', gap: 2}}>
            <IconBtn theme={theme} onClick={() => setZoom(z => Math.max(z - 0.1, 0.5))} label="−"/>
            <div style={{minWidth: 50, textAlign:'center', fontFamily: theme.fonts.mono, fontSize: 12, color: theme.colors.textMuted}}>{Math.round(zoom * 100)}%</div>
            <IconBtn theme={theme} onClick={() => setZoom(z => Math.min(z + 0.1, 2.5))} label="+"/>
            <IconBtn theme={theme} onClick={() => setZoom(1)} label="1:1" wide/>
          </div>

          <div style={{flex: 1}}/>

          <Badge theme={theme} tone={isHW ? 'warning' : 'brand'}>{doc.type}</Badge>

          <div style={{display:'flex', gap: 4}}>
            <IconBtn theme={theme} icon={Icons.download} title="Download"/>
            <IconBtn theme={theme} icon={Icons.edit} title="Annotate"/>
            <IconBtn theme={theme} icon={Icons.trash} title="Delete" danger/>
          </div>
        </div>

        {/* Page area */}
        <div style={{flex: 1, overflow:'auto', background: theme.colors.bg, padding: '32px 0', display:'flex', justifyContent:'center', alignItems:'flex-start'}}>
          <div style={{transform: `scale(${zoom})`, transformOrigin:'top center', transition:'transform 200ms ease'}}>
            <div style={{position:'relative'}}>
              <PagePlaceholder theme={theme} width={560} height={720} n={page.n} title={page.title} kind={page.kind}/>
              {/* "Scan meta" edge label */}
              <div style={{
                position:'absolute', top: -22, left: 0, right: 0,
                display:'flex', justifyContent:'space-between',
                fontFamily: theme.fonts.mono, fontSize: 10.5, color: theme.colors.textSubtle, letterSpacing:'0.08em',
              }}>
                <span>{doc.display_name.toUpperCase()}</span>
                <span>PAGE {String(page.n).padStart(2,'0')} / {String(doc.pages.length).padStart(2,'0')}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* RIGHT: metadata + transcript */}
      <div style={{background: theme.colors.surface, borderLeft: `1px solid ${theme.colors.border}`, display:'flex', flexDirection:'column', minHeight: 0}}>
        <div style={{padding: '16px 20px', borderBottom: `1px solid ${theme.colors.border}`}}>
          <div style={{fontFamily: theme.fonts.ui, fontSize: 10.5, color: theme.colors.textMuted, letterSpacing: '0.12em', textTransform:'uppercase', fontWeight: 600}}>Linked to</div>
          <div style={{display:'flex', alignItems:'center', gap: 10, marginTop: 8}}>
            <Avatar initials={client.initials} size={34} theme={theme}/>
            <div>
              <div style={{fontFamily: theme.fonts.display, fontSize: 15, fontWeight: 600, color: theme.colors.text}}>{client.full_name}</div>
              <div style={{fontFamily: theme.fonts.ui, fontSize: 11.5, color: theme.colors.textMuted}}>DOB {client.dob_display} · age {client.age}</div>
            </div>
          </div>
        </div>

        <div style={{flex: 1, overflow:'auto'}}>
          {/* Document meta */}
          <div style={{padding: '16px 20px', borderBottom: `1px solid ${theme.colors.border}`}}>
            <div style={{fontFamily: theme.fonts.ui, fontSize: 10.5, color: theme.colors.textMuted, letterSpacing: '0.12em', textTransform:'uppercase', fontWeight: 600, marginBottom: 10}}>Document</div>
            <dl style={{margin: 0, display:'grid', gridTemplateColumns:'auto 1fr', gap: '8px 14px', fontFamily: theme.fonts.ui, fontSize: 12.5}}>
              {[
                ['Uploaded', doc.created],
                ['By', doc.uploaded_by],
                ['Source', doc.source],
                ['Size', doc.size],
                ['Pages', `${doc.pages.length}`],
              ].map(([k,v]) => (
                <React.Fragment key={k}>
                  <dt style={{color: theme.colors.textMuted}}>{k}</dt>
                  <dd style={{margin: 0, color: theme.colors.text, fontWeight: 500}}>{v}</dd>
                </React.Fragment>
              ))}
            </dl>
            <div style={{display:'flex', flexWrap:'wrap', gap: 5, marginTop: 12}}>
              {doc.tags.map(t => (
                <span key={t} style={{padding: '2px 8px', fontSize: 10.5, fontFamily: theme.fonts.mono, color: theme.colors.textMuted, background: theme.colors.surface2, border: `1px solid ${theme.colors.border}`, borderRadius: theme.radius.pill, letterSpacing:'0.02em'}}>{t}</span>
              ))}
            </div>
          </div>

          {/* OCR / transcript */}
          {isHW && page.transcript && (
            <div style={{padding: '16px 20px', borderBottom: `1px solid ${theme.colors.border}`}}>
              <div style={{display:'flex', justifyContent:'space-between', alignItems:'baseline', marginBottom: 10}}>
                <div style={{fontFamily: theme.fonts.ui, fontSize: 10.5, color: theme.colors.textMuted, letterSpacing: '0.12em', textTransform:'uppercase', fontWeight: 600}}>Transcribed</div>
                <div style={{fontFamily: theme.fonts.mono, fontSize: 10.5, color: theme.colors.textSubtle}}>OCR · {Math.round((page.ocr_confidence || 0.9) * 100)}% conf.</div>
              </div>
              <ol style={{margin: 0, padding: 0, listStyle: 'none', display:'flex', flexDirection:'column', gap: 6}}>
                {page.transcript.map((line, i) => (
                  <li key={i} style={{display:'flex', gap: 10, padding: '7px 10px', background: theme.colors.surface2, border: `1px solid ${theme.colors.border}`, borderRadius: theme.radius.sm, fontFamily: theme.fonts.ui, fontSize: 12.5, color: theme.colors.text}}>
                    <span style={{fontFamily: theme.fonts.mono, fontSize: 10.5, color: theme.colors.textSubtle, minWidth: 14}}>{i+1}.</span>
                    <span>{line}</span>
                  </li>
                ))}
              </ol>
              <Button theme={theme} variant="ghost" size="sm" leftIcon={Icons.edit} style={{marginTop: 10}}>Edit transcript</Button>
            </div>
          )}

          {/* Notes */}
          <div style={{padding: '16px 20px'}}>
            <div style={{fontFamily: theme.fonts.ui, fontSize: 10.5, color: theme.colors.textMuted, letterSpacing: '0.12em', textTransform:'uppercase', fontWeight: 600, marginBottom: 10}}>Notes on this page</div>
            <Textarea theme={theme} value="" onChange={() => {}} placeholder="Add a note about this page…" rows={4}/>
          </div>
        </div>
      </div>
    </div>
  );
}

function IconBtn({ theme, icon, label, onClick, disabled, danger, title, wide }) {
  const [hover, setHover] = useState(false);
  return (
    <button onClick={onClick} disabled={disabled} title={title}
      onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
      style={{
        height: 30, minWidth: wide ? 44 : 30, padding: wide ? '0 8px' : 0,
        background: hover && !disabled ? (danger ? theme.colors.dangerSoft : theme.colors.surface2) : 'transparent',
        border: `1px solid ${hover && !disabled ? theme.colors.border : 'transparent'}`,
        borderRadius: theme.radius.sm, cursor: disabled ? 'not-allowed' : 'pointer',
        color: danger ? theme.colors.danger : theme.colors.textMuted,
        display:'inline-flex', alignItems:'center', justifyContent:'center',
        fontFamily: theme.fonts.ui, fontSize: 12, fontWeight: 600,
        opacity: disabled ? 0.4 : 1, transition: 'background 120ms',
      }}>
      {icon ? icon({size: 15}) : label}
    </button>
  );
}

Object.assign(window, { PoliciesTab, DocumentViewerScreen, Hairline, PagePlaceholder });
