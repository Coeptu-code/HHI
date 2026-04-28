// Seed data for the HHI CRM prototype.
// Realistic-ish names + Medicare-adjacent ages (skewed to near-65).

window.HHI_DATA = (function () {
  const today = new Date(2026, 3, 23); // April 23, 2026 (matches project "today")

  function d(y, m, day) { return new Date(y, m - 1, day); }
  function mdy(dt) {
    return String(dt.getMonth() + 1).padStart(2, '0') + '/' +
           String(dt.getDate()).padStart(2, '0') + '/' +
           dt.getFullYear();
  }
  function daysBetween(a, b) {
    return Math.round((b - a) / 86400000);
  }

  const clients = [
    { id: 1,  full_name: 'Margaret Whitaker',  dob: d(1961, 7, 12),  phone: '(512) 555-0142', email: 'm.whitaker@hotmail.com',   income: '$58,000', address: '4821 Live Oak Ln',     city: 'Austin',       state: 'TX', zip: '78745', notes: 'Husband George also interested in supplement plan. Prefers afternoon calls.', created: d(2026, 4, 22), policies: 2, attachments: 3, hw_notes: 1 },
    { id: 2,  full_name: 'Robert Chen',        dob: d(1961, 2, 28),  phone: '(408) 555-0199', email: 'rchen1961@gmail.com',      income: '$72,400', address: '1130 Pinewood Dr',     city: 'San Jose',     state: 'CA', zip: '95129', notes: 'Currently on employer plan until July. Retiring August 1.',              created: d(2026, 4, 21), policies: 1, attachments: 2, hw_notes: 0 },
    { id: 3,  full_name: 'Dolores Fitzgerald', dob: d(1961, 5, 3),   phone: '(813) 555-0117', email: 'dolores.f@yahoo.com',      income: '$41,200', address: '219 Bayshore Ct',      city: 'Tampa',        state: 'FL', zip: '33606', notes: 'Widow. Daughter Janet (813-555-0420) helps with paperwork.',             created: d(2026, 4, 20), policies: 1, attachments: 4, hw_notes: 2 },
    { id: 4,  full_name: 'Harold Washington',  dob: d(1960, 11, 19), phone: '(312) 555-0163', email: 'hwashington@outlook.com',  income: '$65,000', address: '8844 S. Cornell Ave',  city: 'Chicago',      state: 'IL', zip: '60617', notes: 'Diabetic — needs Part D with good insulin coverage.',                     created: d(2026, 4, 18), policies: 3, attachments: 5, hw_notes: 0 },
    { id: 5,  full_name: 'Patricia Nguyen',    dob: d(1961, 9, 8),   phone: '(714) 555-0188', email: 'patnguyen@gmail.com',      income: '$52,800', address: '612 Orange Grove Blvd',city: 'Garden Grove', state: 'CA', zip: '92840', notes: '',                                                                        created: d(2026, 4, 17), policies: 0, attachments: 1, hw_notes: 1 },
    { id: 6,  full_name: 'James O\u2019Brien', dob: d(1960, 12, 30), phone: '(617) 555-0124', email: 'jim.obrien@comcast.net',   income: '$89,500', address: '47 Hancock St',        city: 'Boston',       state: 'MA', zip: '02114', notes: 'Veteran — may be eligible for VA coordination.',                          created: d(2026, 4, 15), policies: 1, attachments: 2, hw_notes: 0 },
    { id: 7,  full_name: 'Linda Brooks',       dob: d(1961, 4, 14),  phone: '(404) 555-0152', email: 'lbrooks@bellsouth.net',    income: '$38,700', address: '1502 Peachtree Way',   city: 'Atlanta',      state: 'GA', zip: '30309', notes: 'Qualifies for LIS / Extra Help. Follow up after 5/1.',                     created: d(2026, 4, 14), policies: 0, attachments: 0, hw_notes: 0 },
    { id: 8,  full_name: 'Thomas Kowalski',    dob: d(1961, 1, 25),  phone: '(313) 555-0176', email: 'tkowalski@aol.com',        income: '$61,000', address: '903 Warren Ave',       city: 'Detroit',      state: 'MI', zip: '48207', notes: 'Switching from BCBS. Wants same PCP — Dr. Marek.',                         created: d(2026, 4, 12), policies: 2, attachments: 3, hw_notes: 1 },
    { id: 9,  full_name: 'Evelyn Rodriguez',   dob: d(1961, 6, 21),  phone: '(305) 555-0131', email: 'evelyn.r@hotmail.com',     income: '$44,100', address: '2280 SW 32nd Ave',     city: 'Miami',        state: 'FL', zip: '33145', notes: 'Bilingual (Spanish preferred). Medications from Mexico — verify formulary.',created: d(2026, 4, 10), policies: 1, attachments: 2, hw_notes: 1 },
    { id: 10, full_name: 'Frank Delacroix',    dob: d(1960, 10, 9),  phone: '(504) 555-0145', email: 'fdelacroix@cox.net',       income: '$77,300', address: '3109 Magazine St',     city: 'New Orleans',  state: 'LA', zip: '70115', notes: 'Snowbird — winters in AZ. Needs nationwide network.',                      created: d(2026, 4, 9),  policies: 2, attachments: 4, hw_notes: 0 },
    { id: 11, full_name: 'Susan Abernathy',    dob: d(1961, 3, 17),  phone: '(503) 555-0167', email: 's.abernathy@gmail.com',    income: '$55,600', address: '1488 NE Alameda',      city: 'Portland',     state: 'OR', zip: '97212', notes: '',                                                                        created: d(2026, 4, 7),  policies: 1, attachments: 1, hw_notes: 0 },
    { id: 12, full_name: 'Richard Blackwell',  dob: d(1961, 8, 2),   phone: '(206) 555-0138', email: 'rblackwell@msn.com',       income: '$82,000', address: '721 Queen Anne Ave N', city: 'Seattle',      state: 'WA', zip: '98109', notes: 'Wife enrolled last year — same plan preferred.',                          created: d(2026, 4, 5),  policies: 1, attachments: 2, hw_notes: 1 },
    { id: 13, full_name: 'Barbara Lindstrom',  dob: d(1962, 1, 11),  phone: '(612) 555-0191', email: 'blindstrom@gmail.com',     income: '$49,900', address: '2814 Hennepin Ave',    city: 'Minneapolis',  state: 'MN', zip: '55408', notes: 'Not yet 65 — planning ahead.',                                            created: d(2026, 4, 3),  policies: 0, attachments: 0, hw_notes: 0 },
    { id: 14, full_name: 'Gerald Pemberton',   dob: d(1960, 8, 27),  phone: '(702) 555-0114', email: 'gpemberton@yahoo.com',     income: '$93,200', address: '6501 W Sahara Ave',    city: 'Las Vegas',    state: 'NV', zip: '89146', notes: 'Already on Medicare. Interested in supplement upgrade.',                   created: d(2026, 3, 30), policies: 3, attachments: 6, hw_notes: 2 },
    { id: 15, full_name: 'Carol Whitfield',    dob: d(1961, 11, 4),  phone: '(919) 555-0187', email: 'cwhitfield@nc.rr.com',     income: '$47,500', address: '812 Oberlin Rd',       city: 'Raleigh',      state: 'NC', zip: '27605', notes: 'Referred by Margaret Whitaker (sister-in-law).',                          created: d(2026, 3, 28), policies: 0, attachments: 1, hw_notes: 0 },
    { id: 16, full_name: 'Steven Ashford',     dob: d(1961, 2, 6),   phone: '(215) 555-0128', email: 'sashford@verizon.net',     income: '$68,400', address: '1907 Spruce St',       city: 'Philadelphia', state: 'PA', zip: '19103', notes: '',                                                                        created: d(2026, 3, 25), policies: 1, attachments: 2, hw_notes: 0 },
    { id: 17, full_name: 'Diane Kowalczyk',    dob: d(1960, 9, 15),  phone: '(414) 555-0172', email: 'dkowalczyk@gmail.com',     income: '$54,000', address: '3306 N Downer Ave',    city: 'Milwaukee',    state: 'WI', zip: '53211', notes: 'Already enrolled. Annual review due September.',                          created: d(2026, 3, 20), policies: 2, attachments: 3, hw_notes: 1 },
    { id: 18, full_name: 'Anthony Marino',     dob: d(1961, 10, 28), phone: '(718) 555-0109', email: 'tmarino@aol.com',          income: '$71,800', address: '2284 86th St',         city: 'Brooklyn',     state: 'NY', zip: '11214', notes: 'Needs plan accepted by NYU Langone.',                                     created: d(2026, 3, 18), policies: 0, attachments: 2, hw_notes: 1 },
  ];

  // Compute turning-65 + days-until for each
  clients.forEach(c => {
    const turn = new Date(c.dob.getFullYear() + 65, c.dob.getMonth(), c.dob.getDate());
    c.turns_65_on = turn;
    c.days_until_65 = daysBetween(today, turn);
    c.dob_display = mdy(c.dob);
    c.turns_65_display = mdy(turn);
    c.created_display = mdy(c.created);
    // Age as of today
    let age = today.getFullYear() - c.dob.getFullYear();
    const m = today.getMonth() - c.dob.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < c.dob.getDate())) age--;
    c.age = age;
    // First initial + last
    const parts = c.full_name.split(' ');
    c.initials = (parts[0][0] + (parts[parts.length - 1][0] || '')).toUpperCase();
  });

  // Last-7-days series for the "clients added" card
  function lastNDays(n) {
    const out = [];
    for (let i = n - 1; i >= 0; i--) {
      const day = new Date(today);
      day.setDate(today.getDate() - i);
      const count = clients.filter(c =>
        c.created.getFullYear() === day.getFullYear() &&
        c.created.getMonth() === day.getMonth() &&
        c.created.getDate() === day.getDate()
      ).length;
      out.push({
        day: day,
        label: day.toLocaleDateString('en-US', { weekday: 'short' }),
        sublabel: (day.getMonth() + 1) + '/' + day.getDate(),
        count: count,
      });
    }
    const max = Math.max(...out.map(p => p.count), 1);
    out.forEach(p => { p.pct = Math.round((p.count / max) * 100); });
    return out;
  }

  const added_series = lastNDays(7);
  const added_total = added_series.reduce((s, p) => s + p.count, 0);

  const turning_65 = clients
    .filter(c => c.days_until_65 >= 0 && c.days_until_65 <= 90)
    .sort((a, b) => a.days_until_65 - b.days_until_65);

  // Activity/events per client (for detail page)
  const activity = {
    1: [
      { date: d(2026, 4, 22), kind: 'note',     text: 'Initial intake call. Discussed Plan G vs Plan N.' },
      { date: d(2026, 4, 22), kind: 'doc',      text: 'Uploaded driver\u2019s license scan (2 pages).' },
      { date: d(2026, 4, 20), kind: 'call',     text: 'Left voicemail re: enrollment window.' },
    ],
    2: [
      { date: d(2026, 4, 21), kind: 'note',     text: 'Retiring August 1. Plan needs to start 8/1.' },
      { date: d(2026, 4, 19), kind: 'email',    text: 'Sent quote comparison (MAPD vs Supplement).' },
    ],
    3: [
      { date: d(2026, 4, 20), kind: 'note',     text: 'Daughter Janet to scan policy docs this week.' },
      { date: d(2026, 4, 18), kind: 'doc',      text: 'Received handwritten medication list.' },
      { date: d(2026, 4, 15), kind: 'call',     text: 'Intake — 45 min.' },
    ],
  };

  const attachments = {
    1: [
      { id: 101, display_name: 'Drivers License',      type: 'Other',            pages: 2, created: '04/22/2026 10:14 AM' },
      { id: 102, display_name: 'Current BCBS Policy',  type: 'Policy',           pages: 11, created: '04/22/2026 09:02 AM' },
      { id: 103, display_name: 'Medication List',      type: 'Handwritten Note', pages: 1, created: '04/22/2026 09:05 AM' },
    ],
    2: [
      { id: 201, display_name: 'Employer Plan SBC',    type: 'Policy',           pages: 6, created: '04/21/2026 02:30 PM' },
      { id: 202, display_name: 'Retirement letter',    type: 'Other',            pages: 1, created: '04/21/2026 02:31 PM' },
    ],
    3: [
      { id: 301, display_name: 'Current Advantage Plan',type: 'Policy',          pages: 14, created: '04/20/2026 11:00 AM' },
      { id: 302, display_name: 'Med List (handwritten)',type: 'Handwritten Note',pages: 1, created: '04/18/2026 03:45 PM' },
      { id: 303, display_name: 'SSA Award Letter',     type: 'Other',            pages: 2, created: '04/18/2026 03:46 PM' },
      { id: 304, display_name: 'Part B Card',          type: 'Other',            pages: 1, created: '04/15/2026 04:10 PM' },
    ],
  };

  // ─── Policies by client ───────────────────────────────────────
  const policies = {
    1: [
      { id: 'P-1041', type: 'Medicare Supplement', plan: 'Plan G',        carrier: 'Mutual of Omaha',     policy_number: 'MOO-8821-4471', premium: 142.50, effective: d(2026, 8, 1),  renewal: d(2027, 8, 1), status: 'Pending', agent_commission: '12%' },
      { id: 'P-1042', type: 'Part D',              plan: 'SilverScript Choice', carrier: 'Aetna · SilverScript', policy_number: 'SS-44102-B', premium: 38.70,  effective: d(2026, 8, 1),  renewal: d(2027, 1, 1), status: 'Pending', agent_commission: 'Level' },
    ],
    2: [
      { id: 'P-1028', type: 'Employer Group',      plan: 'BCBS PPO',      carrier: 'Blue Cross Blue Shield', policy_number: 'BCBS-2210-EE', premium: 412.00, effective: d(2024, 1, 1), renewal: d(2026, 7, 31), status: 'Terminating', agent_commission: 'N/A' },
    ],
    3: [
      { id: 'P-0987', type: 'Medicare Advantage',  plan: 'AARP MedicareComplete', carrier: 'UnitedHealthcare', policy_number: 'UHC-7740-X', premium: 0.00, effective: d(2025, 1, 1), renewal: d(2026, 12, 31), status: 'Active', agent_commission: '$573/yr' },
    ],
    4: [
      { id: 'P-0921', type: 'Medicare Supplement', plan: 'Plan G',        carrier: 'Cigna',                policy_number: 'CGN-5521-9',  premium: 138.00, effective: d(2025, 12, 1), renewal: d(2026, 12, 1), status: 'Active', agent_commission: '12%' },
      { id: 'P-0922', type: 'Part D',              plan: 'WellCare Value Script', carrier: 'WellCare',      policy_number: 'WC-9921-R',   premium: 0.00,   effective: d(2025, 12, 1), renewal: d(2026, 12, 31), status: 'Active', agent_commission: 'Level' },
      { id: 'P-0923', type: 'Dental, Vision, Hearing', plan: 'MOO DVH Premier', carrier: 'Mutual of Omaha', policy_number: 'MOO-DVH-2210', premium: 47.00,  effective: d(2025, 12, 1), renewal: d(2026, 12, 1), status: 'Active', agent_commission: '$90/yr' },
    ],
  };

  // ─── Page-level detail for the document viewer ─────────────────
  // Each "page" is a placeholder (striped SVG). For handwritten notes
  // we stage a transcript block so the viewer can show OCR'd / typed text
  // alongside the placeholder page.
  const documents = {
    102: { // Margaret Whitaker — BCBS Policy (multi-page policy doc)
      id: 102, client_id: 1, display_name: 'Current BCBS Policy', type: 'Policy',
      created: 'Apr 22, 2026 · 9:02 AM', uploaded_by: 'Jamie Carter',
      source: 'Uploaded PDF', size: '2.4 MB', pages_count: 11,
      tags: ['BCBS','PPO','active','terminating 7/31'],
      pages: Array.from({length: 11}, (_, i) => ({
        n: i+1, kind: 'policy',
        title: [
          'Cover sheet', 'Plan summary', 'Benefits table', 'Benefits table (cont.)',
          'Prescription coverage', 'Network hospitals', 'Claims procedure',
          'Terms & conditions', 'Exclusions', 'Contact & appeals', 'Signature block',
        ][i],
      })),
    },
    103: { // Margaret Whitaker — handwritten medication list
      id: 103, client_id: 1, display_name: 'Medication List', type: 'Handwritten Note',
      created: 'Apr 22, 2026 · 9:05 AM', uploaded_by: 'Jamie Carter',
      source: 'iPhone camera · 1 photo', size: '1.1 MB', pages_count: 1,
      tags: ['medications','handwritten','transcribed'],
      pages: [{
        n: 1, kind: 'handwritten', title: 'Medication list (handwritten)',
        transcript: [
          'Metformin 500 mg — 2× daily (AM, PM)',
          'Lisinopril 10 mg — 1× daily (AM)',
          'Atorvastatin 20 mg — 1× daily (PM)',
          'Levothyroxine 50 mcg — 1× daily (AM, empty stomach)',
          'Aspirin 81 mg — 1× daily',
          'Vitamin D3 1000 IU — 1× daily',
        ],
        ocr_confidence: 0.92,
      }],
    },
    301: {
      id: 301, client_id: 3, display_name: 'Current Advantage Plan', type: 'Policy',
      created: 'Apr 20, 2026 · 11:00 AM', uploaded_by: 'Jamie Carter',
      source: 'Scanned · 14 photos merged', size: '4.8 MB', pages_count: 14,
      tags: ['UHC','Advantage','active'],
      pages: Array.from({length: 14}, (_, i) => ({ n: i+1, kind: 'policy', title: `Page ${i+1}` })),
    },
    302: {
      id: 302, client_id: 3, display_name: 'Med List (handwritten)', type: 'Handwritten Note',
      created: 'Apr 18, 2026 · 3:45 PM', uploaded_by: 'Jamie Carter',
      source: 'iPhone camera · 1 photo', size: '0.9 MB', pages_count: 1,
      tags: ['medications','handwritten'],
      pages: [{
        n: 1, kind: 'handwritten', title: 'Medication list (handwritten)',
        transcript: [
          'Amlodipine 5 mg — daily',
          'Gabapentin 300 mg — 3× daily',
          'Furosemide 20 mg — daily',
          'Potassium Cl 10 mEq — daily',
        ],
        ocr_confidence: 0.86,
      }],
    },
  };

  return {
    today,
    clients,
    added_series,
    added_total,
    turning_65,
    activity,
    attachments,
    policies,
    documents,
    mdy,
  };
})();
