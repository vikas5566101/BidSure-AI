import { useEffect, useState } from "react";

import api from "../services/api";

function BidSubmission({
  setCurrentPage,
  openSubmissionDocuments,
}) {
  const [submission, setSubmission] = useState(null);
  const [tender, setTender] = useState(null);
  const [bidder, setBidder] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const bidSubmissionId = 18;

  useEffect(() => {
    loadSubmission();
  }, []);

  async function loadSubmission() {
    try {
      setLoading(true);
      setError("");

      const submissionResponse = await api.get(
        `/bid-submissions/${bidSubmissionId}`
      );

      const submissionData = submissionResponse.data;

      setSubmission(submissionData);

      const [tenderResponse, bidderResponse] =
        await Promise.all([
          api.get(
            `/tenders/${submissionData.tender_id}`
          ),
          api.get(
            `/bidders/${submissionData.bidder_id}`
          ),
        ]);

      setTender(tenderResponse.data);
      setBidder(bidderResponse.data);
    } catch (err) {
      console.error(
        "Failed to load bid submission:",
        err
      );

      setError(
        err.response?.data?.detail ||
          "Failed to load bid submission."
      );
    } finally {
      setLoading(false);
    }
  }

  function formatDate(dateString) {
    if (!dateString) {
      return "—";
    }

    return new Date(dateString).toLocaleString();
  }

  function formatStatus(status) {
    if (!status) {
      return "UNKNOWN";
    }

    return status.replaceAll("_", " ");
  }

  function getStatusClass(status) {
    const normalizedStatus = status?.toUpperCase();

    if (
      normalizedStatus === "SUBMITTED" ||
      normalizedStatus === "UNDER_REVIEW"
    ) {
      return "tag success";
    }

    if (
      normalizedStatus === "REJECTED" ||
      normalizedStatus === "DISQUALIFIED"
    ) {
      return "tag error";
    }

    return "tag warning";
  }

  function openCompliance() {
    setCurrentPage("compliance");
  }

  if (loading) {
    return (
      <main className="page">
        <div className="panel loading-panel">
          Loading bid submission...
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="page">
        <div className="panel error-panel">
          {error}
        </div>
      </main>
    );
  }

  return (
    <main className="page">
      <div className="page-header">
        <div>
          <p className="header-label">
            CPCL • GeM Procurement
          </p>

          <h2>Bid Submission #{submission.id}</h2>

          <p>
            Bidder submission and procurement details.
          </p>
        </div>

        <div className="submission-header-actions">
          <span
            className={getStatusClass(
              submission.status
            )}
          >
            {formatStatus(submission.status)}
          </span>

          <button
            className="secondary-button"
            onClick={openCompliance}
          >
            Compliance Assessment
          </button>

          <button
            className="primary-button"
            onClick={() =>
              openSubmissionDocuments(
                submission.id
              )
            }
          >
            View Documents
          </button>
        </div>
      </div>

      <section className="submission-grid">
        <div className="panel">
          <div className="panel-header">
            <h3>Bidder Information</h3>
          </div>

          {bidder && (
            <div className="info-list">
              <div className="info-row">
                <span>Company Name</span>
                <strong>{bidder.company_name}</strong>
              </div>

              <div className="info-row">
                <span>GSTIN</span>
                <strong>{bidder.gstin || "—"}</strong>
              </div>

              <div className="info-row">
                <span>PAN</span>
                <strong>{bidder.pan || "—"}</strong>
              </div>

              <div className="info-row">
                <span>Udyam Number</span>
                <strong>
                  {bidder.udyam_number || "—"}
                </strong>
              </div>

              <div className="info-row">
                <span>Email</span>
                <strong>
                  {bidder.contact_email || "—"}
                </strong>
              </div>

              <div className="info-row">
                <span>Phone</span>
                <strong>
                  {bidder.contact_phone || "—"}
                </strong>
              </div>
            </div>
          )}
        </div>

        <div className="panel">
          <div className="panel-header">
            <h3>Tender Information</h3>
          </div>

          {tender && (
            <div className="info-list">
              <div className="info-row">
                <span>Reference Number</span>
                <strong>
                  {tender.reference_number}
                </strong>
              </div>

              <div className="info-row">
                <span>Title</span>
                <strong>{tender.title}</strong>
              </div>

              <div className="info-row">
                <span>Status</span>
                <strong>
                  {formatStatus(tender.status)}
                </strong>
              </div>

              <div className="info-row">
                <span>Description</span>
                <strong>
                  {tender.description || "—"}
                </strong>
              </div>
            </div>
          )}
        </div>
      </section>

      <section className="panel submission-information">
        <div className="panel-header">
          <h3>Submission Information</h3>
        </div>

        <div className="submission-meta-grid">
          <div className="info-row">
            <span>Submission ID</span>
            <strong>{submission.id}</strong>
          </div>

          <div className="info-row">
            <span>Tender ID</span>
            <strong>{submission.tender_id}</strong>
          </div>

          <div className="info-row">
            <span>Bidder ID</span>
            <strong>{submission.bidder_id}</strong>
          </div>

          <div className="info-row">
            <span>Status</span>
            <strong>
              {formatStatus(submission.status)}
            </strong>
          </div>

          <div className="info-row">
            <span>Submitted At</span>
            <strong>
              {formatDate(submission.submitted_at)}
            </strong>
          </div>

          <div className="info-row">
            <span>Created At</span>
            <strong>
              {formatDate(submission.created_at)}
            </strong>
          </div>
        </div>
      </section>
    </main>
  );
}

export default BidSubmission;