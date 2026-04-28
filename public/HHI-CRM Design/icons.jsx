// Shared lucide-style icons + logo marks. Stroke-only, 20px default.

const Icon = ({ d, size = 20, stroke = 'currentColor', strokeWidth = 1.75, fill = 'none', style, children }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24"
       fill={fill} stroke={stroke} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" style={style}>
    {children || <path d={d} />}
  </svg>
);

const Icons = {
  dashboard: (p) => <Icon {...p}><rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/></Icon>,
  users: (p) => <Icon {...p}><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></Icon>,
  userPlus: (p) => <Icon {...p}><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M19 8v6M22 11h-6"/></Icon>,
  search: (p) => <Icon {...p}><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></Icon>,
  bell: (p) => <Icon {...p}><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></Icon>,
  calendar: (p) => <Icon {...p}><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></Icon>,
  phone: (p) => <Icon {...p}><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6A19.79 19.79 0 0 1 2.12 4.18 2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></Icon>,
  mail: (p) => <Icon {...p}><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 7L2 7"/></Icon>,
  mapPin: (p) => <Icon {...p}><path d="M20 10c0 7-8 12-8 12s-8-5-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></Icon>,
  fileText: (p) => <Icon {...p}><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/></Icon>,
  paperclip: (p) => <Icon {...p}><path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></Icon>,
  camera: (p) => <Icon {...p}><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3Z"/><circle cx="12" cy="13" r="3.5"/></Icon>,
  plus: (p) => <Icon {...p}><path d="M12 5v14M5 12h14"/></Icon>,
  chevronRight: (p) => <Icon {...p}><path d="m9 18 6-6-6-6"/></Icon>,
  chevronDown: (p) => <Icon {...p}><path d="m6 9 6 6 6-6"/></Icon>,
  chevronLeft: (p) => <Icon {...p}><path d="m15 18-6-6 6-6"/></Icon>,
  filter: (p) => <Icon {...p}><path d="M22 3H2l8 9.46V19l4 2v-8.54L22 3z"/></Icon>,
  download: (p) => <Icon {...p}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></Icon>,
  upload: (p) => <Icon {...p}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12"/></Icon>,
  eye: (p) => <Icon {...p}><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></Icon>,
  edit: (p) => <Icon {...p}><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></Icon>,
  trash: (p) => <Icon {...p}><path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6h14z"/></Icon>,
  check: (p) => <Icon {...p}><path d="M20 6 9 17l-5-5"/></Icon>,
  x: (p) => <Icon {...p}><path d="M18 6 6 18M6 6l12 12"/></Icon>,
  settings: (p) => <Icon {...p}><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></Icon>,
  logout: (p) => <Icon {...p}><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/></Icon>,
  activity: (p) => <Icon {...p}><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></Icon>,
  heart: (p) => <Icon {...p}><path d="M20.8 4.6a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78L12 21.23l8.84-8.84a5.5 5.5 0 0 0 0-7.78z"/></Icon>,
  shield: (p) => <Icon {...p}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></Icon>,
  dot: (p) => <svg width="6" height="6" viewBox="0 0 6 6"><circle cx="3" cy="3" r="3" fill="currentColor"/></svg>,
  star: (p) => <Icon {...p}><path d="m12 2 3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></Icon>,
};

// ─── Logo marks ───────────────────────────────────────────────
// Simple crest: rounded square, gold cross + HHI
function LogoCrest({ size = 36, navy = '#14254a', gold = '#b48638', cream = '#fbf7ed' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg" style={{display:'block', borderRadius: Math.round(size*0.16)}}>
      <rect width="40" height="40" rx={size*0.16/size*40} fill={navy}/>
      <rect x="3" y="3" width="34" height="34" rx="2" fill="none" stroke={gold} strokeWidth="1.2" opacity="0.7"/>
      <rect x="17" y="7" width="6" height="26" fill={cream}/>
      <rect x="7" y="17" width="26" height="6" fill={cream}/>
      <text x="20" y="24" textAnchor="middle" fontFamily="Georgia, serif" fontWeight="700" fontSize="10" fill={navy} letterSpacing="-0.5">HHI</text>
    </svg>
  );
}

// Monogram: just rounded square with "HHI"
function LogoMono({ size = 32, bg = '#1a1a19', fg = '#fafafa' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg" style={{display:'block'}}>
      <rect width="32" height="32" rx="6" fill={bg}/>
      <text x="16" y="21" textAnchor="middle" fontFamily="ui-sans-serif, Inter, system-ui" fontWeight="700" fontSize="13" fill={fg} letterSpacing="-0.3">HHI</text>
    </svg>
  );
}

// Wordmark logo (warm theme): tiny serif monogram + stacked wordmark
function LogoWordmark({ size = 36, teal = '#2a3f3a', gold = '#a87730' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg" style={{display:'block'}}>
      <circle cx="20" cy="20" r="19" fill="none" stroke={gold} strokeWidth="1"/>
      <circle cx="20" cy="20" r="15" fill={teal}/>
      <text x="20" y="25" textAnchor="middle" fontFamily="'Instrument Serif', Georgia, serif" fontWeight="400" fontSize="16" fill={gold} fontStyle="italic">H</text>
    </svg>
  );
}

function Logo({ theme, size = 36 }) {
  const s = theme.display.logoStyle;
  if (s === 'mono') return <LogoMono size={size} bg={theme.colors.brand} fg={theme.colors.brandText}/>;
  if (s === 'wordmark') return <LogoWordmark size={size} teal={theme.colors.brand} gold={theme.colors.accent}/>;
  return <LogoCrest size={size} navy={theme.colors.brand} gold={theme.colors.accent} cream={theme.colors.surface}/>;
}

Object.assign(window, { Icon, Icons, Logo, LogoCrest, LogoMono, LogoWordmark });
