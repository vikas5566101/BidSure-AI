import { useEffect, useState } from "react";

import api from "../services/api";

import BidSummary from "../components/BidSummary";
import StatCard from "../components/StatCard";
import DocumentStatus from "../components/DocumentStatus";
import AIRecommendation from "../components/AIRecommendation";

function Dashboard() {
  const [submission, setSubmission] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const bidSubmissionId = 18;

  useEffect(() => {
    loadDashboard();
  }, []);

  async function loadDashboard() {
    try {
      setLoading(true);
      setError("");

      const [
        submissionResponse,
        documentsResponse,
      ] = await Promise.all([
        api.get(`/bid-submissions/${bidSubmissionId}`),
        api.get(
          `/bid-submissions/${bidSubmissionId}/documents`
        ),
      ]);

      setSubmission(submissionResponse.data);
      setDocuments(documentsResponse.data);
    } catch (err) {
      console.error(
        "Failed to load dashboard:",
        err
      );

      setError(
        err.response?.data?.detail ||
          "Failed to load dashboard data."
      );
    } finally {
      setLoading(false);
    }
  }

  const totalDocuments = documents.length;

  const processedDocuments = documents.filter(
    (document) =>
      document.status === "COMPLETED"
  ).length;

  const notProcessedDocuments =
    totalDocuments - processedDocuments;

  if (loading) {
    return (
      <main className="dashboard">
        <div className="panel loading-panel">
          Loading dashboard...
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="dashboard">
        <div className="panel error-panel">
          {error}
        </div>
      </main>
    );
  }

  return (
    <main className="dashboard">
      <div className="page-header">
        <div>
          <p className="header-label">
            CPCL • GeM Procurement
          </p>

          <h2>Dashboard</h2>

          <p>
            Overview of the current bid submission,
            submitted documents, and compliance workflow.
          </p>
        </div>
      </div>

      <BidSummary submission={submission} />

      <section className="stats-grid">
        <StatCard
          label="Total Documents"
          value={totalDocuments}
        />

        <StatCard
          label="Processed"
          value={processedDocuments}
        />

        <StatCard
          label="Not Processed"
          value={notProcessedDocuments}
        />

        <StatCard
          label="Compliance Score"
          value="—"
        />
      </section>

      <section className="dashboard-grid">
        <DocumentStatus documents={documents} />

        <AIRecommendation />
      </section>
    </main>
  );
}

export default Dashboard;