// Main HHI CRM app — router, state, theme.

const { useState: useS, useEffect: useE, useMemo: useM } = React;

// Default tweak state — parsed by the host for Tweaks persistence.
const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "theme": "classic",
  "showCanvas": true,
  "sidebarCollapsed": false,
  "density": "comfortable"
}/*EDITMODE-END*/;

// CSS injection for keyframes + scrollbar polish.
(function injectCSS() {
  if (document.getElementById('hhi-global')) return;
  const s = document.createElement('style');
  s.id = 'hhi-global';
  s.textContent = `
    @keyframes hhi-toast-in { from { opacity:0; transform:translate(-50%, 8px);} to { opacity:1; transform:translate(-50%, 0);} }
    @keyframes hhi-fade-in { from { opacity:0; transform: translateY(4px);} to { opacity:1; transform: none;} }
    .hhi-enter { animation: hhi-fade-in 220ms cubic-bezier(.2,.7,.3,1); }
    *::-webkit-scrollbar { width: 10px; height: 10px; }
    *::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.12); border-radius: 6px; border: 2px solid transparent; background-clip: padding-box; }
    *::-webkit-scrollbar-thumb:hover { background: rgba(0,0,0,0.22); border: 2px solid transparent; background-clip: padding-box; }
    *::-webkit-scrollbar-track { background: transparent; }
    body, html { margin: 0; padding: 0; height: 100%; }
    #root { height: 100%; }
    button:focus-visible, a:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible {
      outline: 2px solid currentColor; outline-offset: 2px;
    }
  `;
  document.head.appendChild(s);
})();

// ─── Single CRM prototype (one theme instance) ──────────────────
function CRMProtoype({ theme, initialRoute = 'login', data, density, fullBleed }) {
  const [route, setRoute] = useS(initialRoute);
  const [clientId, setClientId] = useS(1);
  const [toast, setToast] = useS(null);

  function openClient(id) { setClientId(id); setRoute('client'); }
  function showToast(msg) { setToast(msg); setTimeout(() => setToast(null), 2600); }

  const client = data.clients.find(c => c.id === clientId) || data.clients[0];

  // Adjust spacing for density if needed (kept simple — scales card padding).
  const themeAdj = useM(() => {
    if (density === 'compact') {
      return {...theme, metrics: {...theme.metrics, cardPad: '16px', topbarHeight: '52px'}};
    }
    return theme;
  }, [theme, density]);

  // ── Routing surface ──
  if (route === 'login') {
    return (
      <div style={{height: '100%', background: themeAdj.colors.bg}}>
        <LoginScreen theme={themeAdj} onLogin={() => setRoute('dashboard')}/>
      </div>
    );
  }

  // Screen configs drive Topbar
  const screens = {
    dashboard: {
      title: 'Dashboard',
      subtitle: 'Thursday, April 23',
      breadcrumbs: null,
      actions: null,
      body: <DashboardScreen theme={themeAdj} data={data} onNav={setRoute} onOpenClient={openClient}/>,
    },
    clients: {
      title: 'Clients',
      subtitle: `${data.clients.length} total`,
      breadcrumbs: [{label:'Workspace'}, {label:'Clients'}],
      actions: null,
      body: <ClientListScreen theme={themeAdj} data={data} onOpenClient={openClient} onNav={setRoute}/>,
    },
    client: {
      title: client.full_name,
      subtitle: `DOB ${client.dob_display}`,
      breadcrumbs: [
        {label:'Clients', onClick:() => setRoute('clients')},
        {label: client.full_name},
      ],
      actions: null,
      body: <ClientDetailScreen theme={themeAdj} client={client} data={data} onBack={() => setRoute('clients')} onEdit={() => setRoute('intake-edit')}/>,
    },
    intake: {
      title: 'New client intake',
      subtitle: 'Capture a new client and their documents',
      breadcrumbs: [{label:'Clients', onClick:() => setRoute('clients')}, {label:'New intake'}],
      actions: null,
      body: <ClientIntakeScreen theme={themeAdj} onSave={() => { showToast('Client saved'); setRoute('clients'); }} onCancel={() => setRoute('clients')}/>,
    },
    'intake-edit': {
      title: `Edit · ${client.full_name}`,
      subtitle: null,
      breadcrumbs: [
        {label:'Clients', onClick:() => setRoute('clients')},
        {label: client.full_name, onClick:() => setRoute('client')},
        {label:'Edit'},
      ],
      actions: null,
      body: <ClientIntakeScreen theme={themeAdj} editing={client} onSave={() => { showToast('Changes saved'); setRoute('client'); }} onCancel={() => setRoute('client')}/>,
    },
  };
  const s = screens[route] || screens.dashboard;

  const activeNav = route.startsWith('intake') ? 'intake' : route === 'client' ? 'clients' : route;

  return (
    <div style={{position:'relative', height: '100%'}}>
      <AppShell
        theme={themeAdj}
        active={activeNav}
        onNav={setRoute}
        title={s.title}
        subtitle={s.subtitle}
        breadcrumbs={s.breadcrumbs}
        topActions={s.actions}
      >
        <div className="hhi-enter" key={route}>{s.body}</div>
      </AppShell>
      <Toast message={toast} visible={!!toast} theme={themeAdj}/>
    </div>
  );
}

// ─── Tweakable root ────────────────────────────────────────────
function App() {
  const [tweaks, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const data = window.HHI_DATA;
  const themes = window.HHI_THEMES;

  // Tweak updates from the protocol (listener is mounted by useTweaks)

  // If showCanvas, render the design_canvas with all 3 themes as artboards.
  // Otherwise render a single full-bleed prototype using the active theme.

  if (tweaks.showCanvas) {
    return (
      <React.Fragment>
        <DesignCanvas title="HHI CRM — design explorations" subtitle="One interactive prototype, three aesthetic directions">
          <DCSection id="variants" title="Aesthetic variations" subtitle="Each artboard is fully interactive. Log in, browse clients, open details, run intake.">
            {['classic','modern','warm'].map(k => (
              <DCArtboard key={k} id={k} label={`${themes[k].name} · ${themes[k].subtitle}`} width={1280} height={820}>
                <div style={{width: 1280, height: 820, overflow:'hidden', background: themes[k].colors.bg}}>
                  <CRMProtoype theme={themes[k]} data={data} density={tweaks.density} fullBleed={false}/>
                </div>
              </DCArtboard>
            ))}
          </DCSection>

          <DCSection id="detail-states" title="Detail-state snapshots" subtitle="Each surface at 1:1 in the Classic theme">
            <DCArtboard id="dash-classic" label="Dashboard · Classic" width={1280} height={820}>
              <div style={{width: 1280, height: 820, overflow:'hidden', background: themes.classic.colors.bg}}>
                <CRMProtoype theme={themes.classic} data={data} initialRoute="dashboard" density={tweaks.density}/>
              </div>
            </DCArtboard>
            <DCArtboard id="list-modern" label="Client list · Modern" width={1280} height={820}>
              <div style={{width: 1280, height: 820, overflow:'hidden', background: themes.modern.colors.bg}}>
                <CRMProtoype theme={themes.modern} data={data} initialRoute="clients" density={tweaks.density}/>
              </div>
            </DCArtboard>
            <DCArtboard id="detail-warm" label="Client detail · Warm" width={1280} height={820}>
              <div style={{width: 1280, height: 820, overflow:'hidden', background: themes.warm.colors.bg}}>
                <CRMProtoype theme={themes.warm} data={data} initialRoute="client" density={tweaks.density}/>
              </div>
            </DCArtboard>
            <DCArtboard id="intake-classic" label="New intake · Classic" width={1280} height={820}>
              <div style={{width: 1280, height: 820, overflow:'hidden', background: themes.classic.colors.bg}}>
                <CRMProtoype theme={themes.classic} data={data} initialRoute="intake" density={tweaks.density}/>
              </div>
            </DCArtboard>
          </DCSection>
        </DesignCanvas>

        <TweaksPanel title="Tweaks">
          <TweakSection label="Layout">
            <TweakToggle label="Design canvas view" value={tweaks.showCanvas} onChange={v => setTweak('showCanvas', v)}/>
            <TweakRadio label="Density" value={tweaks.density} onChange={v => setTweak('density', v)} options={[
              {value:'comfortable', label:'Comfortable'},
              {value:'compact', label:'Compact'},
            ]}/>
          </TweakSection>
          <TweakSection label="Active theme (full-bleed mode)">
            <TweakRadio label="Aesthetic" value={tweaks.theme} onChange={v => setTweak('theme', v)} options={[
              {value:'classic', label:'Classic — Navy + gold, serif'},
              {value:'modern',  label:'Modern — Neutral slate'},
              {value:'warm',    label:'Warm — Cream + teal, editorial'},
            ]}/>
          </TweakSection>
        </TweaksPanel>
      </React.Fragment>
    );
  }

  const theme = themes[tweaks.theme] || themes.classic;
  return (
    <React.Fragment>
      <div style={{height: '100vh', background: theme.colors.bg}}>
        <CRMProtoype theme={theme} data={data} density={tweaks.density} fullBleed={true}/>
      </div>
      <TweaksPanel title="Tweaks">
        <TweakSection label="Layout">
          <TweakToggle label="Design canvas view" value={tweaks.showCanvas} onChange={v => setTweak('showCanvas', v)}/>
          <TweakRadio label="Density" value={tweaks.density} onChange={v => setTweak('density', v)} options={[
            {value:'comfortable', label:'Comfortable'},
            {value:'compact', label:'Compact'},
          ]}/>
        </TweakSection>
        <TweakSection label="Aesthetic">
          <TweakRadio label="Theme" value={tweaks.theme} onChange={v => setTweak('theme', v)} options={[
            {value:'classic', label:'Classic — Navy + gold, serif'},
            {value:'modern',  label:'Modern — Neutral slate'},
            {value:'warm',    label:'Warm — Cream + teal, editorial'},
          ]}/>
        </TweakSection>
      </TweaksPanel>
    </React.Fragment>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
