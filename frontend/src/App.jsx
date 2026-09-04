import { useState } from "react";

import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import Dashboard from "./pages/Dashboard";
import Documents from "./pages/Documents";
import Tenders from "./pages/Tenders";
import BidSubmission from "./pages/BidSubmission";
import Compliance from "./pages/Compliance";

function App() {
  const [currentPage, setCurrentPage] = useState("dashboard");
  const [selectedSubmissionId, setSelectedSubmissionId] =
    useState(18);

  function openSubmissionDocuments(submissionId) {
    setSelectedSubmissionId(submissionId);
    setCurrentPage("documents");
  }

  return (
    <div className="app">
      <Sidebar
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
      />

      <div className="main-content">
        <Header />

        {currentPage === "dashboard" && <Dashboard />}

        {currentPage === "tenders" && <Tenders />}

        {currentPage === "submission" && (
          <BidSubmission
            setCurrentPage={setCurrentPage}
            openSubmissionDocuments={
              openSubmissionDocuments
            }
          />
        )}

        {currentPage === "documents" && (
          <Documents
            bidSubmissionId={selectedSubmissionId}
            setCurrentPage={setCurrentPage}
          />
        )}

        {currentPage === "compliance" && (
          <Compliance
            bidSubmissionId={selectedSubmissionId}
            setCurrentPage={setCurrentPage}
          />
        )}
      </div>
    </div>
  );
}

export default App;