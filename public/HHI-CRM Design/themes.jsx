// Three aesthetic themes. Each exposes the same token shape so
// the app components don't have to branch on theme.
//
// Token shape:
//   fonts: { display, ui, mono }
//   colors: {
//     bg, surface, surface2, sidebar, sidebarText, sidebarActiveBg, sidebarActiveText,
//     text, textMuted, textSubtle, border, borderStrong,
//     brand, brandText, brandSoft,
//     accent, accentSoft,
//     success, successSoft, warning, warningSoft, danger, dangerSoft
//   }
//   radius: { sm, md, lg, pill }
//   shadow: { sm, md, lg, card }
//   metrics: { sidebarWidth, topbarHeight, avatarBg }
//   display: { logoMark, wordmark, tagline, appName }
//   heroPattern: optional CSS background for accents

window.HHI_THEMES = {

  // ─────────────────────────────────────────────────────────────
  // 1. CLASSIC — deep navy + gold, serif display face.
  //    Feels like the actual Hutchins wordmark.
  // ─────────────────────────────────────────────────────────────
  classic: {
    name: 'Classic',
    subtitle: 'Navy + gold, serif display',
    fonts: {
      display: '"Source Serif 4", "Source Serif Pro", Georgia, serif',
      ui: '"Inter", system-ui, -apple-system, "Segoe UI", sans-serif',
      mono: '"JetBrains Mono", ui-monospace, SFMono-Regular, monospace',
    },
    colors: {
      bg: '#f6f4ef',
      surface: '#ffffff',
      surface2: '#faf8f3',
      sidebar: '#0f1d3a',
      sidebarText: 'rgba(255,255,255,0.78)',
      sidebarActiveBg: 'rgba(210,170,95,0.16)',
      sidebarActiveText: '#f2cf86',
      sidebarBorder: 'rgba(255,255,255,0.08)',
      text: '#111a2e',
      textMuted: '#4a5472',
      textSubtle: '#8690a8',
      border: '#e7e3d7',
      borderStrong: '#d3cdbc',
      brand: '#14254a',
      brandText: '#ffffff',
      brandSoft: 'rgba(20,37,74,0.08)',
      accent: '#b48638',      // gold
      accentSoft: 'rgba(180,134,56,0.14)',
      accentText: '#5f420f',
      success: '#2f7a52',
      successSoft: 'rgba(47,122,82,0.12)',
      warning: '#a9741b',
      warningSoft: 'rgba(169,116,27,0.12)',
      danger: '#a33a2a',
      dangerSoft: 'rgba(163,58,42,0.10)',
      avatarBg: '#14254a',
      avatarText: '#f2cf86',
    },
    radius: { sm: '6px', md: '10px', lg: '14px', pill: '999px' },
    shadow: {
      sm: '0 1px 2px rgba(17,26,46,0.04)',
      md: '0 4px 16px rgba(17,26,46,0.06)',
      lg: '0 18px 44px rgba(17,26,46,0.10)',
      card: '0 1px 0 rgba(231,227,215,0.9), 0 1px 3px rgba(17,26,46,0.04)',
    },
    metrics: {
      sidebarWidth: '248px',
      topbarHeight: '64px',
      cardPad: '22px',
      baseFontSize: '14px',
    },
    display: {
      appName: 'HHI CRM',
      brandName: 'Hutchins',
      brandNameFull: 'Hutchins Health Insurance',
      tagline: 'For All Your Health Care Needs',
      logoStyle: 'crest', // navy + gold crest
    },
  },

  // ─────────────────────────────────────────────────────────────
  // 2. MODERN — Inter everywhere, mostly neutral, navy only where needed.
  //    Linear/Attio-adjacent. Agent-efficient.
  // ─────────────────────────────────────────────────────────────
  modern: {
    name: 'Modern',
    subtitle: 'Neutral slate, navy accents',
    fonts: {
      display: '"Inter", system-ui, -apple-system, sans-serif',
      ui: '"Inter", system-ui, -apple-system, "Segoe UI", sans-serif',
      mono: '"JetBrains Mono", ui-monospace, SFMono-Regular, monospace',
    },
    colors: {
      bg: '#fafafa',
      surface: '#ffffff',
      surface2: '#f5f5f4',
      sidebar: '#ffffff',
      sidebarText: '#4a4a48',
      sidebarActiveBg: '#f1f1ef',
      sidebarActiveText: '#0f1d3a',
      sidebarBorder: '#ececea',
      text: '#1a1a19',
      textMuted: '#6b6b68',
      textSubtle: '#9a9a95',
      border: '#ececea',
      borderStrong: '#d9d9d4',
      brand: '#0f1d3a',
      brandText: '#ffffff',
      brandSoft: 'rgba(15,29,58,0.06)',
      accent: '#0f1d3a',
      accentSoft: 'rgba(15,29,58,0.08)',
      accentText: '#0f1d3a',
      success: '#2b6c4a',
      successSoft: 'rgba(43,108,74,0.10)',
      warning: '#9b6a1c',
      warningSoft: 'rgba(155,106,28,0.10)',
      danger: '#9b2f22',
      dangerSoft: 'rgba(155,47,34,0.09)',
      avatarBg: '#1a1a19',
      avatarText: '#fafafa',
    },
    radius: { sm: '5px', md: '7px', lg: '10px', pill: '999px' },
    shadow: {
      sm: '0 1px 2px rgba(0,0,0,0.04)',
      md: '0 2px 8px rgba(0,0,0,0.05)',
      lg: '0 8px 28px rgba(0,0,0,0.08)',
      card: '0 0 0 1px #ececea',
    },
    metrics: {
      sidebarWidth: '240px',
      topbarHeight: '56px',
      cardPad: '20px',
      baseFontSize: '13.5px',
    },
    display: {
      appName: 'HHI',
      brandName: 'HHI',
      brandNameFull: 'Hutchins Health Insurance',
      tagline: 'Medicare & Health Insurance CRM',
      logoStyle: 'mono', // monogram
    },
  },

  // ─────────────────────────────────────────────────────────────
  // 3. WARM — cream background, deep teal + muted gold, larger type.
  //    Friendly for a senior-serving agency.
  // ─────────────────────────────────────────────────────────────
  warm: {
    name: 'Warm',
    subtitle: 'Cream, teal, editorial',
    fonts: {
      display: '"Instrument Serif", Georgia, serif',
      ui: '"Geist", "Inter", system-ui, -apple-system, sans-serif',
      mono: '"JetBrains Mono", ui-monospace, monospace',
    },
    colors: {
      bg: '#f5efe4',
      surface: '#fbf7ed',
      surface2: '#efe6d4',
      sidebar: '#2a3f3a',
      sidebarText: 'rgba(245,239,228,0.82)',
      sidebarActiveBg: 'rgba(217,172,98,0.18)',
      sidebarActiveText: '#f0d8a3',
      sidebarBorder: 'rgba(245,239,228,0.10)',
      text: '#1f241f',
      textMuted: '#5d645a',
      textSubtle: '#8c9285',
      border: '#e2dac5',
      borderStrong: '#cdc2a5',
      brand: '#2a3f3a',        // deep teal
      brandText: '#fbf7ed',
      brandSoft: 'rgba(42,63,58,0.10)',
      accent: '#a87730',       // muted gold
      accentSoft: 'rgba(168,119,48,0.14)',
      accentText: '#5a3f15',
      success: '#4a6e3f',
      successSoft: 'rgba(74,110,63,0.14)',
      warning: '#a8712a',
      warningSoft: 'rgba(168,113,42,0.14)',
      danger: '#9d3f2e',
      dangerSoft: 'rgba(157,63,46,0.12)',
      avatarBg: '#2a3f3a',
      avatarText: '#f0d8a3',
    },
    radius: { sm: '8px', md: '14px', lg: '20px', pill: '999px' },
    shadow: {
      sm: '0 1px 2px rgba(42,63,58,0.05)',
      md: '0 6px 20px rgba(42,63,58,0.08)',
      lg: '0 22px 52px rgba(42,63,58,0.12)',
      card: '0 1px 0 rgba(226,218,197,0.9), 0 4px 12px rgba(42,63,58,0.05)',
    },
    metrics: {
      sidebarWidth: '256px',
      topbarHeight: '68px',
      cardPad: '24px',
      baseFontSize: '15px',
    },
    display: {
      appName: 'Hutchins CRM',
      brandName: 'Hutchins',
      brandNameFull: 'Hutchins Health Insurance',
      tagline: 'For All Your Health Care Needs',
      logoStyle: 'wordmark',
    },
  },
};
