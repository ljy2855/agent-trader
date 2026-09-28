"""HTML template for the Kiwoom dashboard."""

DASHBOARD_HTML = r"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Kiwoom Trading Dashboard</title>
  <style>
    :root {
      --bg: #f3efe6;
      --panel: rgba(255, 253, 248, 0.88);
      --panel-strong: rgba(255, 255, 255, 0.95);
      --line: rgba(33, 38, 45, 0.10);
      --ink: #18212f;
      --muted: #5f6979;
      --positive: #0c8f62;
      --negative: #c04f39;
      --warning: #b9841f;
      --accent: #153552;
      --accent-soft: rgba(21, 53, 82, 0.08);
      --shadow: 0 20px 60px rgba(24, 33, 47, 0.10);
      --radius-xl: 28px;
      --radius-lg: 20px;
      --radius-md: 14px;
      --radius-sm: 10px;
      --display-font: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Palatino, serif;
      --body-font: "Avenir Next", "Segoe UI Variable", "Noto Sans KR", sans-serif;
      --mono-font: "IBM Plex Mono", "SFMono-Regular", Consolas, monospace;
    }

    * {
      box-sizing: border-box;
    }

    html {
      scroll-behavior: smooth;
    }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: var(--body-font);
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(222, 201, 149, 0.36), transparent 28%),
        radial-gradient(circle at top right, rgba(180, 214, 224, 0.34), transparent 24%),
        linear-gradient(180deg, #f7f3ea 0%, #f1ede5 52%, #edf2f0 100%);
    }

    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background-image:
        linear-gradient(rgba(24, 33, 47, 0.025) 1px, transparent 1px),
        linear-gradient(90deg, rgba(24, 33, 47, 0.025) 1px, transparent 1px);
      background-size: 32px 32px;
      mask-image: radial-gradient(circle at center, black 48%, transparent 86%);
    }

    .shell {
      width: min(1320px, calc(100vw - 28px));
      margin: 0 auto;
      padding: 24px 0 56px;
    }

    .hero,
    .panel,
    .toolbar {
      background: var(--panel);
      backdrop-filter: blur(18px);
      border: 1px solid var(--line);
      box-shadow: var(--shadow);
      border-radius: var(--radius-xl);
    }

    .tab-nav {
      display: flex;
      gap: 4px;
      margin: 0 0 18px;
      padding: 6px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow);
      width: fit-content;
    }
    .tab-link {
      padding: 9px 18px;
      border-radius: var(--radius-md);
      font-size: 14px;
      font-weight: 600;
      text-decoration: none;
      color: var(--muted);
      transition: background 0.15s, color 0.15s;
      cursor: pointer;
      user-select: none;
    }
    .tab-link:hover { color: var(--ink); }
    .tab-link.active {
      background: var(--accent);
      color: #fff;
    }

    .view { display: none; }
    .view.active { display: block; }

    .hero {
      display: grid;
      grid-template-columns: 1.4fr 1fr;
      gap: 22px;
      padding: 26px;
      margin-bottom: 20px;
    }

    .eyebrow {
      margin: 0 0 12px;
      color: var(--muted);
      font-size: 12px;
      letter-spacing: 0.24em;
      text-transform: uppercase;
    }

    h1 {
      margin: 0;
      font-family: var(--display-font);
      font-size: clamp(2.35rem, 5.2vw, 4.2rem);
      line-height: 0.95;
      letter-spacing: -0.04em;
    }

    .hero-copy {
      margin: 16px 0 0;
      max-width: 54ch;
      color: var(--muted);
      line-height: 1.65;
      font-size: 1rem;
    }

    .identity-strip {
      margin-top: 20px;
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      align-items: center;
    }

    .pill,
    .meta-pill,
    .status-pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      font-size: 0.92rem;
      border: 1px solid rgba(24, 33, 47, 0.08);
      background: rgba(255, 255, 255, 0.72);
    }

    .pill strong,
    .meta-pill strong {
      font-weight: 700;
    }

    .pill.env-mock {
      background: rgba(185, 132, 31, 0.10);
      color: #8a6116;
    }

    .pill.env-live {
      background: rgba(12, 143, 98, 0.10);
      color: var(--positive);
    }

    .hero-side {
      display: grid;
      gap: 12px;
      align-content: start;
    }

    .side-box {
      padding: 16px 18px;
      border-radius: var(--radius-lg);
      border: 1px solid rgba(24, 33, 47, 0.08);
      background: rgba(255, 255, 255, 0.62);
    }

    .side-box .label {
      display: block;
      margin-bottom: 6px;
      color: var(--muted);
      font-size: 12px;
      letter-spacing: 0.18em;
      text-transform: uppercase;
    }

    .side-box .value {
      font-size: 0.98rem;
      line-height: 1.5;
      word-break: break-word;
    }

    .toolbar {
      margin-bottom: 20px;
      padding: 16px 18px;
    }

    .toolbar form {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, auto));
      gap: 12px;
      align-items: end;
    }

    .field {
      display: grid;
      gap: 8px;
      min-width: 150px;
    }

    .field label,
    .toggle {
      color: var(--muted);
      font-size: 12px;
      letter-spacing: 0.16em;
      text-transform: uppercase;
    }

    .field input[type="text"] {
      width: 100%;
      padding: 11px 12px;
      border-radius: var(--radius-sm);
      border: 1px solid rgba(24, 33, 47, 0.12);
      background: rgba(255, 255, 255, 0.85);
      font: inherit;
      color: var(--ink);
    }

    .toggle-wrap {
      display: flex;
      align-items: center;
      min-height: 46px;
      gap: 10px;
      padding: 0 6px;
    }

    .toggle-wrap input {
      width: 18px;
      height: 18px;
      accent-color: var(--accent);
    }

    .toolbar button {
      height: 46px;
      border: 0;
      border-radius: 999px;
      padding: 0 18px;
      font: inherit;
      font-weight: 700;
      color: white;
      background: linear-gradient(135deg, #173552 0%, #275174 100%);
      box-shadow: 0 12px 26px rgba(23, 53, 82, 0.25);
      cursor: pointer;
    }

    .toolbar-note {
      margin-top: 10px;
      color: var(--muted);
      font-size: 0.92rem;
    }

    .error-banner {
      margin-bottom: 16px;
      padding: 14px 16px;
      border-radius: var(--radius-lg);
      border: 1px solid rgba(192, 79, 57, 0.16);
      background: rgba(192, 79, 57, 0.10);
      color: var(--negative);
    }

    .overview-grid,
    .content-grid {
      display: grid;
      gap: 18px;
      margin-bottom: 20px;
    }

    .overview-grid {
      grid-template-columns: 1.55fr 1fr;
    }

    .content-grid {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }

    .panel {
      padding: 18px;
    }

    .span-2 {
      grid-column: span 2;
    }

    .span-3 {
      grid-column: span 3;
    }

    .section-head {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 12px;
      margin-bottom: 16px;
    }

    .section-head h2,
    .section-head h3 {
      margin: 0;
      font-family: var(--display-font);
      letter-spacing: -0.03em;
    }

    .section-head h2 {
      font-size: 2rem;
      line-height: 1;
    }

    .section-head h3 {
      font-size: 1.45rem;
      line-height: 1;
    }

    .section-kicker {
      margin: 0 0 6px;
      color: var(--muted);
      font-size: 12px;
      letter-spacing: 0.18em;
      text-transform: uppercase;
    }

    .section-subtitle {
      margin: 0;
      color: var(--muted);
      font-size: 0.95rem;
      line-height: 1.5;
    }

    .metric-grid,
    .mini-metric-grid {
      display: grid;
      gap: 12px;
    }

    .metric-grid {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }

    .mini-metric-grid {
      grid-template-columns: repeat(4, minmax(0, 1fr));
    }

    .metric-card,
    .mini-metric,
    .focus-item,
    .notice {
      border: 1px solid rgba(24, 33, 47, 0.08);
      border-radius: var(--radius-lg);
      background: rgba(255, 255, 255, 0.72);
    }

    .metric-card {
      padding: 16px;
      min-height: 122px;
      display: grid;
      align-content: start;
      gap: 10px;
    }

    .metric-card .label,
    .mini-metric .label,
    .focus-item .label {
      color: var(--muted);
      font-size: 12px;
      letter-spacing: 0.16em;
      text-transform: uppercase;
    }

    .metric-card .value {
      font-family: var(--display-font);
      font-size: clamp(1.7rem, 3vw, 2.4rem);
      line-height: 1;
      letter-spacing: -0.04em;
    }

    .metric-card.highlight {
      grid-column: 1 / -1;
      background: linear-gradient(135deg, rgba(21, 53, 82, 0.08), rgba(12, 143, 98, 0.06));
      border: 1px solid rgba(21, 53, 82, 0.18);
    }

    .metric-card.highlight .label {
      color: var(--accent);
      font-weight: 700;
    }

    .metric-card.highlight .value {
      font-size: clamp(2.2rem, 4vw, 3.2rem);
      color: var(--accent);
    }

    .metric-card .detail {
      font-size: 12px;
      color: var(--muted);
      letter-spacing: 0.02em;
      margin-top: 4px;
    }

    .mini-metric {
      padding: 14px;
      display: grid;
      gap: 8px;
    }

    .mini-metric .value {
      font-size: 1.05rem;
      font-weight: 700;
    }

    .mini-metric .detail {
      font-size: 0.78rem;
      color: var(--muted);
      letter-spacing: 0.02em;
      line-height: 1.4;
    }

    .mini-metric.highlight {
      background: linear-gradient(135deg, var(--accent-soft), rgba(255, 255, 255, 0.95));
      border: 1px solid rgba(21, 53, 82, 0.18);
      box-shadow: 0 8px 24px rgba(24, 33, 47, 0.08);
    }

    .mini-metric.highlight .label {
      color: var(--accent);
      font-weight: 700;
    }

    .mini-metric.highlight .value {
      font-size: 1.3rem;
    }

    .panel-toolbar {
      padding: 8px 12px 4px;
      display: flex;
      gap: 8px;
    }

    .panel-search {
      flex: 1;
      padding: 8px 12px;
      border-radius: var(--radius-sm);
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.7);
      font: inherit;
      color: var(--ink);
      transition: border-color 120ms ease, background 120ms ease;
    }

    .panel-search:focus {
      outline: none;
      border-color: var(--accent);
      background: var(--panel-strong);
    }

    .empty-cell {
      text-align: center;
      color: var(--muted);
      padding: 24px;
      font-style: italic;
    }

    .pagination {
      display: flex;
      gap: 4px;
      justify-content: center;
      align-items: center;
      padding: 12px 8px;
      flex-wrap: wrap;
    }

    .pagination button {
      min-width: 32px;
      padding: 6px 10px;
      border-radius: var(--radius-sm);
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.7);
      color: var(--ink);
      font: inherit;
      cursor: pointer;
      transition: background 120ms ease, border-color 120ms ease;
    }

    .pagination button:not(:disabled):hover {
      border-color: var(--accent);
      background: var(--accent-soft);
    }

    .pagination button:disabled {
      opacity: 0.4;
      cursor: not-allowed;
    }

    .pagination .page.active {
      background: var(--accent);
      color: #fff;
      border-color: var(--accent);
      font-weight: 600;
    }

    .focus-list {
      display: grid;
      gap: 10px;
      margin-bottom: 12px;
    }

    .focus-item {
      padding: 14px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
    }

    .focus-item strong {
      font-size: 1.1rem;
    }

    .notice {
      padding: 14px;
      line-height: 1.6;
    }

    .notice strong {
      display: block;
      margin-bottom: 6px;
    }

    .notice.ok {
      background: rgba(12, 143, 98, 0.08);
      color: var(--positive);
    }

    .notice.warn {
      background: rgba(185, 132, 31, 0.10);
      color: #8a6116;
    }

    .notice.error {
      background: rgba(192, 79, 57, 0.10);
      color: var(--negative);
    }

    .notice ul {
      margin: 0;
      padding-left: 18px;
    }

    .table-meta {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      margin-bottom: 10px;
      color: var(--muted);
      font-size: 0.92rem;
    }

    .table-wrap {
      overflow: auto;
      max-height: 420px;
      border-radius: var(--radius-md);
      border: 1px solid rgba(24, 33, 47, 0.06);
      background: rgba(255, 255, 255, 0.64);
    }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.94rem;
    }

    th,
    td {
      padding: 10px 12px;
      border-bottom: 1px solid rgba(24, 33, 47, 0.08);
      text-align: left;
      vertical-align: top;
      white-space: nowrap;
    }

    th {
      position: sticky;
      top: 0;
      z-index: 1;
      background: rgba(249, 246, 239, 0.94);
      color: var(--muted);
      font-size: 12px;
      letter-spacing: 0.10em;
      text-transform: uppercase;
    }

    td code,
    .mono {
      font-family: var(--mono-font);
      font-size: 0.88rem;
    }

    .tone-positive {
      color: var(--positive);
      font-weight: 700;
    }

    .tone-negative {
      color: var(--negative);
      font-weight: 700;
    }

    .tone-neutral {
      color: inherit;
    }

    .empty-state {
      min-height: 148px;
      display: grid;
      place-items: center;
      text-align: center;
      padding: 18px;
      border-radius: var(--radius-lg);
      border: 1px dashed rgba(24, 33, 47, 0.14);
      background: rgba(255, 255, 255, 0.45);
      color: var(--muted);
      line-height: 1.6;
    }

    .activity-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }

    .subpanel {
      border: 1px solid rgba(24, 33, 47, 0.08);
      border-radius: var(--radius-lg);
      background: rgba(255, 255, 255, 0.56);
      padding: 14px;
    }

    .subpanel-header {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 12px;
      margin-bottom: 10px;
    }

    .subpanel-header h4 {
      margin: 0;
      font-size: 1.02rem;
    }

    .diagnostics {
      border: 1px solid var(--line);
      border-radius: var(--radius-xl);
      background: rgba(255, 255, 255, 0.55);
      box-shadow: var(--shadow);
      overflow: hidden;
    }

    .diagnostics summary {
      cursor: pointer;
      padding: 16px 18px;
      font-weight: 700;
      list-style: none;
    }

    .diagnostics summary::-webkit-details-marker {
      display: none;
    }

    .diagnostics-body {
      padding: 0 18px 18px;
      display: grid;
      gap: 14px;
    }

    .source-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
    }

    .source-card {
      padding: 14px;
      border-radius: var(--radius-lg);
      border: 1px solid rgba(24, 33, 47, 0.08);
      background: rgba(255, 255, 255, 0.66);
    }

    .source-card header {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: center;
      margin-bottom: 8px;
    }

    .source-title {
      font-weight: 700;
      font-size: 0.96rem;
    }

    .status-pill.ok {
      color: var(--positive);
      background: rgba(12, 143, 98, 0.10);
    }

    .status-pill.empty {
      color: #8a6116;
      background: rgba(185, 132, 31, 0.10);
    }

    .status-pill.unsupported,
    .status-pill.error {
      color: var(--negative);
      background: rgba(192, 79, 57, 0.10);
    }

    .source-card .meta {
      color: var(--muted);
      font-size: 0.9rem;
      line-height: 1.55;
    }

    .hidden-grid {
      display: grid;
      gap: 14px;
    }

    /* -- Agent overview panel ------------------------------------------- */
    .agent-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }
    .agent-card {
      background: var(--panel-strong);
      border: 1px solid var(--line);
      border-radius: var(--radius-lg);
      padding: 16px 18px;
      box-shadow: 0 4px 18px rgba(24, 33, 47, 0.04);
    }
    .agent-card--full { grid-column: 1 / -1; }
    .agent-card--live { background: linear-gradient(135deg, rgba(180,214,224,0.18), rgba(255,255,255,0.96)); }
    .agent-card--muted { background: rgba(255,255,255,0.7); }
    .agent-card-head {
      display: flex; justify-content: space-between; align-items: baseline;
      gap: 12px; margin-bottom: 10px;
    }
    .agent-card-head strong { font-size: 15px; }
    .agent-subhead { font-size: 12px; color: var(--muted); margin: 12px 0 4px; text-transform: uppercase; letter-spacing: 0.05em; }
    .agent-pill {
      display: inline-block; padding: 2px 8px; border-radius: 999px;
      font-size: 11px; font-weight: 600; background: var(--accent-soft); color: var(--accent);
      letter-spacing: 0.02em;
    }
    .agent-pill--tier1 { background: rgba(192, 79, 57, 0.14); color: var(--negative); }
    .agent-pill--tier2 { background: rgba(21, 53, 82, 0.10); color: var(--accent); }
    .agent-pill--exec  { background: rgba(192, 79, 57, 0.18); color: var(--negative); }
    .agent-pill--dry   { background: rgba(185, 132, 31, 0.18); color: var(--warning); }
    .agent-pill--ok    { background: rgba(12, 143, 98, 0.18); color: var(--positive); }
    .agent-pill--off   { background: rgba(95, 105, 121, 0.18); color: var(--muted); }
    .agent-pill--info  { background: rgba(21, 53, 82, 0.10); color: var(--accent); }
    .agent-pill--warn  { background: rgba(185, 132, 31, 0.18); color: var(--warning); }
    .agent-pill--err   { background: rgba(192, 79, 57, 0.18); color: var(--negative); }
    .agent-metric-row {
      display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 8px 14px; margin: 6px 0 10px;
    }
    .agent-metric-row > div { display: flex; flex-direction: column; }
    .agent-metric-row .agent-key {
      font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em;
    }
    .agent-metric-row strong { font-size: 16px; font-family: var(--mono-font); }
    .agent-list { margin: 0; padding: 0; list-style: none; display: flex; flex-direction: column; gap: 6px; }
    .agent-list li { font-size: 13px; line-height: 1.45; }
    .agent-tree, .agent-tree ul { margin: 0; padding: 0; list-style: none; }
    .agent-tree { display: flex; flex-direction: column; gap: 8px; }
    .agent-tree li { font-size: 13px; line-height: 1.45; }
    .agent-tree li > ul { margin: 4px 0 4px 18px; padding-left: 12px; border-left: 1px dashed var(--line); display: flex; flex-direction: column; gap: 4px; }
    .agent-muted { color: var(--muted); font-size: 12px; }
    .agent-error {
      margin-top: 8px; padding: 8px 10px; border-radius: var(--radius-sm);
      background: rgba(192, 79, 57, 0.12); color: var(--negative); font-size: 12px;
    }
    .agent-trigger {
      font-size: 12px; line-height: 1.5;
      padding: 4px 0; border-top: 1px dashed var(--line);
    }
    .agent-trigger:first-of-type { border-top: 0; }
    .agent-table {
      width: 100%; border-collapse: collapse; font-size: 12px;
    }
    .agent-table th {
      text-align: left; padding: 6px 8px; color: var(--muted);
      font-weight: 600; border-bottom: 1px solid var(--line);
      text-transform: uppercase; font-size: 10px; letter-spacing: 0.05em;
    }
    .agent-table td { padding: 6px 8px; border-bottom: 1px solid var(--line); vertical-align: top; }
    .agent-table tr:last-child td { border-bottom: 0; }
    .agent-table .mono { font-family: var(--mono-font); white-space: nowrap; }

    /* -- Agent tab: operator view ---------------------------------------- */
    .ag-stack { display: grid; gap: 20px; }
    /* Grid items default to min-width:auto and grow to their widest child —
       a table or a long gist pushed the tab 56px past a 390px screen. */
    .ag-stack > *, .ag-grid2 > *, .ag-strip > *, .ag-rules > * { min-width: 0; }
    .ag-table-wrap { overflow-x: auto; }
    .ag-stat .v, .ag-stat .s { overflow-wrap: anywhere; }
    .ag-grid2 { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px; }
    .ag-grid2 > .panel { margin: 0; }
    .ag-asof {
      margin-bottom: 12px; padding: 8px 12px; border-radius: var(--radius-sm);
      background: rgba(185, 132, 31, 0.10); color: var(--warning); font-size: 12px;
    }
    .ag-strip { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px; }
    .ag-stat {
      padding: 12px 14px; border-radius: var(--radius-sm);
      background: var(--panel-strong); border: 1px solid var(--line); min-width: 0;
    }
    .ag-stat .k { font-size: 11px; color: var(--muted); letter-spacing: 0.04em; }
    .ag-stat .v {
      font-size: 17px; font-weight: 700; margin-top: 4px;
      display: flex; align-items: center; gap: 7px; flex-wrap: wrap;
    }
    .ag-stat .s { font-size: 12px; color: var(--muted); margin-top: 3px; line-height: 1.45; }
    .ag-dot { width: 9px; height: 9px; border-radius: 50%; flex: none; background: var(--muted); }
    .ag-dot--ok { background: var(--positive); }
    .ag-dot--warn { background: var(--warning); }
    .ag-dot--err { background: var(--negative); }
    .ag-dot--off { background: rgba(95, 105, 121, 0.45); }

    .ag-lead { font-size: 15px; line-height: 1.65; margin: 0 0 14px; color: var(--ink); }
    .ag-lead strong { font-weight: 700; }
    .ag-rules { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
    .ag-rule {
      padding: 12px 14px; border-radius: var(--radius-sm);
      background: var(--panel-strong); border: 1px solid var(--line);
    }
    .ag-rule .t {
      font-size: 11px; color: var(--muted); letter-spacing: 0.05em;
      margin-bottom: 6px; font-weight: 600;
    }
    .ag-rule ul { margin: 0; padding-left: 16px; font-size: 13px; line-height: 1.55; }
    .ag-rule li + li { margin-top: 3px; }
    .ag-rule .num { font-family: var(--mono-font); font-weight: 700; }

    .ag-pos + .ag-pos { margin-top: 18px; padding-top: 16px; border-top: 1px solid var(--line); }
    .ag-pos-head { display: flex; justify-content: space-between; align-items: baseline; gap: 10px; flex-wrap: wrap; }
    .ag-pos-name { font-size: 16px; font-weight: 700; }
    .ag-pos-rate { font-size: 20px; font-weight: 700; font-family: var(--mono-font); }
    .ag-pos-sub { font-size: 12px; color: var(--muted); margin-top: 2px; }
    .ag-bar {
      position: relative; height: 10px; border-radius: 5px; margin: 26px 6px 8px;
      background: linear-gradient(90deg,
        rgba(192, 79, 57, 0.35) 0%, rgba(95, 105, 121, 0.14) 30%,
        rgba(95, 105, 121, 0.14) 70%, rgba(12, 143, 98, 0.35) 100%);
    }
    .ag-bar-entry {
      position: absolute; top: -5px; width: 2px; height: 20px;
      background: rgba(33, 38, 45, 0.45); transform: translateX(-1px);
    }
    .ag-bar-now {
      position: absolute; top: -6px; width: 22px; height: 22px; border-radius: 50%;
      transform: translateX(-50%); border: 3px solid #fff;
      box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
    }
    .ag-bar-now--up { background: var(--positive); }
    .ag-bar-now--down { background: var(--negative); }
    .ag-bar-tag {
      position: absolute; top: -24px; transform: translateX(-50%);
      font-size: 11px; font-weight: 700; font-family: var(--mono-font); white-space: nowrap;
    }
    .ag-bar-labels {
      display: grid; grid-template-columns: 1fr 1fr 1fr; font-size: 12px; margin: 0 0 4px;
    }
    .ag-bar-labels > div:nth-child(2) { text-align: center; }
    .ag-bar-labels > div:nth-child(3) { text-align: right; }
    .ag-bar-labels .p { font-family: var(--mono-font); font-weight: 600; color: var(--ink); }
    .ag-bar-labels .l { color: var(--muted); font-size: 11px; }
    .ag-empty {
      padding: 22px; border-radius: var(--radius-sm); border: 1px dashed var(--line);
      color: var(--muted); font-size: 13px; text-align: center; line-height: 1.6;
    }

    .ag-funnel { display: flex; flex-wrap: wrap; align-items: stretch; gap: 6px; margin-bottom: 12px; }
    .ag-step {
      padding: 7px 10px; border-radius: var(--radius-sm); background: var(--panel-strong);
      border: 1px solid var(--line); font-size: 12px; color: var(--muted); line-height: 1.3;
    }
    .ag-step strong { display: block; font-size: 17px; color: var(--ink); font-family: var(--mono-font); }
    .ag-step--block { border-color: rgba(185, 132, 31, 0.55); background: rgba(185, 132, 31, 0.10); }
    .ag-step--block strong { color: var(--warning); }
    .ag-arrow { align-self: center; color: var(--muted); font-size: 12px; }
    .ag-callout {
      margin-bottom: 12px; padding: 9px 12px; border-radius: var(--radius-sm); font-size: 12.5px;
      line-height: 1.5; background: var(--accent-soft); color: var(--ink);
    }
    .ag-score { display: inline-flex; align-items: center; gap: 6px; font-family: var(--mono-font); font-weight: 700; }
    .ag-score i { display: inline-block; height: 6px; border-radius: 3px; background: var(--accent); opacity: 0.55; }
    .ag-score--pass i { background: var(--positive); opacity: 0.8; }

    .ag-tally { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; align-items: center; }
    .ag-tally .sep { width: 1px; height: 16px; background: var(--line); margin: 0 4px; }
    .ag-dec-wrap { border-top: 1px solid var(--line); }
    .ag-dec-wrap:first-child { border-top: 0; }
    .ag-dec {
      display: grid; grid-template-columns: 54px 104px minmax(0, 150px) 96px minmax(0, 1fr) 14px;
      gap: 10px; align-items: center; padding: 11px 2px; cursor: pointer; list-style: none;
      font-size: 13px;
    }
    .ag-dec::-webkit-details-marker { display: none; }
    .ag-dec:hover { background: var(--accent-soft); }
    .ag-dec .time { font-family: var(--mono-font); font-size: 12px; color: var(--muted); }
    .ag-dec .what { font-weight: 600; }
    .ag-dec .who { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .ag-dec .gist { color: var(--muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .ag-dec .chev { color: var(--muted); transition: transform 0.15s; }
    .ag-dec-wrap[open] .ag-dec .chev { transform: rotate(90deg); }
    .ag-dec-body { padding: 4px 4px 16px 64px; }
    .ag-md { font-size: 13px; line-height: 1.6; color: var(--ink); }
    .ag-md p { margin: 0 0 6px; }
    .ag-md ul { margin: 0 0 6px; padding-left: 18px; }
    .ag-md li + li { margin-top: 3px; }
    .ag-md code { font-family: var(--mono-font); font-size: 12px; background: var(--accent-soft); padding: 0 4px; border-radius: 4px; }

    @media (max-width: 1120px) {
      .ag-strip { grid-template-columns: repeat(3, minmax(0, 1fr)); }
      .ag-rules { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .ag-grid2 { grid-template-columns: 1fr; }
    }
    @media (max-width: 680px) {
      .ag-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .ag-rules { grid-template-columns: 1fr; }
      .ag-dec { grid-template-columns: 46px minmax(0, 1fr) auto 14px; }
      .ag-dec .who, .ag-dec .gist { display: none; }
      .ag-dec-body { padding-left: 4px; }
    }

    /* -- Agent decision timeline ----------------------------------------- */
    .agent-toolbar { display: flex; gap: 8px; align-items: center; }
    .agent-btn {
      padding: 6px 12px; border-radius: var(--radius-sm); border: 1px solid var(--line);
      background: var(--panel-strong); color: var(--ink); font-size: 12px;
      font-weight: 600; cursor: pointer;
    }
    .agent-btn:hover { border-color: var(--accent); color: var(--accent); }
    .agent-tl { display: flex; flex-direction: column; }
    .agent-tl-row {
      display: grid; grid-template-columns: 68px minmax(0, 1fr);
      gap: 12px; padding: 14px 0; border-top: 1px solid var(--line);
    }
    .agent-tl-row:first-child { border-top: 0; }
    .agent-tl-time { font-size: 12px; color: var(--muted); padding-top: 2px; }
    .agent-tl-body { min-width: 0; }
    .agent-tl-head {
      display: flex; flex-wrap: wrap; gap: 8px; align-items: center;
      font-size: 14px; margin-bottom: 6px;
    }
    .agent-tl-why { font-size: 13px; color: var(--ink); margin-bottom: 6px; }
    .agent-chips { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
    .agent-chip {
      font-size: 11px; padding: 2px 8px; border-radius: var(--radius-sm);
      background: var(--panel); border: 1px solid var(--line); color: var(--muted);
    }
    .agent-chip strong { font-family: var(--mono-font); color: var(--ink); }
    .agent-tl-resp {
      font-size: 13px; line-height: 1.55; color: var(--ink);
      display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical;
      overflow: hidden;
    }
    .agent-tl-deleg {
      margin: 8px 0 0 4px; padding-left: 12px; border-left: 1px dashed var(--line);
      display: flex; flex-direction: column; gap: 4px; font-size: 12px; line-height: 1.5;
    }
    .agent-tl-outcome { margin-top: 8px; font-size: 12px; }
    .agent-tl-more { margin-top: 8px; }
    .agent-tl-more > summary {
      cursor: pointer; font-size: 12px; color: var(--accent); font-weight: 600;
    }
    .agent-pre {
      margin: 6px 0 10px; padding: 10px 12px; border-radius: var(--radius-sm);
      background: var(--panel); border: 1px solid var(--line);
      font-family: var(--mono-font); font-size: 11.5px; line-height: 1.5;
      white-space: pre-wrap; word-break: break-word; max-height: 420px; overflow: auto;
    }
    .agent-notice-soft {
      margin-bottom: 10px; padding: 8px 10px; border-radius: var(--radius-sm);
      background: rgba(185, 132, 31, 0.12); color: var(--warning); font-size: 12px;
    }

    @media (max-width: 1120px) {
      .hero,
      .overview-grid,
      .content-grid,
      .activity-grid {
        grid-template-columns: 1fr;
      }

      .span-2,
      .span-3 {
        grid-column: span 1;
      }

      .metric-grid,
      .mini-metric-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }

      .toolbar form {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }

      .agent-grid {
        grid-template-columns: 1fr;
      }

      .agent-metric-row {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
    }

    @media (max-width: 680px) {
      .shell {
        width: min(100vw - 16px, 100%);
        padding-top: 16px;
      }

      .hero,
      .toolbar,
      .panel,
      .diagnostics {
        border-radius: 22px;
      }

      .metric-grid,
      .mini-metric-grid,
      .toolbar form {
        grid-template-columns: 1fr;
      }

      th,
      td {
        padding: 9px 10px;
      }

      .agent-metric-row {
        grid-template-columns: 1fr;
      }

      /* Drop the fixed time gutter — the timestamp moves above the entry. */
      .agent-tl-row {
        grid-template-columns: 1fr;
        gap: 4px;
      }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div>
        <p class="eyebrow">Kiwoom OpenAPI Dashboard</p>
        <h1>Trading Dashboard</h1>
        <p class="hero-copy">계좌 상태, 보유 종목, 활성 주문, 최근 거래 흐름만 빠르게 읽을 수 있도록 화면을 줄였습니다. 빈 섹션과 진단 정보는 아래 접힌 패널에서 확인할 수 있습니다.</p>
        <div class="identity-strip">
          <span class="pill"><strong id="account-name">-</strong></span>
          <span class="meta-pill"><strong id="branch-name">-</strong></span>
          <span class="pill env-mock" id="env-pill"><strong id="env-label">-</strong></span>
        </div>
      </div>
      <div class="hero-side">
        <div class="side-box">
          <span class="label">Last Refresh</span>
          <div class="value" id="generated-at">-</div>
        </div>
        <div class="side-box">
          <span class="label">Base URL</span>
          <div class="value mono" id="base-url">-</div>
        </div>
        <div class="side-box">
          <span class="label">View Rule</span>
          <div class="value">핵심 섹션만 기본 노출, 빈 조회와 상세 진단은 접어두기</div>
        </div>
      </div>
    </section>

    <nav class="tab-nav" id="tab-nav">
      <a href="#main" class="tab-link active" data-view="main">📊 매매 / 수익</a>
      <a href="#agents" class="tab-link" data-view="agents">🧭 전략 · 운영</a>
    </nav>

    <section class="view view-main active" id="view-main">
    <section class="toolbar">
      <form id="filter-form">
        <div class="field">
          <label for="start-date">Start Date</label>
          <input id="start-date" name="start_date" type="text" inputmode="numeric" pattern="\d{8}">
        </div>
        <div class="field">
          <label for="end-date">End Date</label>
          <input id="end-date" name="end_date" type="text" inputmode="numeric" pattern="\d{8}">
        </div>
        <div class="toggle-wrap">
          <input id="show-empty" type="checkbox">
          <label class="toggle" for="show-empty">빈 섹션 표시</label>
        </div>
        <button type="submit">새로 조회</button>
      </form>
      <div class="toolbar-note">YYYYMMDD 형식으로 기간을 바꾸면 기간 손익, 실현손익, 체결 이력을 다시 불러옵니다.</div>
    </section>

    <div id="page-error"></div>

    <section class="overview-grid">
      <section class="panel">
        <div class="section-head">
          <div>
            <p class="section-kicker">Overview</p>
            <h2>핵심 요약</h2>
          </div>
          <p class="section-subtitle" id="summary-note">-</p>
        </div>
        <div id="summary-grid" class="metric-grid"></div>
      </section>

      <aside class="panel">
        <div class="section-head">
          <div>
            <p class="section-kicker">Focus</p>
            <h3>지금 볼 것</h3>
          </div>
        </div>
        <div id="focus-grid" class="focus-list"></div>
        <div id="attention-box"></div>
      </aside>
    </section>

    <section class="panel">
      <div class="section-head">
        <div>
          <p class="section-kicker">Assets</p>
          <h2>총자산 추이</h2>
        </div>
        <p class="section-subtitle" id="asset-chart-note">-</p>
      </div>
      <div id="asset-chart"></div>
    </section>

    <section class="content-grid">
      <section class="panel span-2">
        <div class="section-head">
          <div>
            <p class="section-kicker">Positions</p>
            <h3>보유 종목</h3>
          </div>
          <p class="section-subtitle">현재 포지션만 유지</p>
        </div>
        <div id="holdings-root"></div>
      </section>

      <section class="panel">
        <div class="section-head">
          <div>
            <p class="section-kicker">Orders</p>
            <h3>활성 주문</h3>
          </div>
          <p class="section-subtitle">미체결 또는 진행 중 주문</p>
        </div>
        <div id="orders-root"></div>
      </section>

      <section class="panel span-3">
        <div class="section-head">
          <div>
            <p class="section-kicker">Performance</p>
            <h3>기간 성과</h3>
          </div>
          <p class="section-subtitle" id="performance-note">-</p>
        </div>
        <div id="performance-root"></div>
      </section>
    </section>

    <section class="panel">
      <div class="section-head">
        <div>
          <p class="section-kicker">Recent Activity</p>
          <h3>최근 거래 이력</h3>
        </div>
        <p class="section-subtitle">체결과 실현손익만 분리해서 표시</p>
      </div>
      <div id="activity-root"></div>
    </section>

    <details class="diagnostics" id="diagnostics-fold">
      <summary id="diagnostics-summary">숨겨진 섹션과 데이터 상태</summary>
      <div class="diagnostics-body">
        <div id="source-root"></div>
        <div id="hidden-root" class="hidden-grid"></div>
      </div>
    </details>
    </section><!-- /view-main -->

    <section class="view view-agents" id="view-agents">
     <div class="ag-stack">
      <!-- Read top to bottom: is it running, what is it trying to do, where
           is the money, what is waiting to get in, what did the agents say.
           Every value is the watcher's own report or the broker's; nothing
           here is a code default. -->
      <section class="panel" id="agent-panel">
        <div class="section-head">
          <div>
            <p class="section-kicker">Now</p>
            <h3>지금 시스템 상태</h3>
          </div>
          <p class="section-subtitle" id="agent-note">-</p>
        </div>
        <div id="agent-strip-root"></div>
      </section>

      <section class="panel">
        <div class="section-head">
          <div>
            <p class="section-kicker">Strategy</p>
            <h3>지금 돌고 있는 전략</h3>
          </div>
          <p class="section-subtitle">watcher가 보고한 실효 설정으로 구성</p>
        </div>
        <div id="agent-strategy-root"></div>
      </section>

      <section class="ag-grid2">
        <section class="panel">
          <div class="section-head">
            <div>
              <p class="section-kicker">Position</p>
              <h3>보유 종목 — 손절과 익절 사이</h3>
            </div>
            <p class="section-subtitle" id="agent-position-note">-</p>
          </div>
          <div id="agent-position-root"></div>
        </section>
        <section class="panel">
          <div class="section-head">
            <div>
              <p class="section-kicker">Pipeline</p>
              <h3>후보 파이프라인</h3>
            </div>
            <p class="section-subtitle" id="agent-pipeline-note">-</p>
          </div>
          <div id="agent-pipeline-root"></div>
        </section>
      </section>

      <section class="panel" id="agent-timeline-panel">
        <div class="section-head">
          <div>
            <p class="section-kicker">Decisions</p>
            <h3>에이전트 판단</h3>
          </div>
          <div class="agent-toolbar">
            <input type="date" id="agent-date" class="panel-search" />
            <button type="button" id="agent-reload" class="agent-btn">새로고침</button>
          </div>
        </div>
        <div id="agent-timeline-root"></div>
      </section>

      <details class="diagnostics" id="agent-ops-fold">
        <summary>운영 상세 · 실패 · cooldown · 브리핑 자동화 · 전체 파라미터</summary>
        <div class="diagnostics-body"><div id="agent-status-root"></div></div>
      </details>
     </div>
    </section><!-- /view-agents -->
  </main>

  <script>
    const initialConfig = __INITIAL_CONFIG__;
    let currentPayload = null;

    const pageErrorRoot = document.getElementById("page-error");
    const startInput = document.getElementById("start-date");
    const endInput = document.getElementById("end-date");
    const showEmptyInput = document.getElementById("show-empty");
    const summaryRoot = document.getElementById("summary-grid");
    const focusRoot = document.getElementById("focus-grid");
    const attentionRoot = document.getElementById("attention-box");
    const holdingsRoot = document.getElementById("holdings-root");
    const ordersRoot = document.getElementById("orders-root");
    const performanceRoot = document.getElementById("performance-root");
    const activityRoot = document.getElementById("activity-root");
    const sourceRoot = document.getElementById("source-root");
    const hiddenRoot = document.getElementById("hidden-root");
    const diagnosticsFold = document.getElementById("diagnostics-fold");
    const diagnosticsSummary = document.getElementById("diagnostics-summary");

    startInput.value = initialConfig.start_date;
    endInput.value = initialConfig.end_date;

    function escapeHtml(value) {
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
    }

    function hasValue(value) {
      return value !== null && value !== undefined && value !== "";
    }

    function toNumber(value) {
      if (!hasValue(value)) {
        return null;
      }
      const text = String(value).replace(/,/g, "").trim();
      if (!text) {
        return null;
      }
      const parsed = Number(text);
      return Number.isFinite(parsed) ? parsed : null;
    }

    function normalizeCode(value) {
      const text = String(value ?? "");
      return /^A\d{6}$/.test(text) ? text.slice(1) : text;
    }

    function toneForValue(value) {
      const parsed = toNumber(value);
      if (parsed === null) {
        return "tone-neutral";
      }
      if (parsed > 0) {
        return "tone-positive";
      }
      if (parsed < 0) {
        return "tone-negative";
      }
      return "tone-neutral";
    }

    function formatMetric(value, kind) {
      if (kind === "text") {
        return hasValue(value) ? String(value) : "N/A";
      }
      const parsed = toNumber(value);
      if (parsed === null) {
        return hasValue(value) ? String(value) : "N/A";
      }
      if (kind === "currency") {
        return new Intl.NumberFormat("ko-KR").format(parsed) + "원";
      }
      if (kind === "ratio") {
        return new Intl.NumberFormat("ko-KR", { maximumFractionDigits: 2 }).format(parsed) + "%";
      }
      return new Intl.NumberFormat("ko-KR").format(parsed);
    }

    function formatCell(key, value) {
      if (!hasValue(value)) {
        return "—";
      }

      if (key.includes("date") && String(value).length === 8 && /^\d+$/.test(String(value))) {
        return `${String(value).slice(0, 4)}-${String(value).slice(4, 6)}-${String(value).slice(6, 8)}`;
      }

      if (key.includes("time") && /^\d{4,6}$/.test(String(value))) {
        const padded = String(value).padStart(6, "0");
        return `${padded.slice(0, 2)}:${padded.slice(2, 4)}:${padded.slice(4, 6)}`;
      }

      if (key.includes("rate")) {
        return `<span class="${toneForValue(value)}">${escapeHtml(formatMetric(value, "ratio"))}</span>`;
      }

      if (["quantity", "order_qty", "filled_qty"].includes(key)) {
        return escapeHtml(formatMetric(value, "number"));
      }

      if (key.includes("amount") || key.includes("price") || key.includes("profit") || key === "deposit" || key === "estimated_assets" || key === "evaluation_amount") {
        return `<span class="${toneForValue(value)}">${escapeHtml(formatMetric(value, "currency"))}</span>`;
      }

      if (key.endsWith("_no")) {
        return `<code>${escapeHtml(value)}</code>`;
      }

      if (key.endsWith("_code")) {
        return `<code>${escapeHtml(normalizeCode(value))}</code>`;
      }

      return escapeHtml(value);
    }

    function humanizeKey(key) {
      return key.replaceAll("_", " ");
    }

    function chooseColumns(table) {
      const rows = table.rows || [];
      const visible = (table.columns || []).filter((column) =>
        rows.some((row) => hasValue(row[column.key]))
      );

      if (visible.length > 0) {
        return {
          columns: visible,
          rows,
        };
      }

      const rawRows = table.raw_rows || [];
      const firstRow = rawRows[0] || {};
      const rawColumns = Object.keys(firstRow)
        .filter((key) => key !== "return_code" && key !== "return_msg")
        .slice(0, 8)
        .map((key) => ({ key, label: humanizeKey(key) }));

      return {
        columns: rawColumns,
        rows: rawRows,
      };
    }

    function buildEmpty(message) {
      return `<div class="empty-state">${escapeHtml(message)}</div>`;
    }

    function buildTable(table, options = {}) {
      const rowCount = table.row_count || 0;
      if (rowCount === 0) {
        return buildEmpty(table.empty_message);
      }

      const chosen = chooseColumns(table);
      const columns = chosen.columns;
      const rows = chosen.rows || [];

      if (columns.length === 0) {
        return buildEmpty(table.empty_message);
      }

      const limit = options.limit || rows.length;
      const visibleRows = rows.slice(0, limit);
      const metaNote = rowCount > visibleRows.length
        ? `총 ${rowCount}건 중 ${visibleRows.length}건 표시`
        : `총 ${rowCount}건`;

      return `
        <div class="table-meta">
          <span>${escapeHtml(metaNote)}</span>
          ${options.note ? `<span>${escapeHtml(options.note)}</span>` : ""}
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>${columns.map((column) => `<th>${escapeHtml(column.label)}</th>`).join("")}</tr>
            </thead>
            <tbody>
              ${visibleRows.map((row) => `
                <tr>
                  ${columns.map((column) => `<td>${formatCell(column.key, row[column.key])}</td>`).join("")}
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      `;
    }

    function buildSubpanel(title, subtitle, table, options = {}) {
      return `
        <section class="subpanel">
          <div class="subpanel-header">
            <h4>${escapeHtml(title)}</h4>
            <span class="section-subtitle">${escapeHtml(subtitle)}</span>
          </div>
          ${buildTable(table, options)}
        </section>
      `;
    }

    function renderSummary(cards) {
      summaryRoot.innerHTML = cards.map((card) => {
        const cls = ["metric-card", escapeHtml(card.tone || "neutral")];
        if (card.highlight) cls.push("highlight");
        const detail = card.detail
          ? `<div class="detail">${escapeHtml(card.detail)}</div>`
          : "";
        return `
          <article class="${cls.join(" ")}">
            <div class="label">${escapeHtml(card.label)}</div>
            <div class="value ${escapeHtml(toneForValue(card.value))}">${escapeHtml(formatMetric(card.value, card.kind))}</div>
            ${detail}
          </article>
        `;
      }).join("");
    }

    function renderAssetChart(series) {
      const root = document.getElementById("asset-chart");
      const note = document.getElementById("asset-chart-note");
      if (!root) return;
      const pts = (series && Array.isArray(series.points)) ? series.points : [];
      if (pts.length < 2) {
        root.innerHTML = '<div class="empty-state">자산 추이 데이터가 부족합니다.</div>';
        if (note) note.textContent = (series && series.note) || "-";
        return;
      }
      const W = 720, H = 220, padL = 64, padR = 16, padT = 16, padB = 28;
      const vals = pts.map((p) => p.value);
      let lo = Math.min(...vals), hi = Math.max(...vals);
      if (lo === hi) { lo -= 1; hi += 1; }
      const span = hi - lo;
      const x = (i) => padL + (i / (pts.length - 1)) * (W - padL - padR);
      const y = (v) => padT + (1 - (v - lo) / span) * (H - padT - padB);
      const line = pts.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p.value).toFixed(1)}`).join(" ");
      const area = `${line} L${x(pts.length - 1).toFixed(1)},${(H - padB).toFixed(1)} L${x(0).toFixed(1)},${(H - padB).toFixed(1)} Z`;
      // y gridlines (lo / mid / hi)
      const ticks = [lo, lo + span / 2, hi];
      const grid = ticks.map((v) => {
        const yy = y(v).toFixed(1);
        return `<line x1="${padL}" y1="${yy}" x2="${W - padR}" y2="${yy}" stroke="#2a2e3a" stroke-width="1"/>`
          + `<text x="${padL - 8}" y="${(y(v) + 4).toFixed(1)}" text-anchor="end" font-size="11" fill="#8a90a0">${Math.round(v).toLocaleString()}</text>`;
      }).join("");
      const first = pts[0], last = pts[pts.length - 1];
      const xlabels = `<text x="${x(0)}" y="${H - 8}" font-size="11" fill="#8a90a0">${first.date}</text>`
        + `<text x="${W - padR}" y="${H - 8}" text-anchor="end" font-size="11" fill="#8a90a0">${last.date}</text>`;
      const up = (series.change || 0) >= 0;
      const stroke = up ? "#3fb950" : "#f85149";
      const fill = up ? "rgba(63,185,80,0.12)" : "rgba(248,81,73,0.12)";
      root.innerHTML =
        `<svg viewBox="0 0 ${W} ${H}" width="100%" preserveAspectRatio="xMidYMid meet" role="img" aria-label="총자산 추이">`
        + grid
        + `<path d="${area}" fill="${fill}" stroke="none"/>`
        + `<path d="${line}" fill="none" stroke="${stroke}" stroke-width="2"/>`
        + xlabels + `</svg>`;
      if (note) {
        const chg = series.change;
        const chgTxt = (chg == null) ? "" :
          ` · 기간 변동 ${chg >= 0 ? "+" : ""}${Math.round(chg).toLocaleString()}원`;
        note.textContent = (series.note || "") + chgTxt;
      }
    }

    function renderFocus(payload) {
      const overview = payload.overview || {};
      const items = [
        ["보유 종목 수", overview.holdings_count || 0],
        ["활성 주문 수", overview.active_orders_count || 0],
        ["최근 체결 건수", overview.executions_count || 0],
        ["숨은 진단 수", (overview.issues_count || 0) + (overview.empty_sources_count || 0)],
      ];

      focusRoot.innerHTML = items.map(([label, value]) => `
        <article class="focus-item">
          <span class="label">${escapeHtml(label)}</span>
          <strong>${escapeHtml(String(value))}</strong>
        </article>
      `).join("");
    }

    function renderAttention(payload) {
      const issues = (payload.sources || []).filter((source) => source.status === "error" || source.status === "unsupported");
      const empties = (payload.sources || []).filter((source) => source.status === "empty");

      if (issues.length > 0) {
        attentionRoot.innerHTML = `
          <article class="notice error">
            <strong>확인 필요한 항목</strong>
            <ul>${issues.map((source) => `<li>${escapeHtml(source.title)}: ${escapeHtml(source.message || source.status_label)}</li>`).join("")}</ul>
          </article>
        `;
        return;
      }

      if (empties.length > 0) {
        attentionRoot.innerHTML = `
          <article class="notice warn">
            <strong>현재 비어 있는 조회</strong>
            <div>${escapeHtml(empties.map((source) => source.title).join(", "))}</div>
          </article>
        `;
        return;
      }

      attentionRoot.innerHTML = `
        <article class="notice ok">
          <strong>핵심 조회 정상</strong>
          <div>계좌 요약과 주요 섹션이 모두 정상 응답입니다.</div>
        </article>
      `;
    }

    function renderHoldings(payload) {
      const table = payload.tables.holdings;
      holdingsRoot.innerHTML = buildTable(table, { limit: 10, note: "손익 기준 컬럼 우선 표시" });
    }

    function renderOrders(payload) {
      const unexecuted = payload.tables.unexecuted_orders;
      const orderStatus = payload.tables.order_status;
      const orderSource = (payload.sources || []).find((source) => source.title === "주문 체결 현황");

      if ((unexecuted.row_count || 0) > 0) {
        ordersRoot.innerHTML = buildTable(unexecuted, { limit: 8, note: "미체결 주문 기준" });
        return;
      }

      if ((orderStatus.row_count || 0) > 0) {
        ordersRoot.innerHTML = buildTable(orderStatus, { limit: 8, note: "주문 진행 상태 기준" });
        return;
      }

      const sourceMessage = orderSource && (orderSource.status === "error" || orderSource.status === "unsupported")
        ? orderSource.message
        : "현재 활성 주문이 없습니다.";
      ordersRoot.innerHTML = buildEmpty(sourceMessage || "현재 활성 주문이 없습니다.");
    }

    function renderPerformance(payload) {
      const performance = (payload.performance || []).filter((item) => hasValue(item.value));
      const filter = payload.filters || {};
      document.getElementById("performance-note").textContent = `${filter.start_date} ~ ${filter.end_date}`;

      if (performance.length === 0) {
        performanceRoot.innerHTML = buildEmpty("기간 성과 데이터가 없습니다.");
        return;
      }

      performanceRoot.innerHTML = `
        <div class="mini-metric-grid">
          ${performance.map((item) => {
            const cls = ["mini-metric"];
            if (item.highlight) cls.push("highlight");
            const tone = item.tone || toneForValue(item.value);
            const detail = hasValue(item.detail)
              ? `<div class="detail">${escapeHtml(item.detail)}</div>`
              : "";
            return `
              <article class="${cls.join(" ")}">
                <div class="label">${escapeHtml(item.label)}</div>
                <div class="value ${escapeHtml(tone)}">${escapeHtml(formatMetric(item.value, item.kind))}</div>
                ${detail}
              </article>`;
          }).join("")}
        </div>
      `;
    }

    // Pagination state per panel (key → { page, search })
    const paginationState = {};

    function renderActivity(payload, showEmpty) {
      const blocks = [];
      const executions = payload.tables.executions;
      const realized = payload.tables.realized_profit;
      const tradingJournal = payload.tables.trading_journal;

      if ((executions.row_count || 0) > 0 || showEmpty) {
        blocks.push(buildPaginatedPanel("executions", "체결 이력", "최근 체결 — 검색 / 페이징 가능", executions, {
          searchKeys: ["stock_name", "stock_code"],
          pageSize: 10,
        }));
      }

      if ((tradingJournal.row_count || 0) > 0 || showEmpty) {
        blocks.push(buildPaginatedPanel("trading_journal", "당일매매일지", "거래별 손익", tradingJournal, {
          searchKeys: ["stock_name", "stock_code"],
          pageSize: 10,
        }));
      }

      if ((realized.row_count || 0) > 0 || showEmpty) {
        blocks.push(buildPaginatedPanel("realized", "실현손익", "기간 기준", realized, {
          searchKeys: ["stock_name", "stock_code"],
          pageSize: 10,
        }));
      }

      if (blocks.length === 0) {
        activityRoot.innerHTML = buildEmpty("선택 기간에 표시할 체결 이력이나 실현손익이 없습니다.");
        return;
      }

      activityRoot.innerHTML = `<div class="activity-grid">${blocks.join("")}</div>`;

      // Wire up search + pagination event handlers AFTER innerHTML write.
      attachPanelHandlers("executions", executions, { pageSize: 10, searchKeys: ["stock_name", "stock_code"] });
      attachPanelHandlers("trading_journal", tradingJournal, { pageSize: 10, searchKeys: ["stock_name", "stock_code"] });
      attachPanelHandlers("realized", realized, { pageSize: 10, searchKeys: ["stock_name", "stock_code"] });
    }

    function buildPaginatedPanel(panelKey, title, subtitle, table, options) {
      const state = paginationState[panelKey] || (paginationState[panelKey] = { page: 0, search: "" });
      const totalRows = (table.rows || []).length;
      return `
        <section class="subpanel" data-panel="${escapeHtml(panelKey)}">
          <div class="subpanel-header">
            <h4>${escapeHtml(title)}</h4>
            <span class="section-subtitle">${escapeHtml(subtitle)} · 총 ${totalRows}건</span>
          </div>
          <div class="panel-toolbar">
            <input
              type="search"
              class="panel-search"
              data-panel="${escapeHtml(panelKey)}"
              placeholder="종목명 또는 코드 검색"
              value="${escapeHtml(state.search)}"
            />
          </div>
          <div class="panel-body" data-panel-body="${escapeHtml(panelKey)}">
            ${renderPanelTableBody(table, panelKey, options)}
          </div>
        </section>
      `;
    }

    function renderPanelTableBody(table, panelKey, options) {
      const state = paginationState[panelKey] || { page: 0, search: "" };
      const chosen = chooseColumns(table);
      const columns = chosen.columns;
      const allRows = chosen.rows || [];

      if (columns.length === 0 || allRows.length === 0) {
        return buildEmpty(table.empty_message);
      }

      const search = (state.search || "").trim().toLowerCase();
      const searchKeys = options.searchKeys || [];
      const filtered = search
        ? allRows.filter((row) => searchKeys.some((k) => String(row[k] || "").toLowerCase().includes(search)))
        : allRows;

      const pageSize = options.pageSize || 10;
      const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
      const page = Math.min(state.page, totalPages - 1);
      state.page = page;
      const start = page * pageSize;
      const visibleRows = filtered.slice(start, start + pageSize);

      const meta = filtered.length === allRows.length
        ? `총 ${allRows.length}건`
        : `필터 ${filtered.length}건 / 전체 ${allRows.length}건`;
      const pageNote = `${page + 1} / ${totalPages} 페이지`;

      const pagination = totalPages > 1
        ? `
          <nav class="pagination" data-panel-pager="${escapeHtml(panelKey)}">
            <button type="button" data-action="first" ${page === 0 ? "disabled" : ""}>«</button>
            <button type="button" data-action="prev"  ${page === 0 ? "disabled" : ""}>‹ 이전</button>
            ${buildPageNumbers(panelKey, page, totalPages)}
            <button type="button" data-action="next"  ${page >= totalPages - 1 ? "disabled" : ""}>다음 ›</button>
            <button type="button" data-action="last"  ${page >= totalPages - 1 ? "disabled" : ""}>»</button>
          </nav>`
        : "";

      return `
        <div class="table-meta">
          <span>${escapeHtml(meta)}</span>
          <span>${escapeHtml(pageNote)}</span>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>${columns.map((c) => `<th>${escapeHtml(c.label)}</th>`).join("")}</tr>
            </thead>
            <tbody>
              ${visibleRows.length === 0
                ? `<tr><td colspan="${columns.length}" class="empty-cell">검색 결과가 없습니다.</td></tr>`
                : visibleRows.map((row) => `
                    <tr>${columns.map((c) => `<td>${formatCell(c.key, row[c.key])}</td>`).join("")}</tr>
                  `).join("")
              }
            </tbody>
          </table>
        </div>
        ${pagination}
      `;
    }

    function buildPageNumbers(panelKey, current, total) {
      const max = 7;
      let start = Math.max(0, current - 3);
      let end = Math.min(total, start + max);
      start = Math.max(0, end - max);
      const buttons = [];
      for (let i = start; i < end; i += 1) {
        const cls = i === current ? "page active" : "page";
        buttons.push(`<button type="button" class="${cls}" data-action="goto" data-page="${i}">${i + 1}</button>`);
      }
      return buttons.join("");
    }

    function attachPanelHandlers(panelKey, table, options) {
      const search = document.querySelector(`.panel-search[data-panel="${panelKey}"]`);
      const body = document.querySelector(`.panel-body[data-panel-body="${panelKey}"]`);
      if (!body) return;

      const rerender = () => {
        body.innerHTML = renderPanelTableBody(table, panelKey, options);
        attachPagerOnly(panelKey, table, options);
      };

      if (search) {
        search.addEventListener("input", (e) => {
          const state = paginationState[panelKey] || (paginationState[panelKey] = { page: 0, search: "" });
          state.search = e.target.value;
          state.page = 0;
          rerender();
        });
      }
      attachPagerOnly(panelKey, table, options);
    }

    function attachPagerOnly(panelKey, table, options) {
      const pager = document.querySelector(`[data-panel-pager="${panelKey}"]`);
      if (!pager) return;
      const body = document.querySelector(`.panel-body[data-panel-body="${panelKey}"]`);
      pager.addEventListener("click", (e) => {
        const btn = e.target.closest("button");
        if (!btn || btn.disabled) return;
        const state = paginationState[panelKey] || (paginationState[panelKey] = { page: 0, search: "" });
        const action = btn.getAttribute("data-action");
        const chosen = chooseColumns(table);
        const allRows = chosen.rows || [];
        const search = (state.search || "").trim().toLowerCase();
        const searchKeys = options.searchKeys || [];
        const filtered = search
          ? allRows.filter((row) => searchKeys.some((k) => String(row[k] || "").toLowerCase().includes(search)))
          : allRows;
        const pageSize = options.pageSize || 10;
        const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
        if (action === "first") state.page = 0;
        else if (action === "prev") state.page = Math.max(0, state.page - 1);
        else if (action === "next") state.page = Math.min(totalPages - 1, state.page + 1);
        else if (action === "last") state.page = totalPages - 1;
        else if (action === "goto") state.page = parseInt(btn.getAttribute("data-page"), 10) || 0;
        body.innerHTML = renderPanelTableBody(table, panelKey, options);
        attachPagerOnly(panelKey, table, options);
      }, { once: true });
    }

    function renderDiagnostics(payload, showEmpty) {
      const sources = payload.sources || [];
      const issueSources = sources.filter((source) => source.status !== "ok");
      const hiddenBlocks = [];

      const hiddenTables = [
        ["주문 체결 현황 상세", payload.tables.order_status, 6],
        ["기간 수익률 원본", payload.tables.daily_profit_detail, 6],
      ];

      for (const [title, table, limit] of hiddenTables) {
        if ((table.row_count || 0) > 0 || showEmpty) {
          hiddenBlocks.push(buildSubpanel(title, table.row_count ? "상세 데이터" : "빈 섹션", table, { limit }));
        }
      }

      const sourceBlocks = issueSources.length > 0 || showEmpty
        ? `
          <div class="source-grid">
            ${(showEmpty ? sources : issueSources).map((source) => `
              <article class="source-card">
                <header>
                  <div class="source-title">${escapeHtml(source.title)}</div>
                  <span class="status-pill ${escapeHtml(source.status)}">${escapeHtml(source.status_label)}</span>
                </header>
                <div class="meta">${escapeHtml(source.api_id || "-")} · ${escapeHtml(String(source.record_count))}건<br>${escapeHtml(source.message || "메시지 없음")}</div>
              </article>
            `).join("")}
          </div>
        `
        : "";

      if (!sourceBlocks && hiddenBlocks.length === 0) {
        diagnosticsFold.hidden = true;
        return;
      }

      diagnosticsFold.hidden = false;
      diagnosticsFold.open = issueSources.length > 0;
      diagnosticsSummary.textContent = `숨겨진 섹션 ${hiddenBlocks.length}개 · 데이터 상태 ${showEmpty ? sources.length : issueSources.length}건`;
      sourceRoot.innerHTML = sourceBlocks;
      hiddenRoot.innerHTML = hiddenBlocks.join("");
    }

    function renderDashboard(payload) {
      currentPayload = payload;
      const showEmpty = showEmptyInput.checked;

      document.getElementById("account-name").textContent = payload.identity.account_name;
      document.getElementById("branch-name").textContent = payload.identity.branch_name;
      document.getElementById("env-label").textContent = payload.environment.label;
      document.getElementById("generated-at").textContent = new Date(payload.generated_at).toLocaleString("ko-KR");
      document.getElementById("base-url").textContent = payload.environment.base_url;
      document.getElementById("summary-note").textContent = `${payload.filters.start_date} ~ ${payload.filters.end_date}`;

      const envPill = document.getElementById("env-pill");
      envPill.className = `pill ${payload.environment.mode === "mock" ? "env-mock" : "env-live"}`;

      renderSummary(payload.summary || []);
      renderAssetChart(payload.asset_series);
      renderFocus(payload);
      renderAttention(payload);
      renderHoldings(payload);
      renderOrders(payload);
      renderPerformance(payload);
      renderActivity(payload, showEmpty);
      renderDiagnostics(payload, showEmpty);
      renderAgentPosition();
    }

    async function loadDashboard() {
      pageErrorRoot.innerHTML = "";
      const params = new URLSearchParams({
        start_date: startInput.value,
        end_date: endInput.value,
      });

      try {
        const response = await fetch(`/api/dashboard?${params.toString()}`);
        const payload = await response.json();

        if (!response.ok) {
          throw new Error(payload.error || "Dashboard request failed");
        }

        renderDashboard(payload);
      } catch (error) {
        pageErrorRoot.innerHTML = `<div class="error-banner">${escapeHtml(error.message || String(error))}</div>`;
      }
    }

    document.getElementById("filter-form").addEventListener("submit", (event) => {
      event.preventDefault();
      loadDashboard();
    });

    showEmptyInput.addEventListener("change", () => {
      if (currentPayload) {
        renderDashboard(currentPayload);
      }
    });

    // -- Agent overview rendering --------------------------------------

    const agentStatusRoot = document.getElementById("agent-status-root");
    const agentTimelineRoot = document.getElementById("agent-timeline-root");
    const agentNote = document.getElementById("agent-note");
    const agentDateInput = document.getElementById("agent-date");
    const agentReloadBtn = document.getElementById("agent-reload");

    function fmtKstShort(iso) {
      if (!iso) return "-";
      try {
        const d = new Date(iso);
        if (isNaN(d.getTime())) return iso;
        return d.toLocaleString("ko-KR", {
          timeZone: "Asia/Seoul",
          month: "2-digit",
          day: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
          hour12: false,
        });
      } catch (_) {
        return iso;
      }
    }

    // Live watcher config, grouped for reading. Labels only — every value comes
    // from the watcher's own /state payload. Nothing here has a default: if the
    // watcher does not report a key, the row is omitted rather than guessed.
    const CONFIG_GROUPS = [
      ["진입", [
        ["entry_mode", "진입 논리"], ["ma_period", "MA 기간"],
        ["universe_mode", "유니버스"], ["leaders_market_tp", "시장"],
        ["leaders_limit", "리더보드"], ["candidate_limit", "후보 수"],
      ]],
      ["게이트", [
        ["new_candidate_min_score", "Tier2 dispatch score"],
        ["auto_buy_min_score", "auto-buy score"],
        ["min_market_cap_krw", "최소 시총"],
        ["day_change_min", "day change 하한"], ["day_change_max", "day change 상한"],
      ]],
      ["포지션", [
        ["max_positions", "동시 보유"], ["max_new_positions", "사이클당 신규"],
        ["position_budget_pct", "종목당 비중"],
        ["max_daily_new_entries", "일일 신규 상한"],
        ["max_daily_loss_pct", "일일 손실 한도 %"], ["max_daily_loss_krw", "일일 손실 한도 원"],
      ]],
      ["청산", [
        ["stop_loss_pct", "손절"], ["hard_take_profit_pct", "익절"],
        ["stale_unfilled_minutes", "미체결 취소"],
      ]],
      ["Tier 2", [
        ["holding_swing_pct", "보유 변동"], ["intraday_high_drop_pct", "고점 이탈"],
        ["holding_dedup_profit_delta_pct", "holding dedup"],
        ["periodic_review_minutes", "정기 점검"],
        ["api_failure_threshold", "API 실패"], ["unfilled_threshold", "미체결 누적"],
      ]],
      ["에이전트", [
        ["poll_interval_seconds", "폴링"], ["cooldown_seconds", "cooldown"],
        ["agent_timeout_seconds", "agent timeout"],
        ["stale_price_delta_pct", "stale 임계"],
        ["agent_peer_review_enabled", "peer review"],
        ["agent_arbitration_enabled", "중재"],
      ]],
    ];

    function fmtConfigValue(key, value) {
      if (value === true) return "on";
      if (value === false) return "off";
      if (value === null || value === undefined || value === "") return null;
      if (Array.isArray(value)) {
        if (!value.length) return null;
        const head = value.slice(0, 3).join(", ");
        return value.length > 3 ? `${head} 외 ${value.length - 3}` : head;
      }
      if (typeof value === "number") {
        if (key === "min_market_cap_krw") {
          if (value <= 0) return "off";
          return value >= 1e12 ? `${(value / 1e12).toFixed(1)}조` : `${(value / 1e8).toFixed(0)}억`;
        }
        if (key === "max_daily_loss_krw") return value > 0 ? `${value.toLocaleString()}원` : "off";
        if (key.endsWith("_pct")) return `${value}%`;
        if (key.endsWith("_seconds")) return `${value}s`;
        if (key.endsWith("_minutes")) return `${value}분`;
      }
      return String(value);
    }

    function renderLiveConfig(config) {
      // The watcher predates this field (or is unreachable). Say so — do NOT
      // fall back to code defaults, which is exactly the bug this replaced.
      if (!config || !Object.keys(config).length) {
        return `<div class="agent-card agent-card--full agent-card--muted">
            <div class="agent-card-head"><strong>라이브 설정</strong></div>
            <div class="agent-muted">
              이 watcher는 설정을 보고하지 않습니다 (구버전).
              실제 값은 <code>k8s/kiwoom-watcher.yaml</code> 또는
              <code>kubectl -n tools get deploy kiwoom-watcher -o jsonpath='{.spec.template.spec.containers[0].args}'</code>
              로 직접 확인하세요.
            </div>
          </div>`;
      }
      const groups = CONFIG_GROUPS.map(([title, keys]) => {
        const cells = keys.map(([key, label]) => {
          const shown = fmtConfigValue(key, config[key]);
          if (shown === null) return "";
          return `<div><span class="agent-key">${escapeHtml(label)}</span><strong>${escapeHtml(shown)}</strong></div>`;
        }).filter(Boolean).join("");
        if (!cells) return "";
        return `<div class="agent-subhead">${escapeHtml(title)}</div>
                <div class="agent-metric-row">${cells}</div>`;
      }).filter(Boolean).join("");
      return `
        <div class="agent-card agent-card--full">
          <div class="agent-card-head">
            <strong>라이브 설정</strong>
            <span class="agent-muted">watcher가 보고한 실행 중인 값</span>
          </div>
          ${groups}
        </div>`;
    }

    function renderOpsDetails(payload) {
      if (!payload) {
        agentStatusRoot.innerHTML = '<div class="empty-state">Agent 상태 데이터를 불러오지 못했습니다.</div>';
        return;
      }
      const watcher = payload.watcher || {};
      const autopilot = payload.autopilot || {};
      const ws = (watcher.status === "ok" && watcher.state) ? watcher.state : null;

      // Watcher live state card
      let liveHtml = "";
      if (ws) {
        const regime = ws.regime || {};
        const errorBadge = ws.last_error
          ? `<div class="agent-error">⚠️ ${escapeHtml(ws.last_error)}</div>` : "";
        const stoppedBadge = ws.stopped_at
          ? `<div class="agent-error">⚠️ watcher가 ${fmtKstShort(ws.stopped_at)}에 정지했습니다.</div>` : "";
        // A degraded index read forces breadth to 0, which is numerically
        // indistinguishable from a crash — flag it rather than let the number lie.
        const degradedBadge = (regime.market_data_complete === false)
          ? `<div class="agent-error">⚠️ 지수 조회 불완전 — regime 수치를 신뢰할 수 없습니다 (신규 진입 차단됨).</div>` : "";
        const riskOffBadge = regime.extreme_risk_off
          ? `<span class="agent-pill agent-pill--err">extreme_risk_off</span>` : "";
        const inFlightHtml = (ws.in_flight && ws.in_flight.length)
          ? `<ul class="agent-list">${ws.in_flight.map(s =>
              `<li><strong>${escapeHtml(s.target_role || "?")}</strong> · ${escapeHtml(s.trigger_type)} ${s.stock_code ? `(${escapeHtml(s.stock_code)} ${escapeHtml(s.stock_name || "")})` : ""} · 시작 ${fmtKstShort(s.started_at)}</li>`
            ).join("")}</ul>`
          : `<div class="agent-muted">현재 in-flight 없음</div>`;

        // Cumulative per-stage failures. api_failure_count is a *consecutive*
        // counter that any success resets, so it can read 0 while hundreds of
        // intermittent failures pile up — these are the ones that show that.
        const failures = ws.failures || {};
        const failKeys = Object.keys(failures);
        const failHtml = failKeys.length
          ? `<div class="agent-subhead">누적 실패</div>
             <ul class="agent-list">${failKeys.map(k => {
               const f = failures[k] || {};
               const rate = ws.cycle_count ? ((f.count / ws.cycle_count) * 100).toFixed(1) : null;
               const tone = (rate !== null && rate >= 10) ? "err" : (rate !== null && rate >= 2) ? "warn" : "info";
               return `<li><span class="agent-pill agent-pill--${tone}">${escapeHtml(k)}</span>
                 ${f.count}건${rate !== null ? ` · ${rate}%` : ""}
                 <span class="agent-muted">${f.last_detail ? ` · ${escapeHtml(String(f.last_detail).slice(0, 120))}` : ""}</span></li>`;
             }).join("")}</ul>`
          : "";

        const breaker = ws.daily_entry_breaker;
        let breakerHtml = "";
        if (breaker) {
          const bits = [];
          if (breaker.tripped) {
            bits.push(`<span class="agent-pill agent-pill--err">차단됨</span> ${escapeHtml(breaker.trip_reason || breaker.trip_code || "")}`);
          } else if (breaker.enabled) {
            bits.push(`<span class="agent-pill agent-pill--ok">정상</span>`);
          } else {
            bits.push(`<span class="agent-pill agent-pill--off">비활성</span>`);
          }
          const limits = breaker.limits || {};
          if (limits.max_daily_new_entries) {
            bits.push(`신규 ${breaker.new_entries ?? 0}/${limits.max_daily_new_entries}건`);
          }
          // Loss limits armed but unverified block ALL new entries — the single
          // most surprising silent state in the system. Never hide it.
          if (breaker.loss_source_status === "unverified") {
            bits.push(`<span class="agent-pill agent-pill--warn">손익 소스 미검증 — 신규 매수 전면 차단</span>`);
          }
          if (breaker.state_error) {
            bits.push(`<span class="agent-pill agent-pill--err">${escapeHtml(breaker.state_error)}</span>`);
          }
          breakerHtml = `<div class="agent-subhead">일일 서킷브레이커</div>
                         <div class="agent-list"><li>${bits.join(" · ")}</li></div>`;
        }

        const cooldowns = ws.cooldowns || {};
        const cdKeys = Object.keys(cooldowns);
        const cooldownHtml = cdKeys.length
          ? `<div class="agent-subhead">Cooldown (재발화 억제 중)</div>
             <ul class="agent-list">${cdKeys.slice(0, 8).map(k =>
               `<li><code>${escapeHtml(k)}</code> <span class="agent-muted">→ ${fmtKstShort(cooldowns[k])}</span></li>`
             ).join("")}${cdKeys.length > 8 ? `<li class="agent-muted">외 ${cdKeys.length - 8}건</li>` : ""}</ul>`
          : "";

        liveHtml = `
          <div class="agent-card agent-card--live agent-card--full">
            <div class="agent-card-head">
              <span>
                <span class="agent-pill ${ws.execute_orders ? "agent-pill--exec" : "agent-pill--dry"}">
                  ${escapeHtml(ws.mode ? String(ws.mode).toUpperCase() : "-")} · ${ws.execute_orders ? "EXECUTE" : "DRY-RUN"}
                </span>
                ${riskOffBadge}
              </span>
              <span class="agent-muted">last tick ${fmtKstShort(ws.last_tick_at)}</span>
            </div>
            <div class="agent-metric-row">
              <div><span class="agent-key">cycle</span><strong>${ws.cycle_count ?? 0}</strong></div>
              <div><span class="agent-key">regime</span><strong>${escapeHtml(regime.regime || "-")}</strong></div>
              <div><span class="agent-key">${escapeHtml(regime.primary_market || "primary")} chg</span><strong>${regime.primary_change_pct ?? "-"}%</strong></div>
              <div><span class="agent-key">breadth</span><strong>${regime.primary_breadth ?? regime.breadth_score ?? "-"}</strong></div>
              <div><span class="agent-key">holdings</span><strong>${(ws.portfolio||{}).holding_count ?? "-"}</strong></div>
              <div><span class="agent-key">open orders</span><strong>${(ws.portfolio||{}).open_order_count ?? "-"}</strong></div>
              <div><span class="agent-key">candidates</span><strong>${(ws.portfolio||{}).candidate_count ?? "-"}</strong></div>
              <div><span class="agent-key">연속 API 실패</span><strong>${ws.api_failure_count ?? 0}</strong></div>
            </div>
            <div class="agent-subhead">In-flight Tier 2</div>
            ${inFlightHtml}
            ${breakerHtml}
            ${failHtml}
            ${cooldownHtml}
            ${degradedBadge}
            ${stoppedBadge}
            ${errorBadge}
          </div>`;
      } else {
        liveHtml = `<div class="agent-card agent-card--live agent-card--muted agent-card--full">
            <div class="agent-card-head">
              <span class="agent-pill agent-pill--dry">Watcher 상태 미가용</span>
            </div>
            <div class="agent-muted">${escapeHtml(watcher.error || "watcher status server 응답 없음")}</div>
          </div>`;
      }

      // Autopilot cards
      let autopilotsHtml = "";
      if (autopilot.status === "ok" && Array.isArray(autopilot.autopilots) && autopilot.autopilots.length) {
        autopilotsHtml = autopilot.autopilots.map(ap => {
          const trigs = (ap.triggers || []).map(t => `
            <div class="agent-trigger">
              <code>${escapeHtml(t.cron || "?")}</code>
              <span class="agent-muted"> · next ${fmtKstShort(t.next_run_at)}</span>
              ${t.last_fired_at ? `<span class="agent-muted"> · last ${fmtKstShort(t.last_fired_at)}</span>` : ""}
              ${t.enabled === false ? '<span class="agent-pill agent-pill--off">disabled</span>' : ""}
            </div>`).join("");
          return `
            <div class="agent-card">
              <div class="agent-card-head">
                <strong>${escapeHtml(ap.title || "?")}</strong>
                <span class="agent-pill ${ap.status === "active" ? "agent-pill--ok" : "agent-pill--off"}">${escapeHtml(ap.status || "?")}</span>
              </div>
              ${trigs || '<div class="agent-muted">트리거 없음</div>'}
              ${ap.error ? `<div class="agent-error">${escapeHtml(ap.error)}</div>` : ""}
            </div>`;
        }).join("");
      } else {
        autopilotsHtml = `<div class="agent-card agent-card--muted">
            <div class="agent-card-head"><strong>Autopilot 상태</strong></div>
            <div class="agent-muted">${escapeHtml(autopilot.error || "정보 없음")}</div>
          </div>`;
      }

      agentStatusRoot.innerHTML = `
        <div class="agent-grid">
          ${liveHtml}
          ${renderLiveConfig(ws ? ws.config : null)}
          ${autopilotsHtml}
        </div>`;
    }


    // -- Agent tab: operator view ---------------------------------------
    //
    // Top to bottom the tab answers the questions an operator actually has:
    // is it running, what is it trying to do, where is the money relative to
    // its exits, what is waiting to get in, and what did the agents decide.
    // The raw status card and the full parameter dump still exist, folded at
    // the bottom — they are for diagnosis, not for reading the situation.

    const agentStripRoot = document.getElementById("agent-strip-root");
    const agentStrategyRoot = document.getElementById("agent-strategy-root");
    const agentPositionRoot = document.getElementById("agent-position-root");
    const agentPositionNote = document.getElementById("agent-position-note");
    const agentPipelineRoot = document.getElementById("agent-pipeline-root");
    const agentPipelineNote = document.getElementById("agent-pipeline-note");
    let latestOverview = null;

    function toNum(value) {
      if (value === null || value === undefined || value === "") return null;
      const n = Number(String(value).replace(/,/g, ""));
      return Number.isFinite(n) ? n : null;
    }

    function signedPct(value, digits = 2) {
      if (value === null || value === undefined || !Number.isFinite(Number(value))) return "-";
      const n = Number(value);
      return `${n > 0 ? "+" : ""}${n.toFixed(digits)}%`;
    }

    function wonText(value) {
      return value === null || value === undefined ? "-" : `${Math.round(value).toLocaleString("ko-KR")}원`;
    }

    function kstDate(iso) {
      if (!iso) return null;
      const d = new Date(iso);
      if (isNaN(d.getTime())) return null;
      return new Intl.DateTimeFormat("en-CA", {
        timeZone: "Asia/Seoul", year: "numeric", month: "2-digit", day: "2-digit",
      }).format(d);
    }

    // The watcher's counters live in memory and only move while it ticks, so
    // outside the session — or after a rollout before the open — every live
    // field is zero, which reads exactly like a dead process (2026-09-24,
    // Chuseok). It persists its last tick to the PVC and republishes that as
    // `last_session` on start; that is what gets shown, and it is labelled.
    function watcherView(overview) {
      const watcher = (overview && overview.watcher) || {};
      const ws = watcher.status === "ok" ? watcher.state : null;
      if (!ws) return { ws: null, src: null, live: false, error: watcher.error || "watcher 응답 없음" };
      if ((ws.cycle_count || 0) > 0) return { ws, src: ws, live: true };
      if (ws.last_session) return { ws, src: ws.last_session, live: false };
      return { ws, src: null, live: false };
    }

    const REGIME_LABELS = { risk_on: "강세", neutral: "중립", risk_off: "약세" };

    function statHtml(key, dot, value, sub) {
      return `<div class="ag-stat">
          <div class="k">${escapeHtml(key)}</div>
          <div class="v"><span class="ag-dot ag-dot--${dot}"></span>${value}</div>
          ${sub ? `<div class="s">${sub}</div>` : ""}
        </div>`;
    }

    function renderAgentStrip(overview) {
      const session = overview.session || {};
      const view = watcherView(overview);
      const ws = view.ws;
      const src = view.src;
      const cards = [];

      // 1. Market session — computed server-side from the same KRX calendar
      //    the watcher gates on, so it never depends on the watcher.
      const phaseDot = {
        open: "ok", pre_open: "off", after_close: "off", holiday: "off", uncertain: "warn",
      }[session.phase] || "off";
      const nextOpen = session.next_open
        ? `다음 개장 ${fmtKstShort(session.next_open)}${session.next_open_uncertain ? " (특별장 미확인)" : ""}`
        : "다음 개장 미정 (캘린더 범위 밖)";
      cards.push(statHtml(
        "시장",
        phaseDot,
        `${escapeHtml(session.label || "-")}${session.reason ? ` <span class="agent-muted">${escapeHtml(session.reason)}</span>` : ""}`,
        session.is_open
          ? `${escapeHtml(session.opens_at || "")} ~ ${escapeHtml(session.closes_at || "")}`
          : escapeHtml(nextOpen),
      ));

      // 2. Watcher liveness. During the session a stale tick is the one state
      //    that matters most, so it turns red rather than staying a quiet number.
      if (!ws) {
        cards.push(statHtml("Watcher", "err", "응답 없음", escapeHtml(view.error || "")));
      } else {
        let dot = "ok";
        const lastTick = ws.last_tick_at ? new Date(ws.last_tick_at) : null;
        const ageMin = lastTick ? (Date.now() - lastTick.getTime()) / 60000 : null;
        const stuck = session.is_open && (ageMin === null || ageMin > 3);
        if (ws.stopped_at || stuck) dot = "err";
        else if (ws.last_error) dot = "warn";
        let sub;
        if (view.live) sub = `마지막 틱 ${fmtKstShort(ws.last_tick_at)} · ${ws.cycle_count}회`;
        else if (src) sub = `이번 기동 후 틱 없음 · 직전 틱 ${fmtKstShort(src.last_tick_at)}`;
        else sub = "틱 기록 없음";
        if (stuck && !ws.stopped_at) sub = `⚠️ 장중인데 틱이 멈춤 · ${sub}`;
        cards.push(statHtml(
          "Watcher",
          dot,
          ws.stopped_at ? "정지" : (ws.execute_orders ? "실거래" : "Dry-run"),
          escapeHtml(sub),
        ));
      }

      // 3. Regime.
      const regime = (src && src.regime) || null;
      if (regime && regime.regime) {
        const extreme = regime.extreme_risk_off;
        const incomplete = regime.market_data_complete === false;
        // Weakness is the setup below_ma buys into, so risk_off is not a
        // warning here — only a crash veto or an unreadable index is.
        const dot = extreme || incomplete ? "err" : "off";
        const extra = extreme
          ? ` <span class="agent-pill agent-pill--err">급락 · 신규 차단</span>`
          : incomplete ? ` <span class="agent-pill agent-pill--err">지수 조회 불완전</span>` : "";
        const mkt = String(regime.primary_market || "kospi").toUpperCase();
        cards.push(statHtml(
          "시장 레짐",
          dot,
          `${escapeHtml(REGIME_LABELS[regime.regime] || regime.regime)}${extra}`,
          `${escapeHtml(mkt)} ${signedPct(regime.primary_change_pct)} · 상승종목 비율 ${escapeHtml(String(regime.primary_breadth ?? "-"))}`,
        ));
      } else {
        cards.push(statHtml("시장 레짐", "off", "-", "첫 틱 이후 표시"));
      }

      // 4. New-entry gate (daily breaker).
      const breaker = (ws && ws.daily_entry_breaker) || (src && src.daily_entry_breaker) || null;
      if (breaker) {
        const limits = breaker.limits || {};
        const max = limits.max_daily_new_entries;
        const lossOn = (limits.max_daily_loss_pct > 0) || (limits.max_daily_loss_krw > 0);
        let dot = "ok";
        let value = "정상";
        if (breaker.tripped) { dot = "err"; value = "차단"; }
        // Loss limits armed on an unverified P&L source block every new buy —
        // the most surprising silent state in the system. Never hide it.
        else if (breaker.loss_source_status === "unverified") { dot = "err"; value = "전면 차단"; }
        else if (breaker.state_error) { dot = "warn"; value = "상태 오류"; }
        const bits = [];
        if (breaker.tripped && breaker.trip_reason) bits.push(escapeHtml(breaker.trip_reason));
        if (max) {
          const today = kstDate(new Date().toISOString());
          const day = breaker.trading_day === today ? "오늘" : escapeHtml(breaker.trading_day || "");
          bits.push(`${day} ${breaker.new_entries ?? 0}/${max}건`);
        }
        bits.push(lossOn ? "손실 한도 켜짐" : "손실 한도 꺼짐");
        cards.push(statHtml("진입 차단기", dot, value, bits.join(" · ")));
      } else {
        cards.push(statHtml("진입 차단기", "off", "-", "첫 틱 이후 표시"));
      }

      // 5. Anomalies.
      if (ws) {
        const failures = ws.failures || {};
        const total = Object.values(failures).reduce((a, f) => a + (f.count || 0), 0);
        const inflight = (ws.in_flight || []).length;
        const dot = ws.last_error ? "err" : (total > 0 ? "warn" : "ok");
        const value = ws.last_error ? "오류" : (total > 0 ? `실패 ${total}건` : "없음");
        const bits = [inflight ? `agent 응답 대기 ${inflight}건` : "agent 응답 대기 없음"];
        if (ws.last_error) bits.unshift(escapeHtml(String(ws.last_error).slice(0, 80)));
        cards.push(statHtml("이상 징후", dot, value, bits.join(" · ")));
      }

      const asof = (!view.live && src)
        ? `<div class="ag-asof">watcher가 이번 기동(${fmtKstShort(ws.started_at)}) 후 아직 틱하지 않아, 레짐·진입 차단기·후보는 직전 세션(${fmtKstShort(src.last_tick_at)}) 값입니다.</div>`
        : "";
      agentStripRoot.innerHTML = `${asof}<div class="ag-strip">${cards.join("")}</div>`;
    }

    // The strategy in words, built only from the watcher's effective config.
    // If the watcher does not report a key the sentence says "?" rather than
    // filling in a code default — that substitution is the bug §7 warns about.
    function renderAgentStrategy(overview) {
      const view = watcherView(overview);
      const c = (view.ws && view.ws.config) || null;
      if (!c || !Object.keys(c).length) {
        agentStrategyRoot.innerHTML = `<div class="ag-empty">watcher가 실효 설정을 보고하지 않아 전략을 구성할 수 없습니다.<br>코드 기본값으로 추정하지 않습니다.</div>`;
        return;
      }
      const k = overview.strategy_constants || {};
      const n = (v) => `<span class="num">${escapeHtml(String(v))}</span>`;
      const market = { "001": "KOSPI", "101": "KOSDAQ", "000": "KOSPI·KOSDAQ" }[c.leaders_market_tp] || "";
      const cap = c.min_market_cap_krw > 0
        ? `시총 ${fmtConfigValue("min_market_cap_krw", c.min_market_cap_krw)} 이상`
        : "시총 제한 없음";
      const universe = c.universe_mode === "roster" ? `${market} 대형주 고정 로스터`
        : c.universe_mode === "both" ? `대형주 로스터 + ${market} 리더보드 상위 ${c.leaders_limit}`
        : `${market} 리더보드 상위 ${c.leaders_limit}`;
      const band = k.below_ma_max_dip_pct ?? "?";
      const entry = c.entry_mode === "below_ma"
        ? `MA${c.ma_period} 아래로 0~${band}% 눌린 종목`
        : `당일 ${c.day_change_min}~${c.day_change_max}% 오른 종목`;
      const budget = toNum(c.position_budget_pct);
      const stop = toNum(c.stop_loss_pct);
      const perLoss = budget !== null && stop !== null ? Math.abs(budget * stop / 100) : null;
      const lossOn = (c.max_daily_loss_pct > 0) || (c.max_daily_loss_krw > 0);

      const lead = `<strong>${escapeHtml(universe)}</strong>(${escapeHtml(cap)})에서
        <strong>${escapeHtml(entry)}</strong>을 찾아, 점수 <strong>${escapeHtml(String(c.new_candidate_min_score))}점 이상</strong>이면
        스크리너 agent에게 묻고 승인되면 매수합니다.
        <strong>손절 ${escapeHtml(String(c.stop_loss_pct))}% · 익절 +${escapeHtml(String(c.hard_take_profit_pct))}%</strong>는
        코드가 즉시 시장가로 청산하고, 그 사이 구간의 매도는 평가사 agent가 판단합니다.`;

      const rule = (title, items) => `<div class="ag-rule"><div class="t">${escapeHtml(title)}</div>
          <ul>${items.filter(Boolean).map((i) => `<li>${i}</li>`).join("")}</ul></div>`;

      agentStrategyRoot.innerHTML = `
        <p class="ag-lead">${lead}</p>
        <div class="ag-rules">
          ${rule("진입", [
            `${escapeHtml(universe)} · ${escapeHtml(cap)}`,
            c.entry_mode === "below_ma"
              ? `MA${n(c.ma_period)} 대비 ${n(`0~${band}%`)} 아래 (평균회귀)`
              : `당일 ${n(`${c.day_change_min}~${c.day_change_max}%`)} 상승 (모멘텀)`,
            `점수 ${n(`${c.new_candidate_min_score}+`)} → 스크리너 판정`,
            "TIER1은 전액, TIER2는 절반으로 매수",
          ])}
          ${rule("청산", [
            `손절 ${n(`${c.stop_loss_pct}%`)} · 익절 ${n(`+${c.hard_take_profit_pct}%`)} — 즉시 시장가 (코드)`,
            `보유 ${n(`±${c.holding_swing_pct}%`)} 변동 또는 고점 대비 ${n(`-${c.intraday_high_drop_pct}%`)} → 평가사 판단`,
            c.stale_unfilled_minutes ? `미체결 ${n(`${c.stale_unfilled_minutes}분`)} 뒤 자동 취소` : "",
          ])}
          ${rule("비중", [
            budget !== null ? `종목당 자산 ${n(`${budget}%`)} (TIER2 ${n(`${budget / 2}%`)})` : "",
            `동시 보유 최대 ${n(c.max_positions)}종목`,
            c.max_daily_new_entries > 0 ? `하루 신규 최대 ${n(c.max_daily_new_entries)}건` : "하루 신규 건수 제한 없음",
            perLoss !== null ? `손절 1회 ≈ 계좌 ${n(`-${perLoss.toFixed(1)}%`)} (TIER1 기준)` : "",
          ])}
          ${rule("안전장치", [
            view.ws.execute_orders
              ? `<span class="agent-pill agent-pill--exec">실주문</span> 활성`
              : `<span class="agent-pill agent-pill--dry">Dry-run</span> 주문 없음`,
            "시장 급락·지수 조회 불완전 시 신규 매수 차단",
            lossOn ? "일일 손실 한도 켜짐" : `<span class="agent-pill agent-pill--warn">일일 손실 한도 꺼짐</span>`,
            "PM·리스크 판단은 기록만 (주문 없음)",
          ])}
        </div>`;
    }

    // Holdings from the broker (the trading tab's payload, always available)
    // placed on a stop → take scale from the watcher's config.
    function renderAgentPosition() {
      if (!latestOverview) return;  // agent tab not opened yet
      const view = watcherView(latestOverview);
      const c = (view.ws && view.ws.config) || {};
      const stop = toNum(c.stop_loss_pct);
      const take = toNum(c.hard_take_profit_pct);
      if (!currentPayload) {
        agentPositionRoot.innerHTML = `<div class="ag-empty">계좌 조회 중…</div>`;
        return;
      }
      agentPositionNote.textContent = `계좌 조회 ${new Date(currentPayload.generated_at).toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" })}`;
      const table = (currentPayload.tables || {}).holdings || {};
      const holdings = (table.rows || []).map((r) => ({
        name: r.stock_name || r.stock_code,
        code: String(r.stock_code || "").replace(/^A/, ""),
        qty: toNum(r.quantity),
        avg: toNum(r.avg_price),
        cur: toNum(r.current_price),
        pl: toNum(r.profit_loss),
        rate: toNum(r.profit_rate),
        value: toNum(r.evaluation_amount),
      })).filter((h) => h.qty);

      if (!holdings.length) {
        agentPositionRoot.innerHTML = `<div class="ag-empty">보유 종목 없음 — 빈 슬롯 ${escapeHtml(String(c.max_positions ?? "-"))}개.<br>점수 게이트를 넘는 후보가 나오면 스크리너가 호출됩니다.</div>`;
        return;
      }

      const scaleOk = stop !== null && take !== null && take > stop;
      const clamp = (v) => Math.max(0, Math.min(100, v));
      agentPositionRoot.innerHTML = holdings.map((h) => {
        const up = (h.rate ?? 0) >= 0;
        const color = up ? "var(--positive)" : "var(--negative)";
        let bar = "";
        if (scaleOk) {
          const span = take - stop;
          const entryPos = clamp((0 - stop) / span * 100);
          const nowPos = clamp(((h.rate ?? 0) - stop) / span * 100);
          const stopPrice = h.avg ? h.avg * (1 + stop / 100) : null;
          const takePrice = h.avg ? h.avg * (1 + take / 100) : null;
          const toStop = h.rate !== null ? (h.rate - stop).toFixed(2) : "-";
          const toTake = h.rate !== null ? (take - h.rate).toFixed(2) : "-";
          bar = `
            <div class="ag-bar">
              <div class="ag-bar-entry" style="left:${entryPos}%" title="매수가"></div>
              <div class="ag-bar-now ag-bar-now--${up ? "up" : "down"}" style="left:${nowPos}%"></div>
              <div class="ag-bar-tag" style="left:${nowPos}%; color:${color}">${signedPct(h.rate)}</div>
            </div>
            <div class="ag-bar-labels">
              <div><div class="p">≈ ${wonText(stopPrice)}</div><div class="l">손절 ${stop}% · 여유 ${toStop}%p</div></div>
              <div><div class="p">≈ ${wonText(takePrice)}</div><div class="l">익절 +${take}% · 남은 ${toTake}%p</div></div>
            </div>`;
        }
        return `<div class="ag-pos">
            <div class="ag-pos-head">
              <div>
                <div class="ag-pos-name">${escapeHtml(h.name)} <span class="mono agent-muted">${escapeHtml(h.code)}</span></div>
                <div class="ag-pos-sub">${h.qty}주 · 평단 ${wonText(h.avg)} · 현재 ${wonText(h.cur)} · 평가 ${wonText(h.value)}</div>
              </div>
              <div style="text-align:right">
                <div class="ag-pos-rate" style="color:${color}">${signedPct(h.rate)}</div>
                <div class="ag-pos-sub">${wonText(h.pl)}</div>
              </div>
            </div>
            ${bar}
          </div>`;
      }).join("") + `<div class="agent-muted" style="margin-top:12px">세로선은 매수가. 손절·익절 가격은 평단 기준 근사값이고, 실제 발동은 증권사 평가 수익률(비용 반영)로 판정합니다.</div>`;
    }

    function renderAgentPipeline(overview) {
      const view = watcherView(overview);
      const c = (view.ws && view.ws.config) || {};
      const src = view.src;
      const board = src && src.candidates;
      const slots = src && src.candidate_slots;
      agentPipelineNote.textContent = board && board.at
        ? `${view.live ? "" : "직전 세션 · "}${fmtKstShort(board.at)} 틱 기준`
        : "-";
      const parts = [];

      if (board) {
        const blocked = board.qualified > 0 && board.available_slots <= 0;
        const step = (label, value, cls = "") =>
          `<div class="ag-step ${cls}"><strong>${escapeHtml(String(value ?? "-"))}</strong>${escapeHtml(label)}</div>`;
        const arrow = `<span class="ag-arrow">→</span>`;
        const steps = [step("스캔", board.scanned)];
        if (board.in_band !== null && board.in_band !== undefined) steps.push(step("MA 밴드 안", board.in_band));
        steps.push(step("진입 조건 통과", board.eligible));
        steps.push(step(`점수 ${board.min_score}+`, board.qualified));
        steps.push(step("빈 슬롯", board.available_slots, blocked ? "ag-step--block" : ""));
        parts.push(`<div class="ag-funnel">${steps.join(arrow)}</div>`);
        if (blocked) {
          // At zero slots the detector returns before building an event, so the
          // screener is never asked. A board full of 9s would otherwise read as
          // the system ignoring them.
          parts.push(`<div class="ag-callout">게이트를 넘은 후보 ${board.qualified}개가 있지만 빈 슬롯이 없어 <strong>스크리너를 호출하지 않았습니다</strong> (동시 보유 ${escapeHtml(String(c.max_positions ?? "-"))}종목 한도).</div>`);
        } else if (board.qualified === 0) {
          parts.push(`<div class="ag-callout">이 틱에는 점수 ${board.min_score}점을 넘은 후보가 없습니다.</div>`);
        }
      }

      if (slots && slots.qualified_ticks) {
        const pct = Math.round(slots.starved_ticks / slots.qualified_ticks * 100);
        parts.push(`<div class="agent-muted" style="margin-bottom:10px">
            ${escapeHtml(slots.trading_day || "")} 하루: 게이트 통과 후보가 있던 틱 <strong>${slots.qualified_ticks}</strong> 중
            <strong>${slots.starved_ticks}</strong>틱(${pct}%)은 빈 슬롯이 없었음${slots.best_starved_name
              ? ` · 막힌 최고 <strong>${escapeHtml(slots.best_starved_name)} ${escapeHtml(String(slots.best_starved_score))}점</strong>`
              : ""}
          </div>`);
      }

      if (board && board.top && board.top.length) {
        const maxScore = Math.max(10, ...board.top.map((r) => r.score || 0));
        parts.push(`<div class="ag-table-wrap"><table class="agent-table">
            <thead><tr><th>종목</th><th>점수</th><th>MA 대비</th><th>당일</th><th>상태</th></tr></thead>
            <tbody>${board.top.map((r) => `<tr>
              <td>${escapeHtml(r.stock_name || r.stock_code || "-")}</td>
              <td><span class="ag-score ${r.qualified ? "ag-score--pass" : ""}">${escapeHtml(String(r.score ?? "-"))}<i style="width:${Math.round((r.score || 0) / maxScore * 44)}px"></i></span></td>
              <td class="mono">${r.ma_dip_pct !== null && r.ma_dip_pct !== undefined ? signedPct(-r.ma_dip_pct) : "-"}</td>
              <td class="mono">${signedPct(r.day_change_pct)}</td>
              <td>${r.qualified
                ? '<span class="agent-pill agent-pill--ok">게이트 통과</span>'
                : r.blocked_by
                  ? `<span class="agent-muted">${escapeHtml(r.blocked_by)}</span>`
                  : '<span class="agent-muted">점수 미달</span>'}</td>
            </tr>`).join("")}</tbody>
          </table></div>`);
      }

      if (!parts.length) {
        parts.push(`<div class="ag-empty">후보 기록이 아직 없습니다.<br>다음 거래일 첫 틱부터 표시됩니다.</div>`);
      }
      agentPipelineRoot.innerHTML = parts.join("");
    }

    function renderAgentOverview(payload) {
      if (!payload) {
        agentStripRoot.innerHTML = '<div class="empty-state">Agent 상태 데이터를 불러오지 못했습니다.</div>';
        return;
      }
      latestOverview = payload;
      agentNote.textContent = `갱신 ${fmtKstShort(payload.generated_at)}`;
      renderAgentStrip(payload);
      renderAgentStrategy(payload);
      renderAgentPosition();
      renderAgentPipeline(payload);
      renderOpsDetails(payload);
    }

    // On a holiday or before the open, "today" has no decisions yet. Opening
    // the tab on an empty timeline hides the last session's reasoning behind a
    // date picker; default to the day the watcher last ticked instead.
    function defaultTimelineDate() {
      if (!agentDateInput || agentDateInput.value || !latestOverview) return;
      const phase = (latestOverview.session || {}).phase;
      if (phase !== "holiday" && phase !== "pre_open") return;
      const view = watcherView(latestOverview);
      const day = kstDate(view.src && view.src.last_tick_at);
      if (day) agentDateInput.value = day;
    }

    // -- Agent decision timeline ----------------------------------------
    function snapshotChips(snapshot) {
      if (!snapshot || typeof snapshot !== "object") return "";
      // Show the handful of fields that actually drove the decision; the full
      // object is one click away in the <details> body.
      const PICK = [
        ["score", "score"], ["day_change_pct", "day chg"],
        ["orderbook_ratio", "호가비율"], ["spread_pct", "스프레드"],
        ["profit_rate", "수익률"], ["current_price", "현재가"],
        ["ma_dip_pct", "MA 이탈"], ["volume_ratio_20d", "거래량배수"],
        ["interval_minutes", "간격"],
        ["quantity", "수량"],
      ];
      const chips = PICK.map(([key, label]) => {
        const v = snapshot[key];
        if (v === undefined || v === null) return "";
        const suffix = key.endsWith("_pct") ? "%" : (key === "interval_minutes" ? "분" : "");
        const shown = typeof v === "number" ? v.toLocaleString() : String(v);
        return `<span class="agent-chip">${escapeHtml(label)} <strong>${escapeHtml(shown)}${suffix}</strong></span>`;
      }).filter(Boolean).join("");
      return chips;
    }

    function stripActionTag(text) {
      // The `<!-- ACTION: X -->` marker is already rendered as a pill; leaving it
      // in the prose just shows raw HTML comment syntax to the reader.
      return String(text || "").replace(/<!--[\s\S]*?-->/g, "").trim();
    }

    function actionPillClass(action) {
      if (!action) return "off";
      if (action === "TIER1" || action === "TIER2") return "ok";
      if (action === "REJECT" || action === "HOLD" || action === "ACKNOWLEDGE") return "info";
      if (action === "CUT_LOSS" || action === "ESCALATE") return "err";
      return "warn";
    }

    function outcomeBadgeHtml(row) {
      const src = row.outcome_source;
      if (src === "watcher" && row.outcome) {
        const o = row.outcome;
        const label = o.outcome || "-";
        return `<span class="agent-pill agent-pill--${outcomeColor(label)}">${escapeHtml(label)}</span>`
          + (o.detail ? `<span class="agent-muted"> ${escapeHtml(String(o.detail).slice(0, 140))}</span>` : "");
      }
      // A delegation yields a second opinion, not an order — there is nothing
      // to reconcile, so an "미확인" badge would be misleading.
      if (src === "not_applicable") return "";
      // The whole payload is unjoinable (watcher restarted / unreachable). One
      // banner already says so — repeating it on every row would read like N
      // separate reconciliation failures.
      if (src === "unavailable") return "";
      // Never say "주문 없음" here. Not observed is a different claim from not
      // placed, and conflating them would hide a real order.
      const why = src === "ambiguous"
        ? "동일 시각 트리거가 겹쳐 대사 불가"
        : "매칭되는 watcher 기록 없음";
      return `<span class="agent-pill agent-pill--off">주문 결과 미확인</span>
              <span class="agent-muted"> ${escapeHtml(why)}</span>`;
    }

    const TRIGGER_LABELS = {
      periodic_review: "정기 점검",
      regime_flip: "레짐 전환",
      extreme_risk_off: "시장 급락",
      holding_swing: "보유 변동",
      new_candidate: "신규 후보",
      api_failures: "API 장애",
      unfilled_overflow: "미체결 누적",
      stop_loss: "손절",
      hard_take_profit: "익절",
      max_positions_overflow: "보유 초과",
      stale_unfilled_order: "미체결 취소",
      squad_delegation: "위임",
    };

    function triggerLabel(type) {
      return TRIGGER_LABELS[type] || type || "-";
    }

    // Agents answer in markdown; rendering it as plain text left `**결정:
    // HOLD**` and bullet dashes on screen. Only what the agents actually use:
    // paragraphs, `- ` bullets, **bold**, `code`. Escaped first, so this can
    // never inject markup.
    function mdLite(text) {
      const lines = escapeHtml(stripActionTag(text)).split(/\n/);
      const inline = (t) => t
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/`([^`]+)`/g, "<code>$1</code>");
      let html = "";
      let inList = false;
      for (const raw of lines) {
        const line = raw.trim();
        const bullet = line.match(/^[-*]\s+(.*)$/);
        if (bullet) {
          if (!inList) { html += "<ul>"; inList = true; }
          html += `<li>${inline(bullet[1])}</li>`;
          continue;
        }
        if (inList) { html += "</ul>"; inList = false; }
        if (line) html += `<p>${inline(line)}</p>`;
      }
      if (inList) html += "</ul>";
      return `<div class="ag-md">${html}</div>`;
    }

    // One line per decision. The agents lead with "결정: X" (already the
    // pill), a re-quote timestamp, and a recital of the holding — quantity,
    // average price, current price — which the position panel already shows.
    // On 2026-09-23 that recital was the first line of seven of eight
    // answers, so the gist skips it to reach the first line with a reason.
    function gistOf(text) {
      const lines = stripActionTag(text).split(/\n/).map((l) => l.trim()).filter(Boolean);
      let fallback = "";
      for (const line of lines) {
        let t = line.replace(/^[-*]\s+/, "").replace(/\*\*/g, "").replace(/`/g, "");
        if (/^결정\s*[:：]/.test(t) && t.length < 30) continue;
        t = t.replace(/^\d{1,2}:\d{2}(\s*~\s*\d{1,2}:\d{2})?\s*KST\s*(라이브\s*)?재조회(\s*결과)?\s*[:,]?\s*/, "");
        if (!t) continue;
        const recital = /평균단가|평단/.test(t) && /현재가/.test(t);
        if (recital) { if (!fallback) fallback = t; continue; }
        return t.length > 160 ? `${t.slice(0, 160)}…` : t;
      }
      return fallback.length > 160 ? `${fallback.slice(0, 160)}…` : fallback;
    }

    function decisionRowHtml(row) {
      const isDeleg = row.kind === "delegation";
      const target = row.stock_code
        ? escapeHtml(row.stock_name || row.stock_code)
        : `<span class="agent-muted">포트폴리오 전체</span>`;
      const actionPill = row.final_action
        ? `<span class="agent-pill agent-pill--${actionPillClass(row.final_action)}">${escapeHtml(row.final_action)}</span>`
        : row.kind === "tier1"
          ? `<span class="agent-pill agent-pill--tier1">코드 실행</span>`
          : `<span class="agent-pill agent-pill--warn">ACTION 없음</span>`;
      const tierTag = isDeleg ? "" : `<span class="agent-muted">T${escapeHtml(String(row.tier))}</span> `;

      // An agent can answer the same dispatch across several runs; the last one
      // carrying an ACTION is what the watcher applied. Earlier ones are working
      // notes and belong below it.
      const responses = row.responses || [];
      const withAction = responses.filter((r) => r.action);
      const answer = withAction.length
        ? withAction[withAction.length - 1]
        : (responses.length ? responses[responses.length - 1] : null);
      const priorRuns = responses.filter((r) => r !== answer);

      const gist = row.kind === "tier1"
        ? (row.reason || "코드가 즉시 실행")
        : answer ? gistOf(answer.text) : "응답 없음";

      const reasoning = row.kind === "tier1"
        ? `<div class="agent-muted">Tier 1 — 코드가 즉시 실행. 에이전트 판단 없음.</div>`
        : answer ? mdLite(answer.text)
        : `<div class="agent-muted">에이전트 응답이 기록되지 않았습니다.</div>`;

      const priorHtml = priorRuns.length
        ? `<div class="agent-tl-deleg">${priorRuns.map((d) => `
             <div><span class="agent-muted">이전 런 ${d.action ? escapeHtml(d.action) : "(ACTION 없음)"} · </span>
             <span class="agent-muted">${escapeHtml(stripActionTag(d.text).slice(0, 200))}</span></div>`).join("")}</div>`
        : "";

      const issue = row.issue || {};
      const raw = `
        ${row.snapshot ? `<div class="agent-subhead">트리거 스냅샷</div><pre class="agent-pre">${escapeHtml(JSON.stringify(row.snapshot, null, 2))}</pre>` : ""}
        ${row.snapshot_raw ? `<div class="agent-subhead">스냅샷 (파싱 실패, 원문)</div><pre class="agent-pre">${escapeHtml(row.snapshot_raw)}</pre>` : ""}
        ${responses.map((r, i) => `
          <div class="agent-subhead">응답 ${i + 1}/${responses.length} · ${escapeHtml(r.action || "ACTION 없음")} · ${fmtKstShort(r.created_at)}</div>
          <pre class="agent-pre">${escapeHtml(r.text)}</pre>`).join("")}
        ${issue.identifier ? `<div class="agent-muted">이슈 ${escapeHtml(issue.identifier)} · ${escapeHtml(issue.title || "")} · ${escapeHtml(issue.status || "")}</div>` : ""}`;
      const hasRaw = row.snapshot || row.snapshot_raw || responses.length;
      const outcome = outcomeBadgeHtml(row);

      return `
        <details class="ag-dec-wrap">
          <summary class="ag-dec">
            <span class="time">${escapeHtml(String(row.dispatched_at || "").slice(11, 16))}</span>
            <span class="what">${tierTag}${escapeHtml(triggerLabel(row.trigger_type))}</span>
            <span class="who">${target}</span>
            <span>${actionPill}</span>
            <span class="gist">${escapeHtml(gist)}</span>
            <span class="chev">›</span>
          </summary>
          <div class="ag-dec-body">
            ${row.reason ? `<div class="agent-tl-why"><strong>트리거</strong> · ${escapeHtml(row.reason)}</div>` : ""}
            ${snapshotChips(row.snapshot) ? `<div class="agent-chips">${snapshotChips(row.snapshot)}</div>` : ""}
            ${reasoning}
            ${priorHtml}
            ${outcome ? `<div class="agent-tl-outcome">${outcome}</div>` : ""}
            ${hasRaw ? `<details class="agent-tl-more"><summary>원문 · 스냅샷 보기</summary>${raw}</details>` : ""}
          </div>
        </details>`;
    }

    function renderAgentTimeline(payload) {
      if (!payload) {
        agentTimelineRoot.innerHTML = '<div class="empty-state">판단 기록을 불러오지 못했습니다.</div>';
        return;
      }
      const rows = Array.isArray(payload.rows) ? payload.rows : [];
      const src = payload.source || {};
      const banners = [];
      if (src.multica === "disabled" || src.multica === "error") {
        banners.push(`<div class="agent-error">Multica 조회 실패 — 판단 근거를 읽을 수 없습니다. ${escapeHtml(src.note || "")}</div>`);
      } else if (src.multica === "partial") {
        banners.push(`<div class="agent-error">${escapeHtml(src.note || "부분 결과")}</div>`);
      }
      const joinUnavailable = src.outcome_join === "unavailable";
      if (joinUnavailable) {
        banners.push(`<div class="agent-notice-soft">${escapeHtml(src.note || "watcher 기록이 없어 주문 결과를 대사할 수 없습니다.")} 판단 내용은 그대로 표시됩니다.</div>`);
      }

      // What the day came to, before any individual row: most days are a
      // column of HOLDs, and that fact should take one glance, not a scroll.
      const byAction = {};
      const byTrigger = {};
      let orders = 0;
      rows.forEach((r) => {
        const a = r.final_action || (r.kind === "tier1" ? "코드 실행" : "ACTION 없음");
        byAction[a] = (byAction[a] || 0) + 1;
        const t = triggerLabel(r.trigger_type);
        byTrigger[t] = (byTrigger[t] || 0) + 1;
        const o = r.outcome && r.outcome.outcome;
        if (o === "submitted" || o === "filled" || o === "unknown") orders += 1;
      });
      const actionChips = Object.entries(byAction)
        .sort((x, y) => y[1] - x[1])
        .map(([a, cnt]) => `<span class="agent-pill agent-pill--${actionPillClass(a)}">${escapeHtml(a)} ${cnt}</span>`)
        .join("");
      const triggerChips = Object.entries(byTrigger)
        .sort((x, y) => y[1] - x[1])
        .map(([t, cnt]) => `<span class="agent-chip">${escapeHtml(t)} <strong>${cnt}</strong></span>`)
        .join("");
      const orderChip = joinUnavailable
        ? `<span class="agent-chip">주문 연결 <strong>대사 불가</strong></span>`
        : `<span class="agent-chip">주문으로 이어짐 <strong>${orders}</strong></span>`;
      const tally = rows.length
        ? `<div class="ag-tally">${actionChips}<span class="sep"></span>${triggerChips}<span class="sep"></span>${orderChip}</div>`
        : "";

      const today = kstDate(new Date().toISOString());
      const dayNote = payload.date && payload.date !== today ? " · 오늘 아님" : "";
      const body = rows.length
        ? `<div class="ag-decs">${rows.map(decisionRowHtml).join("")}</div>`
        : `<div class="ag-empty">${escapeHtml(payload.date || "")}에 기록된 에이전트 판단이 없습니다.</div>`;

      agentTimelineRoot.innerHTML = `
        <div class="agent-card agent-card--full">
          <div class="agent-card-head">
            <strong>${escapeHtml(payload.date || "")} 판단 ${rows.length}건</strong>
            <span class="agent-muted">최신순 · 행을 눌러 근거 보기${escapeHtml(dayNote)}</span>
          </div>
          ${banners.join("")}
          ${tally}
          ${body}
        </div>`;
    }

    function outcomeColor(outcome) {
      if (!outcome) return "";
      // "submitted" = broker accepted the request; "filled" = execution
      // confirmed against the account. They are never the same thing.
      if (outcome === "filled" || outcome === "submitted") return "ok";
      if (outcome === "informational" || outcome === "skipped") return "info";
      // "cancelled" = the watcher shut down mid-decision. Nothing went wrong,
      // but the decision never landed either.
      if (outcome === "dry_run" || outcome === "stale" || outcome === "cancelled") return "warn";
      // "unknown" = the request went out and the answer was lost, so an order
      // may exist that nobody is tracking. Louder than a clean failure.
      if (outcome === "timeout" || outcome === "failed"
          || outcome === "dispatch_failed" || outcome === "unknown") return "err";
      return "";
    }

    async function loadAgentOverview() {
      try {
        const response = await fetch("/api/agent_overview");
        if (!response.ok) {
          throw new Error(`agent_overview HTTP ${response.status}`);
        }
        const payload = await response.json();
        renderAgentOverview(payload);
      } catch (error) {
        agentStripRoot.innerHTML = `<div class="error-banner">${escapeHtml(error.message || String(error))}</div>`;
      }
    }

    let timelineLoading = false;
    async function loadAgentTimeline() {
      // The timeline fans out to the Multica CLI, so overlapping calls would
      // stack subprocesses. One at a time is plenty for a 30s refresh.
      if (timelineLoading) return;
      timelineLoading = true;
      try {
        const date = agentDateInput && agentDateInput.value ? agentDateInput.value : "";
        const url = date ? `/api/agent_timeline?date=${encodeURIComponent(date)}` : "/api/agent_timeline";
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`agent_timeline HTTP ${response.status}`);
        }
        renderAgentTimeline(await response.json());
      } catch (error) {
        agentTimelineRoot.innerHTML = `<div class="error-banner">${escapeHtml(error.message || String(error))}</div>`;
      } finally {
        timelineLoading = false;
      }
    }

    if (agentDateInput) {
      // Typing into <input type="date"> fires `change` on every intermediate
      // state — entering the year digit by digit briefly yields 0002-08-13,
      // which is a *valid* date and would otherwise trigger a real fetch.
      // Debounce, and ignore years that cannot be a trading day here.
      let dateDebounce = null;
      agentDateInput.addEventListener("change", () => {
        clearTimeout(dateDebounce);
        dateDebounce = setTimeout(() => {
          const value = agentDateInput.value;
          if (value && Number(value.slice(0, 4)) < 2000) return;
          loadAgentTimeline();
        }, 500);
      });
    }
    if (agentReloadBtn) {
      agentReloadBtn.addEventListener("click", () => loadAgentTimeline());
    }

    // -- Tab navigation -------------------------------------------------
    const tabLinks = Array.from(document.querySelectorAll(".tab-link"));
    const views = {
      main: document.getElementById("view-main"),
      agents: document.getElementById("view-agents"),
    };

    let agentTabSeen = false;
    function activateView(name) {
      const target = views[name] ? name : "main";
      Object.entries(views).forEach(([key, el]) => {
        if (el) el.classList.toggle("active", key === target);
      });
      tabLinks.forEach((link) => {
        link.classList.toggle("active", link.dataset.view === target);
      });
      // Load the agent data the first time the tab is actually opened. The
      // timeline spawns Multica CLI subprocesses server-side, so it must not run
      // for users who never leave the trading tab.
      if (target === "agents" && !agentTabSeen) {
        agentTabSeen = true;
        loadAgentOverview().then(() => {
          defaultTimelineDate();
          loadAgentTimeline();
        });
      }
    }

    function viewFromHash() {
      const raw = (window.location.hash || "").replace(/^#/, "");
      return views[raw] ? raw : "main";
    }

    tabLinks.forEach((link) => {
      link.addEventListener("click", (event) => {
        event.preventDefault();
        const target = link.dataset.view;
        if (window.location.hash !== `#${target}`) {
          window.location.hash = target;
        } else {
          activateView(target);
        }
      });
    });

    window.addEventListener("hashchange", () => activateView(viewFromHash()));
    activateView(viewFromHash());

    loadDashboard();
    // Auto-refresh the agent panel only while its tab is actually on screen —
    // the old version polled regardless of which tab was open, spawning Multica
    // subprocesses for users sitting on the trading tab.
    setInterval(() => {
      if (document.hidden) return;
      if (!views.agents || !views.agents.classList.contains("active")) return;
      loadAgentOverview();
      loadAgentTimeline();
    }, 30000);
  </script>
</body>
</html>
"""


__all__ = ["DASHBOARD_HTML"]
