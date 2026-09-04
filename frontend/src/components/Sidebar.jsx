const NAV_ITEMS = [
  { id: "overview", label: "Overview", icon: IconGrid },
  { id: "transactions", label: "Transactions", icon: IconList },
  { id: "queue", label: "Recovery Queue", icon: IconInbox },
  { id: "analytics", label: "Analytics", icon: IconBarChart },
  { id: "guardrails", label: "Guardrails", icon: IconShield },
  { id: "audit", label: "Audit Logs", icon: IconClock },
  { id: "settings", label: "Settings", icon: IconGear },
];

export default function Sidebar({ active, onNavigate }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <span className="brand-mark" aria-hidden="true">
          <IconMark />
        </span>
        <span className="brand-name">Revenue Recovery</span>
      </div>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = active === item.id;
          return (
            <button
              key={item.id}
              className={`nav-item ${isActive ? "nav-item--active" : ""}`}
              onClick={() => onNavigate(item.id)}
            >
              <Icon />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <span className="sidebar-footer-mark">
          <IconMark small />
        </span>
        <span className="sidebar-footer-text">AI Revenue Recovery Agent</span>
      </div>
    </aside>
  );
}

/* ---- Minimal inline icon set (no external icon library dependency) ---- */

function IconMark({ small }) {
  const size = small ? 16 : 20;
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
      <path
        d="M4 13.5L13 3l-2.4 8.2H20L11 22l2.3-8.5H4z"
        fill="currentColor"
      />
    </svg>
  );
}

function IconGrid() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <rect x="1.5" y="1.5" width="5.5" height="5.5" rx="1.2" stroke="currentColor" strokeWidth="1.3" />
      <rect x="9" y="1.5" width="5.5" height="5.5" rx="1.2" stroke="currentColor" strokeWidth="1.3" />
      <rect x="1.5" y="9" width="5.5" height="5.5" rx="1.2" stroke="currentColor" strokeWidth="1.3" />
      <rect x="9" y="9" width="5.5" height="5.5" rx="1.2" stroke="currentColor" strokeWidth="1.3" />
    </svg>
  );
}

function IconList() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <rect x="1.5" y="2.5" width="13" height="2.6" rx="0.8" fill="currentColor" />
      <rect x="1.5" y="6.7" width="13" height="2.6" rx="0.8" fill="currentColor" />
      <rect x="1.5" y="10.9" width="8" height="2.6" rx="0.8" fill="currentColor" />
    </svg>
  );
}

function IconInbox() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path
        d="M2 9.5L3.8 3h8.4L14 9.5v3a1 1 0 01-1 1H3a1 1 0 01-1-1v-3z"
        stroke="currentColor"
        strokeWidth="1.3"
        strokeLinejoin="round"
      />
      <path d="M2 9.5h3.2l.9 1.6h3.8l.9-1.6H14" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" />
    </svg>
  );
}

function IconBarChart() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <rect x="2" y="8" width="3" height="6" rx="0.7" fill="currentColor" />
      <rect x="6.5" y="4.5" width="3" height="9.5" rx="0.7" fill="currentColor" />
      <rect x="11" y="1.5" width="3" height="12.5" rx="0.7" fill="currentColor" />
    </svg>
  );
}

function IconShield() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path
        d="M8 1.5l5.5 2v3.7c0 3.7-2.4 6.3-5.5 7.3-3.1-1-5.5-3.6-5.5-7.3V3.5L8 1.5z"
        stroke="currentColor"
        strokeWidth="1.3"
        strokeLinejoin="round"
      />
      <path d="M5.6 8.1l1.7 1.7 3.1-3.4" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function IconClock() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <circle cx="8" cy="8" r="6.3" stroke="currentColor" strokeWidth="1.3" />
      <path d="M8 4.7V8l2.4 1.4" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function IconGear() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <circle cx="8" cy="8" r="2.3" stroke="currentColor" strokeWidth="1.3" />
      <path
        d="M8 1.8v1.6M8 12.6v1.6M14.2 8h-1.6M3.4 8H1.8M12.4 3.6l-1.1 1.1M4.7 11.3l-1.1 1.1M12.4 12.4l-1.1-1.1M4.7 4.7L3.6 3.6"
        stroke="currentColor"
        strokeWidth="1.3"
        strokeLinecap="round"
      />
    </svg>
  );
}
