import { useEffect, useState } from "react";
import api from "../services/api";

function Compliance({ bidSubmissionId = 18, setCurrentPage }) {
  const [assessment, setAssessment] = useState(null);

  const [loading, setLoading] = useState(true);
  const [assessing, setAssessing] = useState(false);
  const [recommending, setRecommending] = useState(false);

  const [error, setError] = useState("");

  useEffect(() => {
    runAssessment();
  }, [bidSubmissionId]);

  async function runAssessment() {
    setLoading(true);
    setError("");

    try {
      const response = await api.post(
        `/compliance/assess/${bidSubmissionId}`
      );

      setAssessment(response.data);
    } catch (err) {
      console.error(
        "Failed to assess compliance:",
        err
      );

      setError(
        err.response?.data?.detail ||
          "Failed to generate compliance assessment."
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleReassess() {
    setAssessing(true);
    setError("");

    try {
      const response = await api.post(
        `/compliance/assess/${bidSubmissionId}`
      );

      setAssessment(response.data);
    } catch (err) {
      console.error(
        "Failed to reassess compliance:",
        err
      );

      setError(
        err.response?.data?.detail ||
          "Failed to generate compliance assessment."
      );
    } finally {
      setAssessing(false);
    }
  }

  async function handleRecommendation() {
    setRecommending(true);
    setError("");

    try {
      const response = await api.post(
        `/compliance/recommend/${bidSubmissionId}`
      );

      setAssessment(response.data);
    } catch (err) {
      console.error(
        "Failed to generate recommendation:",
        err
      );

      setError(
        err.response?.data?.detail ||
          "Failed to generate recommendation."
      );
    } finally {
      setRecommending(false);
    }
  }

  function getRiskClass(riskLevel) {
    if (!riskLevel) {
      return "unknown";
    }

    const risk = riskLevel.toLowerCase();

    if (risk.includes("low")) {
      return "low";
    }

    if (
      risk.includes("medium") ||
      risk.includes("moderate")
    ) {
      return "medium";
    }

    if (
      risk.includes("high") ||
      risk.includes("critical")
    ) {
      return "high";
    }

    return "unknown";
  }

  function getScoreClass(score) {
    if (score === null || score === undefined) {
      return "unknown";
    }

    if (score >= 80) {
      return "good";
    }

    if (score >= 60) {
      return "warning";
    }

    return "danger";
  }

  function formatStatus(status) {
    if (!status) {
      return "UNKNOWN";
    }

    return status.replaceAll("_", " ");
  }

  function formatDate(date) {
    if (!date) {
      return "Not available";
    }

    return new Date(date).toLocaleString();
  }

  if (loading) {
    return (
      <main className="page">
        <div className="page-header">
          <div>
            <h2>Compliance Assessment</h2>
            <p>
              Analyzing bid submission #
              {bidSubmissionId}
            </p>
          </div>
        </div>

        <section className="empty-state">
          <h3>Generating assessment...</h3>

          <p>
            The system is evaluating the submitted bid
            against the available compliance information.
          </p>
        </section>
      </main>
    );
  }

  return (
    <main className="page">
      <div className="page-header">
        <div>
          <h2>Compliance Assessment</h2>

          <p>
            AI-assisted compliance assessment for bid
            submission #{bidSubmissionId}
          </p>
        </div>

        <div className="page-actions">
          {setCurrentPage && (
            <button
              className="secondary-button"
              onClick={() =>
                setCurrentPage("submission")
              }
            >
              Back to Submission
            </button>
          )}

          <button
            className="secondary-button"
            onClick={handleRecommendation}
            disabled={
              recommending || !assessment
            }
          >
            {recommending
              ? "Generating..."
              : "Generate Recommendation"}
          </button>

          <button
            className="primary-button"
            onClick={handleReassess}
            disabled={assessing}
          >
            {assessing
              ? "Assessing..."
              : "Reassess"}
          </button>
        </div>
      </div>

      {error && (
        <section className="error-state">
          <h3>Compliance Error</h3>

          <p>{error}</p>

          <button
            className="primary-button"
            onClick={runAssessment}
          >
            Try Again
          </button>
        </section>
      )}

      {assessment && (
        <>
          <section className="compliance-overview">
            <div className="compliance-score-card">
              <span className="card-label">
                Compliance Score
              </span>

              <div
                className={`compliance-score ${getScoreClass(
                  assessment.score
                )}`}
              >
                {assessment.score !== null &&
                assessment.score !== undefined
                  ? assessment.score.toFixed(1)
                  : "—"}
              </div>

              <span className="score-label">
                out of 100
              </span>
            </div>

            <div className="compliance-info-card">
              <span className="card-label">
                Risk Level
              </span>

              <span
                className={`risk-badge ${getRiskClass(
                  assessment.risk_level
                )}`}
              >
                {assessment.risk_level ||
                  "Not available"}
              </span>
            </div>

            <div className="compliance-info-card">
              <span className="card-label">
                Assessment Status
              </span>

              <span className="assessment-status">
                {formatStatus(assessment.status)}
              </span>
            </div>

            <div className="compliance-info-card">
              <span className="card-label">
                Assessed At
              </span>

              <span className="assessment-date">
                {formatDate(
                  assessment.assessed_at
                )}
              </span>
            </div>
          </section>

          <section className="compliance-section">
            <div className="section-heading">
              <h3>Assessment Summary</h3>
            </div>

            <div className="summary-box">
              {assessment.summary ||
                "No assessment summary available."}
            </div>
          </section>

          <section className="compliance-section">
            <div className="section-heading">
              <h3>AI Recommendation</h3>
            </div>

            <div className="recommendation-box">
              {assessment.recommendation ||
                "No recommendation generated yet."}
            </div>

            {!assessment.recommendation && (
              <button
                className="primary-button recommendation-button"
                onClick={handleRecommendation}
                disabled={recommending}
              >
                {recommending
                  ? "Generating Recommendation..."
                  : "Generate Recommendation"}
              </button>
            )}

            <p className="ai-disclaimer">
              This recommendation is AI-assisted and
              should support, not replace, the
              Procurement Officer's final decision.
            </p>
          </section>

          {assessment.assessment_metadata &&
            Object.keys(
              assessment.assessment_metadata
            ).length > 0 && (
              <section className="compliance-section">
                <div className="section-heading">
                  <h3>Assessment Details</h3>
                </div>

                <div className="metadata-grid">
                  {Object.entries(
                    assessment.assessment_metadata
                  ).map(([key, value]) => (
                    <div
                      className="metadata-item"
                      key={key}
                    >
                      <span className="metadata-key">
                        {key.replaceAll("_", " ")}
                      </span>

                      <span className="metadata-value">
                        {typeof value === "object"
                          ? JSON.stringify(value)
                          : String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              </section>
            )}

          <section className="officer-decision">
            <div>
              <h3>
                Procurement Officer Decision
              </h3>

              <p>
                The final qualification or
                disqualification decision remains with
                the Procurement Officer.
              </p>
            </div>

            <span className="decision-status">
              Pending Officer Review
            </span>
          </section>
        </>
      )}
    </main>
  );
}

export default Compliance;