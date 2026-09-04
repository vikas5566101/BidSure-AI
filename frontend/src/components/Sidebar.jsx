function Sidebar({ currentPage, setCurrentPage }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-logo">B</div>

        <div>
          <h1>BidSure AI</h1>
          <p>Procurement Compliance</p>
        </div>
      </div>

      <nav className="navigation">
        <button
          className={`nav-item ${
            currentPage === "dashboard" ? "active" : ""
          }`}
          onClick={() => setCurrentPage("dashboard")}
        >
          Dashboard
        </button>

        <button
          className={`nav-item ${
            currentPage === "tenders" ? "active" : ""
          }`}
          onClick={() => setCurrentPage("tenders")}
        >
          Tenders
        </button>

        <button
          className={`nav-item ${
            currentPage === "submission" ? "active" : ""
          }`}
          onClick={() => setCurrentPage("submission")}
        >
          Bid Submission
        </button>

        <button
          className={`nav-item ${
            currentPage === "documents" ? "active" : ""
          }`}
          onClick={() => setCurrentPage("documents")}
        >
          Documents
        </button>

        <button
          className={`nav-item ${
            currentPage === "compliance" ? "active" : ""
          }`}
          onClick={() => setCurrentPage("compliance")}
        >
          Compliance
        </button>
      </nav>

      <div className="sidebar-footer">
        <strong>CPCL</strong>
        <span>GeM Procurement</span>
      </div>
    </aside>
  );
}

export default Sidebar;