export default function Header({ health, viewTitle, viewSubtitle }) {
  return (
    <header className="topheader">
      <div>
        <h1 className="topheader-title">{viewTitle}</h1>
        <p className="topheader-subtitle">{viewSubtitle}</p>
      </div>
      <div className="topheader-right">
        <span className="conn-indicator">
          <span className={`status-dot ${health ? "status-dot--ok" : "status-dot--down"}`} />
          {health ? "Backend connected" : "Backend unreachable"}
        </span>
        <span className="mode-pill">Test Mode</span>
      </div>
    </header>
  );
}
