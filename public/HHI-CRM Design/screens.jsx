// Client list + client detail + client intake screens.

function ClientListScreen({ theme, data, onOpenClient, onNav }) {
  const [q, setQ] = useState('');
  const [filter, setFilter] = useState('all');
  const [sortBy, setSortBy] = useState('recent');
  const [selected, setSelected] = useState(new Set());

  const rows = useMemo(() => {
    let r = [...data.clients];
    if (q.trim()) {
      const n = q.toLowerCase();
      r = r.filter(c => c.full_name.toLowerCase().includes(n) || c.phone.includes(n) || c.email.toLowerCase().includes(n) || c.city.toLowerCase().includes(n));
    }
    if (filter === 'turning65') r = r.filter(c => c.days_until_65 >= 0 && c.days_until_65 <= 90);
    if (filter === 'no_policy') r = r.filter(c => c.policies === 0);
    if (filter === 'recent') r = r.filter(c => (data.today - c.created) < 7*86400000);
    if (sortBy === 'recent') r.sort((a,b) => b.created - a.created);
    if (sortBy === 'name') r.sort((a,b) => a.full_name.localeCompare(b.full_name));
    if (sortBy === 'turns65') r.sort((a,b) => a.days_until_65 - b.days_until_65);
    return r;
  }, [q, filter, sortBy, data]);

  function toggle(id) {
    const s = new Set(selected);
    if (s.has(id)) s.delete(id); else s.add(id);
    setSelected(s);
  }

  return (
    <div style={{maxWidth: 1320, margin: '0 auto'}}>
      {/* Filter bar */}
      <div style={{display:'flex', alignItems:'center', gap: 12, marginBottom: 16, flexWrap:'wrap'}}>
        <div style={{flex: 1, minWidth: 280, maxWidth: 480}}>
          <Input theme={theme} value={q} onChange={e => setQ(e.target.value)} placeholder="Search by name, phone, email, or city…" leftIcon={Icons.search}/>
        </div>
        <div style={{display:'flex', gap: 4, padding: 3, background: theme.colors.surface, borderRadius: theme.radius.pill, border: `1px solid ${theme.colors.border}`}}>
          {[
            {k:'all', l:'All', count: data.clients.length},
            {k:'turning65', l:'Turning 65', count: data.turning_65.length},
            {k:'no_policy', l:'No policy', count: data.clients.filter(c => c.policies === 0).length},
            {k:'recent', l:'This week', count: data.added_total},
          ].map(f => (
            <button key={f.k} onClick={() => setFilter(f.k)} style={{
              padding: '6px 12px', border: 'none', cursor: 'pointer',
              background: filter === f.k ? theme.colors.brand : 'transparent',
              color: filter === f.k ? theme.colors.brandText : theme.colors.textMuted,
              fontFamily: theme.fonts.ui, fontSize: 12.5, fontWeight: 600,
              borderRadius: theme.radius.pill,
              display:'inline-flex', alignItems:'center', gap: 6,
              transition: 'background 140ms',
            }}>
              {f.l}
              <span style={{fontSize: 10.5, opacity: 0.7, fontFamily: theme.fonts.mono}}>{f.count}</span>
            </button>
          ))}
        </div>
        <Select theme={theme} value={sortBy} onChange={e => setSortBy(e.target.value)} options={[
          {value:'recent', label:'Most recent'},
          {value:'name', label:'Name A → Z'},
          {value:'turns65', label:'Turns 65 soonest'},
        ]} style={{width: 180}}/>
        <Button theme={theme} variant="primary" leftIcon={Icons.plus} onClick={() => onNav('intake')}>New client</Button>
      </div>

      {/* Bulk action bar */}
      {selected.size > 0 && (
        <div style={{
          display:'flex', alignItems:'center', gap: 14, padding: '10px 16px', marginBottom: 12,
          background: theme.colors.brand, color: theme.colors.brandText, borderRadius: theme.radius.md,
          animation: 'hhi-toast-in 200ms',
        }}>
          <span style={{fontFamily: theme.fonts.ui, fontSize: 13, fontWeight: 600}}>{selected.size} selected</span>
          <div style={{height: 20, width: 1, background: 'rgba(255,255,255,0.2)'}}/>
          <button style={{background:'none', border:'none', color: theme.colors.brandText, fontSize: 13, fontFamily: theme.fonts.ui, cursor:'pointer', opacity: 0.85, display:'inline-flex', alignItems:'center', gap: 6}}>{Icons.mail({size: 14})} Email</button>
          <button style={{background:'none', border:'none', color: theme.colors.brandText, fontSize: 13, fontFamily: theme.fonts.ui, cursor:'pointer', opacity: 0.85, display:'inline-flex', alignItems:'center', gap: 6}}>{Icons.download({size: 14})} Export</button>
          <button onClick={() => setSelected(new Set())} style={{marginLeft:'auto', background:'none', border:'none', color: theme.colors.brandText, fontSize: 13, fontFamily: theme.fonts.ui, cursor:'pointer', opacity: 0.65}}>Clear</button>
        </div>
      )}

      {/* Table */}
      <Card theme={theme} padding="0">
        <table style={{width:'100%', borderCollapse:'collapse', fontFamily: theme.fonts.ui}}>
          <thead>
            <tr style={{borderBottom: `1px solid ${theme.colors.border}`}}>
              <th style={{padding: '12px 16px', width: 36}}>
                <input type="checkbox" checked={selected.size === rows.length && rows.length > 0} onChange={e => setSelected(e.target.checked ? new Set(rows.map(r => r.id)) : new Set())} style={{accentColor: theme.colors.accent, width: 14, height: 14}}/>
              </th>
              {['Client','Contact','Location','Age','Turns 65','Docs','Added'].map(h => (
                <th key={h} style={{textAlign:'left', padding: '12px 14px', fontSize: 11, fontWeight: 600, color: theme.colors.textMuted, letterSpacing: '0.08em', textTransform:'uppercase'}}>{h}</th>
              ))}
              <th style={{width: 40}}/>
            </tr>
          </thead>
          <tbody>
            {rows.map(c => {
              const isSel = selected.has(c.id);
              return (
                <tr key={c.id}
                  onClick={() => onOpenClient(c.id)}
                  onMouseEnter={e => e.currentTarget.style.background = theme.colors.surface2}
                  onMouseLeave={e => e.currentTarget.style.background = isSel ? theme.colors.accentSoft : 'transparent'}
                  style={{
                  borderBottom: `1px solid ${theme.colors.border}`,
                  background: isSel ? theme.colors.accentSoft : 'transparent',
                  cursor:'pointer', transition: 'background 120ms',
                }}>
                  <td style={{padding: '12px 16px'}} onClick={e => { e.stopPropagation(); toggle(c.id); }}>
                    <input type="checkbox" checked={isSel} onChange={() => toggle(c.id)} onClick={e => e.stopPropagation()} style={{accentColor: theme.colors.accent, width: 14, height: 14}}/>
                  </td>
                  <td style={{padding: '12px 14px'}}>
                    <div style={{display:'flex', alignItems:'center', gap: 12}}>
                      <Avatar initials={c.initials} size={34} theme={theme}/>
                      <div style={{minWidth: 0}}>
                        <div style={{fontSize: 13.5, fontWeight: 600, color: theme.colors.text}}>{c.full_name}</div>
                        <div style={{fontSize: 11.5, color: theme.colors.textSubtle, marginTop: 2}}>DOB {c.dob_display}</div>
                      </div>
                    </div>
                  </td>
                  <td style={{padding: '12px 14px', fontSize: 13}}>
                    <div style={{color: theme.colors.text, fontFamily: theme.fonts.mono, fontSize: 12}}>{c.phone}</div>
                    <div style={{color: theme.colors.textMuted, fontSize: 11.5, marginTop: 2, whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis', maxWidth: 200}}>{c.email}</div>
                  </td>
                  <td style={{padding: '12px 14px', fontSize: 13, color: theme.colors.text}}>
                    {c.city}<span style={{color: theme.colors.textSubtle}}>, {c.state}</span>
                  </td>
                  <td style={{padding: '12px 14px', fontSize: 13, color: theme.colors.text, fontFamily: theme.fonts.mono}}>{c.age}</td>
                  <td style={{padding: '12px 14px'}}>
                    {c.days_until_65 >= 0 && c.days_until_65 <= 90 ? (
                      <Badge theme={theme} tone={c.days_until_65 <= 14 ? 'danger' : c.days_until_65 <= 30 ? 'warning' : 'accent'}>
                        {c.days_until_65 === 0 ? 'Today' : `${c.days_until_65}d`}
                      </Badge>
                    ) : (
                      <span style={{fontSize: 12, color: theme.colors.textSubtle, fontFamily: theme.fonts.mono}}>{c.turns_65_display}</span>
                    )}
                  </td>
                  <td style={{padding: '12px 14px'}}>
                    <div style={{display:'flex', gap: 6, alignItems:'center'}}>
                      {c.policies > 0 && <Badge theme={theme} tone="brand" leftIcon={Icons.shield}>{c.policies}</Badge>}
                      {c.attachments > 0 && <Badge theme={theme} tone="neutral" leftIcon={Icons.paperclip}>{c.attachments}</Badge>}
                      {c.hw_notes > 0 && <Badge theme={theme} tone="warning" leftIcon={Icons.fileText}>{c.hw_notes}</Badge>}
                      {c.policies === 0 && c.attachments === 0 && c.hw_notes === 0 && <span style={{fontSize: 11.5, color: theme.colors.textSubtle}}>—</span>}
                    </div>
                  </td>
                  <td style={{padding: '12px 14px', fontSize: 12, color: theme.colors.textMuted, fontFamily: theme.fonts.mono, whiteSpace:'nowrap'}}>{c.created_display}</td>
                  <td style={{padding: '12px 14px', color: theme.colors.textSubtle}}>{Icons.chevronRight({size: 14})}</td>
                </tr>
              );
            })}
            {rows.length === 0 && (
              <tr><td colSpan={9} style={{padding: '48px 16px', textAlign:'center', fontFamily: theme.fonts.ui, fontSize: 13.5, color: theme.colors.textMuted}}>
                No clients match your filters.
              </td></tr>
            )}
          </tbody>
        </table>
        <div style={{display:'flex', alignItems:'center', justifyContent:'space-between', padding: '12px 18px', borderTop: `1px solid ${theme.colors.border}`, fontFamily: theme.fonts.ui, fontSize: 12.5, color: theme.colors.textMuted}}>
          <span>Showing <strong style={{color: theme.colors.text}}>{rows.length}</strong> of {data.clients.length}</span>
          <div style={{display:'flex', gap: 6}}>
            <Button theme={theme} variant="secondary" size="sm" disabled>Previous</Button>
            <Button theme={theme} variant="secondary" size="sm">Next</Button>
          </div>
        </div>
      </Card>
    </div>
  );
}

// ─── Client Detail ─────────────────────────────────────────────
function ClientDetailScreen({ theme, client, data, onBack, onEdit, onOpenDoc }) {
  const [tab, setTab] = useState('overview');
  const atts = data.attachments[client.id] || [];
  const acts = data.activity[client.id] || [
    { date: new Date(2026, 3, 15), kind: 'note', text: 'Client added to the system.' },
  ];

  const Tabs = [
    {k:'overview', l:'Overview'},
    {k:'documents', l:'Documents', count: atts.length},
    {k:'policies', l:'Policies', count: client.policies},
    {k:'activity', l:'Activity', count: acts.length},
  ];

  const kindIcon = {
    note: Icons.fileText, doc: Icons.paperclip, call: Icons.phone, email: Icons.mail,
  };

  return (
    <div style={{maxWidth: 1320, margin: '0 auto'}}>
      {/* Header card */}
      <Card theme={theme} style={{marginBottom: 14, padding: 0, overflow:'hidden'}}>
        <div style={{
          height: 72, background: `linear-gradient(135deg, ${theme.colors.brand} 0%, ${theme.colors.brand} 60%, ${theme.colors.accent} 200%)`,
          position:'relative',
        }}>
          <div aria-hidden="true" style={{position:'absolute', inset: 0, background: `repeating-linear-gradient(45deg, transparent, transparent 16px, rgba(255,255,255,0.04) 16px, rgba(255,255,255,0.04) 17px)`}}/>
        </div>
        <div style={{padding: '0 28px 20px', display:'flex', alignItems:'flex-end', gap: 18, marginTop: -32, flexWrap:'wrap'}}>
          <Avatar initials={client.initials} size={72} theme={theme} style={{border: `3px solid ${theme.colors.surface}`, boxShadow: theme.shadow.md, borderRadius: theme.radius.lg, fontSize: 24}}/>
          <div style={{flex: 1, minWidth: 240, paddingTop: 32}}>
            <div style={{display:'flex', alignItems:'center', gap: 10, flexWrap:'wrap'}}>
              <h2 style={{margin: 0, fontFamily: theme.fonts.display, fontSize: 26, fontWeight: 600, color: theme.colors.text, letterSpacing:'-0.015em'}}>{client.full_name}</h2>
              {client.days_until_65 >= 0 && client.days_until_65 <= 90 && (
                <Badge theme={theme} tone={client.days_until_65 <= 14 ? 'danger' : 'accent'} leftIcon={Icons.heart}>Turns 65 in {client.days_until_65}d</Badge>
              )}
              <Badge theme={theme} tone="success" leftIcon={Icons.dot}>Active</Badge>
            </div>
            <div style={{display:'flex', gap: 16, marginTop: 6, flexWrap:'wrap', fontFamily: theme.fonts.ui, fontSize: 12.5, color: theme.colors.textMuted}}>
              <span style={{display:'inline-flex', alignItems:'center', gap: 5}}>{Icons.phone({size: 12})} {client.phone}</span>
              <span style={{display:'inline-flex', alignItems:'center', gap: 5}}>{Icons.mail({size: 12})} {client.email}</span>
              <span style={{display:'inline-flex', alignItems:'center', gap: 5}}>{Icons.mapPin({size: 12})} {client.city}, {client.state}</span>
              <span style={{display:'inline-flex', alignItems:'center', gap: 5}}>{Icons.calendar({size: 12})} DOB {client.dob_display} (age {client.age})</span>
            </div>
          </div>
          <div style={{display:'flex', gap: 8, paddingTop: 32}}>
            <Button theme={theme} variant="secondary" leftIcon={Icons.phone}>Call</Button>
            <Button theme={theme} variant="secondary" leftIcon={Icons.camera}>Scan</Button>
            <Button theme={theme} variant="primary" leftIcon={Icons.edit} onClick={onEdit}>Edit</Button>
          </div>
        </div>

        {/* Tabs */}
        <div style={{display:'flex', gap: 2, padding: '0 20px', borderTop: `1px solid ${theme.colors.border}`, background: theme.colors.surface2}}>
          {Tabs.map(t => (
            <button key={t.k} onClick={() => setTab(t.k)} style={{
              padding: '12px 16px', border: 'none', cursor:'pointer', background:'transparent',
              color: tab === t.k ? theme.colors.text : theme.colors.textMuted,
              fontFamily: theme.fonts.ui, fontSize: 13, fontWeight: 600,
              borderBottom: `2px solid ${tab === t.k ? theme.colors.accent : 'transparent'}`,
              marginBottom: -1,
              display:'inline-flex', alignItems:'center', gap: 6,
            }}>
              {t.l}
              {t.count > 0 && <span style={{fontSize: 11, padding: '1px 6px', background: theme.colors.surface, borderRadius: theme.radius.pill, color: theme.colors.textMuted, fontFamily: theme.fonts.mono}}>{t.count}</span>}
            </button>
          ))}
        </div>
      </Card>

      {tab === 'overview' && (
        <div style={{display:'grid', gridTemplateColumns: '1.4fr 1fr', gap: 14}}>
          {/* Left column */}
          <div style={{display:'flex', flexDirection:'column', gap: 14}}>
            <Card theme={theme}>
              <div style={{fontFamily: theme.fonts.ui, fontSize: 11.5, color: theme.colors.textMuted, letterSpacing: '0.08em', textTransform:'uppercase', fontWeight: 600, marginBottom: 14}}>Personal information</div>
              <div style={{display:'grid', gridTemplateColumns:'repeat(2, 1fr)', gap: '18px 24px'}}>
                {[
                  ['Full name', client.full_name],
                  ['Date of birth', `${client.dob_display} · age ${client.age}`],
                  ['Phone', client.phone],
                  ['Email', client.email],
                  ['Income', client.income],
                  ['Turns 65', client.turns_65_display],
                  ['Address', client.address],
                  ['City, State, ZIP', `${client.city}, ${client.state} ${client.zip}`],
                ].map(([k, v]) => (
                  <div key={k}>
                    <div style={{fontFamily: theme.fonts.ui, fontSize: 11, color: theme.colors.textSubtle, letterSpacing:'0.04em', textTransform:'uppercase', fontWeight: 600, marginBottom: 4}}>{k}</div>
                    <div style={{fontFamily: theme.fonts.ui, fontSize: 13.5, color: theme.colors.text}}>{v || <span style={{color: theme.colors.textSubtle}}>—</span>}</div>
                  </div>
                ))}
              </div>
              {client.notes && (
                <div style={{marginTop: 20, paddingTop: 16, borderTop: `1px solid ${theme.colors.border}`}}>
                  <div style={{fontFamily: theme.fonts.ui, fontSize: 11, color: theme.colors.textSubtle, letterSpacing:'0.04em', textTransform:'uppercase', fontWeight: 600, marginBottom: 6}}>Notes</div>
                  <div style={{fontFamily: theme.fonts.ui, fontSize: 13.5, color: theme.colors.text, lineHeight: 1.6}}>{client.notes}</div>
                </div>
              )}
            </Card>

            <Card theme={theme}>
              <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom: 14}}>
                <div style={{fontFamily: theme.fonts.ui, fontSize: 11.5, color: theme.colors.textMuted, letterSpacing: '0.08em', textTransform:'uppercase', fontWeight: 600}}>Attachments</div>
                <Button theme={theme} variant="ghost" size="sm" leftIcon={Icons.upload}>Upload</Button>
              </div>
              {atts.length === 0 ? (
                <div style={{
                  border: `1.5px dashed ${theme.colors.borderStrong}`,
                  borderRadius: theme.radius.md, padding: '28px 18px',
                  textAlign:'center', color: theme.colors.textMuted, fontSize: 13,
                }}>No attachments yet. <a href="#" style={{color: theme.colors.accent, textDecoration:'none'}}>Upload</a> or <a href="#" style={{color: theme.colors.accent, textDecoration:'none'}}>scan</a> documents.</div>
              ) : (
                <div style={{display:'flex', flexDirection:'column', gap: 8}}>
                  {atts.map(a => (
                    <div key={a.id} style={{
                      display:'flex', alignItems:'center', gap: 12, padding: '10px 12px',
                      background: theme.colors.surface2, borderRadius: theme.radius.md,
                      border: `1px solid ${theme.colors.border}`,
                    }}>
                      {/* thumbnail placeholder */}
                      <div style={{
                        width: 38, height: 48, flexShrink: 0,
                        background: `repeating-linear-gradient(135deg, ${theme.colors.surface}, ${theme.colors.surface} 4px, ${theme.colors.surface2} 4px, ${theme.colors.surface2} 7px)`,
                        border: `1px solid ${theme.colors.border}`, borderRadius: theme.radius.sm,
                        display:'flex', alignItems:'center', justifyContent:'center',
                        color: theme.colors.textSubtle,
                      }}>
                        {Icons.fileText({size: 16})}
                      </div>
                      <div style={{flex: 1, minWidth: 0}}>
                        <div style={{fontFamily: theme.fonts.ui, fontSize: 13, fontWeight: 600, color: theme.colors.text}}>{a.display_name}</div>
                        <div style={{fontFamily: theme.fonts.ui, fontSize: 11.5, color: theme.colors.textMuted, marginTop: 2}}>{a.type} · {a.pages} page{a.pages === 1 ? '' : 's'} · {a.created}</div>
                      </div>
                      <div style={{display:'flex', gap: 4}}>
                        {Array.from({length: Math.min(a.pages, 4)}).map((_, i) => (
                          <button key={i} style={{padding: '3px 8px', background: theme.colors.surface, border: `1px solid ${theme.colors.border}`, borderRadius: theme.radius.sm, fontSize: 11, fontFamily: theme.fonts.mono, color: theme.colors.textMuted, cursor:'pointer'}}>p{i+1}</button>
                        ))}
                        {a.pages > 4 && <span style={{fontSize: 11, color: theme.colors.textSubtle, alignSelf:'center'}}>+{a.pages-4}</span>}
                      </div>
                      <Button theme={theme} variant="ghost" size="sm" leftIcon={Icons.eye}>Open</Button>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>

          {/* Right column */}
          <div style={{display:'flex', flexDirection:'column', gap: 14}}>
            <Card theme={theme}>
              <div style={{fontFamily: theme.fonts.ui, fontSize: 11.5, color: theme.colors.textMuted, letterSpacing: '0.08em', textTransform:'uppercase', fontWeight: 600, marginBottom: 14}}>Policies</div>
              {client.policies === 0 ? (
                <div style={{fontSize: 13, color: theme.colors.textMuted}}>No policies on file.</div>
              ) : (
                <div style={{display:'flex', flexDirection:'column', gap: 10}}>
                  {Array.from({length: client.policies}).map((_, i) => (
                    <div key={i} style={{padding: '12px 14px', border: `1px solid ${theme.colors.border}`, borderRadius: theme.radius.md, background: theme.colors.surface2}}>
                      <div style={{display:'flex', alignItems:'center', justifyContent:'space-between'}}>
                        <div style={{display:'flex', alignItems:'center', gap: 10}}>
                          <span style={{color: theme.colors.brand, display:'inline-flex'}}>{Icons.shield({size: 16})}</span>
                          <div>
                            <div style={{fontFamily: theme.fonts.ui, fontSize: 13, fontWeight: 600, color: theme.colors.text}}>Policy #{100 + client.id*10 + i}</div>
                            <div style={{fontFamily: theme.fonts.ui, fontSize: 11.5, color: theme.colors.textMuted}}>{i === 0 ? 'Medicare Supplement · Plan G' : i === 1 ? 'Part D · SilverScript' : 'Dental & Vision'}</div>
                          </div>
                        </div>
                        <Badge theme={theme} tone="success">Active</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>

            <Card theme={theme}>
              <div style={{fontFamily: theme.fonts.ui, fontSize: 11.5, color: theme.colors.textMuted, letterSpacing: '0.08em', textTransform:'uppercase', fontWeight: 600, marginBottom: 14}}>Recent activity</div>
              <div style={{position:'relative'}}>
                <div style={{position:'absolute', left: 11, top: 4, bottom: 4, width: 1, background: theme.colors.border}}/>
                {acts.map((a, i) => (
                  <div key={i} style={{display:'flex', gap: 12, padding: '8px 0', position:'relative'}}>
                    <div style={{width: 24, height: 24, flexShrink: 0, borderRadius: '50%', background: theme.colors.surface, border: `1px solid ${theme.colors.border}`, display:'flex', alignItems:'center', justifyContent:'center', color: theme.colors.textMuted, zIndex: 1}}>
                      {(kindIcon[a.kind] || Icons.dot)({size: 11})}
                    </div>
                    <div style={{flex: 1, minWidth: 0}}>
                      <div style={{fontFamily: theme.fonts.ui, fontSize: 13, color: theme.colors.text, lineHeight: 1.4}}>{a.text}</div>
                      <div style={{fontFamily: theme.fonts.mono, fontSize: 10.5, color: theme.colors.textSubtle, marginTop: 3}}>{data.mdy(a.date)}</div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>
      )}

      {tab === 'policies' && <PoliciesTab theme={theme} client={client} data={data}/>}

      {tab === 'documents' && (
        <Card theme={theme}>
          <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom: 16}}>
            <div>
              <div style={{fontFamily: theme.fonts.ui, fontSize: 10.5, color: theme.colors.textMuted, letterSpacing: '0.12em', textTransform:'uppercase', fontWeight: 600}}>Documents</div>
              <div style={{fontFamily: theme.fonts.display, fontSize: 22, fontWeight: 600, color: theme.colors.text, letterSpacing:'-0.01em', marginTop: 2}}>{atts.length} attached</div>
            </div>
            <div style={{display:'flex', gap: 8}}>
              <Button theme={theme} variant="ghost" size="sm" leftIcon={Icons.camera}>Scan</Button>
              <Button theme={theme} variant="secondary" size="sm" leftIcon={Icons.upload}>Upload</Button>
            </div>
          </div>
          {atts.length === 0 ? (
            <div style={{border: `1.5px dashed ${theme.colors.borderStrong}`, borderRadius: theme.radius.md, padding: '40px 20px', textAlign:'center', fontFamily: theme.fonts.ui, color: theme.colors.textMuted, fontSize: 13.5}}>
              No documents yet. Upload policy PDFs or capture handwritten notes with the scan button.
            </div>
          ) : (
            <div style={{display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(220px, 1fr))', gap: 14}}>
              {atts.map(a => {
                const hasViewer = !!(data.documents && data.documents[a.id]);
                return (
                  <button key={a.id} onClick={() => hasViewer && onOpenDoc?.(a.id)}
                    disabled={!hasViewer}
                    style={{
                      all: 'unset',
                      display:'flex', flexDirection:'column',
                      padding: 12, background: theme.colors.surface2,
                      border: `1px solid ${theme.colors.border}`, borderRadius: theme.radius.md,
                      cursor: hasViewer ? 'pointer' : 'default',
                      transition: 'box-shadow 120ms, border-color 120ms, transform 120ms',
                    }}
                    onMouseEnter={e => { if (hasViewer) { e.currentTarget.style.borderColor = theme.colors.accent; e.currentTarget.style.transform = 'translateY(-1px)'; e.currentTarget.style.boxShadow = theme.shadow.md; } }}
                    onMouseLeave={e => { e.currentTarget.style.borderColor = theme.colors.border; e.currentTarget.style.transform = 'none'; e.currentTarget.style.boxShadow = 'none'; }}
                  >
                    <PagePlaceholder theme={theme} width="100%" height={156} n={1} title={a.display_name} kind={a.type === 'Handwritten Note' ? 'handwritten' : 'policy'}/>
                    <div style={{marginTop: 10, display:'flex', justifyContent:'space-between', alignItems:'flex-start', gap: 8}}>
                      <div style={{minWidth: 0, flex: 1}}>
                        <div style={{fontFamily: theme.fonts.ui, fontSize: 13, fontWeight: 600, color: theme.colors.text, whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis'}}>{a.display_name}</div>
                        <div style={{fontFamily: theme.fonts.mono, fontSize: 10.5, color: theme.colors.textSubtle, marginTop: 3}}>{a.pages} page{a.pages === 1 ? '' : 's'} · {a.created.split(' ')[0]}</div>
                      </div>
                      <Badge theme={theme} tone={a.type === 'Handwritten Note' ? 'warning' : a.type === 'Policy' ? 'brand' : 'neutral'}>{a.type === 'Handwritten Note' ? 'Note' : a.type}</Badge>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </Card>
      )}

      {tab === 'activity' && (
        <Card theme={theme}>
          <div style={{fontFamily: theme.fonts.ui, fontSize: 10.5, color: theme.colors.textMuted, letterSpacing: '0.12em', textTransform:'uppercase', fontWeight: 600, marginBottom: 4}}>Activity</div>
          <div style={{fontFamily: theme.fonts.display, fontSize: 22, fontWeight: 600, color: theme.colors.text, letterSpacing:'-0.01em', marginBottom: 16}}>Full timeline</div>
          <div style={{position:'relative', paddingLeft: 22}}>
            <div style={{position:'absolute', left: 11, top: 6, bottom: 6, width: 1, background: theme.colors.border}}/>
            {acts.map((a, i) => (
              <div key={i} style={{display:'flex', gap: 14, padding: '10px 0', position:'relative', marginLeft: -22}}>
                <div style={{width: 24, height: 24, flexShrink: 0, borderRadius: '50%', background: theme.colors.surface, border: `1px solid ${theme.colors.accent}`, color: theme.colors.accent, display:'flex', alignItems:'center', justifyContent:'center', zIndex: 1}}>
                  {(kindIcon[a.kind] || Icons.dot)({size: 11})}
                </div>
                <div style={{flex: 1, minWidth: 0, paddingTop: 3}}>
                  <div style={{fontFamily: theme.fonts.ui, fontSize: 14, color: theme.colors.text, lineHeight: 1.45}}>{a.text}</div>
                  <div style={{fontFamily: theme.fonts.mono, fontSize: 11, color: theme.colors.textSubtle, marginTop: 4}}>{data.mdy(a.date)}</div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

// ─── Client Intake form ───────────────────────────────────────
function ClientIntakeScreen({ theme, onSave, onCancel, editing }) {
  const [form, setForm] = useState(editing || {
    full_name: '', dob: '', phone: '', email: '',
    income: '', address: '', city: '', state: '', zip: '',
    notes: '', policy_notes: '', hw_notes: '',
  });
  const [step, setStep] = useState(1);

  function up(k, v) { setForm(f => ({...f, [k]: v})); }

  const steps = [
    { n: 1, l: 'Personal',   d: 'Name, contact, address' },
    { n: 2, l: 'Documents',  d: 'Upload policy or handwritten' },
    { n: 3, l: 'Review',     d: 'Confirm and save' },
  ];

  return (
    <div style={{maxWidth: 960, margin: '0 auto'}}>
      {/* Stepper */}
      <div style={{display:'flex', alignItems:'center', gap: 8, marginBottom: 20}}>
        {steps.map((s, i) => {
          const done = step > s.n;
          const active = step === s.n;
          return (
            <React.Fragment key={s.n}>
              <button onClick={() => setStep(s.n)} style={{
                display:'flex', alignItems:'center', gap: 10, padding: '10px 14px',
                background: active ? theme.colors.surface : 'transparent',
                border: `1px solid ${active ? theme.colors.accent : 'transparent'}`,
                boxShadow: active ? `0 0 0 3px ${theme.colors.accentSoft}` : 'none',
                borderRadius: theme.radius.md, cursor:'pointer',
                fontFamily: theme.fonts.ui,
              }}>
                <div style={{
                  width: 24, height: 24, borderRadius: '50%',
                  background: done ? theme.colors.accent : active ? theme.colors.brand : theme.colors.surface2,
                  color: done || active ? '#fff' : theme.colors.textMuted,
                  border: done || active ? 'none' : `1px solid ${theme.colors.border}`,
                  display:'flex', alignItems:'center', justifyContent:'center',
                  fontSize: 12, fontWeight: 700,
                }}>{done ? Icons.check({size: 12}) : s.n}</div>
                <div style={{textAlign:'left'}}>
                  <div style={{fontSize: 13, fontWeight: 600, color: active ? theme.colors.text : theme.colors.textMuted}}>{s.l}</div>
                  <div style={{fontSize: 11, color: theme.colors.textSubtle}}>{s.d}</div>
                </div>
              </button>
              {i < steps.length - 1 && <div style={{flex: 1, height: 1, background: theme.colors.border}}/>}
            </React.Fragment>
          );
        })}
      </div>

      <Card theme={theme}>
        {step === 1 && (
          <React.Fragment>
            <div style={{marginBottom: 20}}>
              <div style={{fontFamily: theme.fonts.display, fontSize: 20, fontWeight: 600, color: theme.colors.text}}>Personal information</div>
              <div style={{fontFamily: theme.fonts.ui, fontSize: 13, color: theme.colors.textMuted, marginTop: 4}}>Required fields are marked with an asterisk.</div>
            </div>
            <div style={{display:'grid', gridTemplateColumns:'repeat(6, 1fr)', gap: 14}}>
              <Field theme={theme} label="Full name*" span={3}><Input theme={theme} value={form.full_name} onChange={e => up('full_name', e.target.value)} placeholder="Margaret Whitaker"/></Field>
              <Field theme={theme} label="Date of birth" span={2}><Input theme={theme} value={form.dob} onChange={e => up('dob', e.target.value)} placeholder="MM/DD/YYYY"/></Field>
              <Field theme={theme} label="Phone" span={2}><Input theme={theme} value={form.phone} onChange={e => up('phone', e.target.value)} placeholder="(512) 555-0142" leftIcon={Icons.phone}/></Field>
              <Field theme={theme} label="Email" span={4}><Input theme={theme} value={form.email} onChange={e => up('email', e.target.value)} placeholder="m.whitaker@example.com" leftIcon={Icons.mail}/></Field>
              <Field theme={theme} label="Annual income" span={2}><Input theme={theme} value={form.income} onChange={e => up('income', e.target.value)} placeholder="$58,000"/></Field>
              <Field theme={theme} label="Street address" span={4}><Input theme={theme} value={form.address} onChange={e => up('address', e.target.value)} placeholder="4821 Live Oak Ln"/></Field>
              <Field theme={theme} label="ZIP*" span={2}><Input theme={theme} value={form.zip} onChange={e => up('zip', e.target.value)} placeholder="78745" rightAdornment={form.zip.length === 5 ? <Badge theme={theme} tone="success" leftIcon={Icons.check}>Auto</Badge> : null}/></Field>
              <Field theme={theme} label="City" span={3}><Input theme={theme} value={form.city} onChange={e => up('city', e.target.value)} placeholder="Austin"/></Field>
              <Field theme={theme} label="State" span={3}><Input theme={theme} value={form.state} onChange={e => up('state', e.target.value)} placeholder="TX"/></Field>
              <Field theme={theme} label="Notes" span={6}><Textarea theme={theme} value={form.notes} onChange={e => up('notes', e.target.value)} placeholder="Preferred call times, family contacts, health considerations…" rows={3}/></Field>
            </div>
          </React.Fragment>
        )}

        {step === 2 && (
          <React.Fragment>
            <div style={{marginBottom: 20}}>
              <div style={{fontFamily: theme.fonts.display, fontSize: 20, fontWeight: 600, color: theme.colors.text}}>Upload documents</div>
              <div style={{fontFamily: theme.fonts.ui, fontSize: 13, color: theme.colors.textMuted, marginTop: 4}}>Attach a policy and an optional handwritten note. Documents can also be added later.</div>
            </div>

            <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap: 14}}>
              {[
                { title: 'Policy document', desc: 'Upload an existing PDF, or capture multiple photos to merge.', icon: Icons.shield },
                { title: 'Handwritten note', desc: 'Optional — medication list, family details, preferences.', icon: Icons.fileText },
              ].map((d, i) => (
                <div key={i} style={{
                  padding: 20, border: `1.5px dashed ${theme.colors.borderStrong}`,
                  borderRadius: theme.radius.lg, background: theme.colors.surface2,
                  display:'flex', flexDirection:'column', gap: 14,
                }}>
                  <div style={{display:'flex', alignItems:'center', gap: 10}}>
                    <div style={{width: 34, height: 34, borderRadius: theme.radius.md, background: theme.colors.brandSoft, color: theme.colors.brand, display:'flex', alignItems:'center', justifyContent:'center'}}>{d.icon({size: 16})}</div>
                    <div>
                      <div style={{fontFamily: theme.fonts.ui, fontSize: 14, fontWeight: 600, color: theme.colors.text}}>{d.title}</div>
                      <div style={{fontFamily: theme.fonts.ui, fontSize: 12, color: theme.colors.textMuted, marginTop: 1}}>{d.desc}</div>
                    </div>
                  </div>
                  <div style={{display:'flex', gap: 8}}>
                    <Button theme={theme} variant="secondary" size="sm" leftIcon={Icons.upload}>Upload file</Button>
                    <Button theme={theme} variant="ghost" size="sm" leftIcon={Icons.camera}>Capture</Button>
                  </div>
                  <Textarea theme={theme} value={i === 0 ? form.policy_notes : form.hw_notes} onChange={e => up(i === 0 ? 'policy_notes' : 'hw_notes', e.target.value)} placeholder="Notes about this document…" rows={2}/>
                </div>
              ))}
            </div>
          </React.Fragment>
        )}

        {step === 3 && (
          <React.Fragment>
            <div style={{marginBottom: 20}}>
              <div style={{fontFamily: theme.fonts.display, fontSize: 20, fontWeight: 600, color: theme.colors.text}}>Review and save</div>
              <div style={{fontFamily: theme.fonts.ui, fontSize: 13, color: theme.colors.textMuted, marginTop: 4}}>Double-check before saving. You can edit anything afterwards.</div>
            </div>
            <div style={{background: theme.colors.surface2, border: `1px solid ${theme.colors.border}`, borderRadius: theme.radius.md, padding: 18}}>
              <div style={{display:'grid', gridTemplateColumns:'repeat(2, 1fr)', gap: '14px 24px'}}>
                {[
                  ['Name', form.full_name || '—'],
                  ['DOB', form.dob || '—'],
                  ['Phone', form.phone || '—'],
                  ['Email', form.email || '—'],
                  ['Address', `${form.address || '—'}${form.city ? `, ${form.city}` : ''}${form.state ? `, ${form.state}` : ''} ${form.zip || ''}`],
                  ['Income', form.income || '—'],
                ].map(([k, v]) => (
                  <div key={k}>
                    <div style={{fontSize: 11, color: theme.colors.textSubtle, textTransform:'uppercase', letterSpacing:'0.06em', fontWeight: 600}}>{k}</div>
                    <div style={{fontSize: 13.5, color: theme.colors.text, marginTop: 3}}>{v}</div>
                  </div>
                ))}
              </div>
            </div>
          </React.Fragment>
        )}

        <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginTop: 24, paddingTop: 18, borderTop: `1px solid ${theme.colors.border}`}}>
          <Button theme={theme} variant="ghost" onClick={onCancel}>Cancel</Button>
          <div style={{display:'flex', gap: 8}}>
            {step > 1 && <Button theme={theme} variant="secondary" leftIcon={Icons.chevronLeft} onClick={() => setStep(step - 1)}>Back</Button>}
            {step < 3 ? (
              <Button theme={theme} variant="primary" rightIcon={Icons.chevronRight} onClick={() => setStep(step + 1)}>Continue</Button>
            ) : (
              <Button theme={theme} variant="primary" leftIcon={Icons.check} onClick={() => onSave(form)}>Save client</Button>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
}

function Field({ label, children, span = 1, theme }) {
  return (
    <div style={{gridColumn: `span ${span}`}}>
      <label style={{display:'block', fontFamily: theme.fonts.ui, fontSize: 11.5, fontWeight: 600, color: theme.colors.textMuted, marginBottom: 6, letterSpacing:'0.03em'}}>{label}</label>
      {children}
    </div>
  );
}

Object.assign(window, { ClientListScreen, ClientDetailScreen, ClientIntakeScreen });
