import { useEffect, useState } from "react";

import api from "../services/api";

function Tenders() {
  const [tenders, setTenders] = useState([]);
  const [selectedTender, setSelectedTender] = useState(null);
  const [requirements, setRequirements] = useState([]);

  const [loading, setLoading] = useState(true);
  const [requirementsLoading, setRequirementsLoading] =
    useState(false);

  const [error, setError] = useState("");
  const [requirementsError, setRequirementsError] =
    useState("");

  useEffect(() => {
    loadTenders();
  }, []);

  async function loadTenders() {
    try {
      setLoading(true);
      setError("");

      const response = await api.get("/tenders");

      setTenders(response.data);
    } catch (err) {
      console.error("Failed to load tenders:", err);

      setError(
        err.response?.data?.detail ||
          "Failed to load tenders."
      );
    } finally {
      setLoading(false);
    }
  }

  async function loadRequirements(tender) {
    try {
      setSelectedTender(tender);
      setRequirementsLoading(true);
      setRequirementsError("");
      setRequirements([]);

      const response = await api.get(
        `/tenders/${tender.id}/requirements`
      );

      setRequirements(response.data);
    } catch (err) {
      console.error(
        "Failed to load tender requirements:",
        err
      );

      setRequirementsError(
        err.response?.data?.detail ||
          "Failed to load tender requirements."
      );
    } finally {
      setRequirementsLoading(false);
    }
  }

  function formatDate(dateString) {
    if (!dateString) {
      return "—";
    }

    return new Date(dateString).toLocaleDateString();
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
      normalizedStatus === "OPEN" ||
      normalizedStatus === "ACTIVE"
    ) {
      return "tag success";
    }

    if (
      normalizedStatus === "CLOSED" ||
      normalizedStatus === "COMPLETED"
    ) {
      return "tag";
    }

    return "tag warning";
  }

  if (loading) {
    return (
      <main className="page">
        <div className="panel loading-panel">
          Loading tenders...
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

  if (selectedTender) {
    return (
      <main className="page">
        <button
          className="back-button"
          onClick={() => {
            setSelectedTender(null);
            setRequirements([]);
            setRequirementsError("");
          }}
        >
          ← Back to Tenders
        </button>

        <section className="tender-detail-header">
          <div>
            <div className="tender-reference">
              {selectedTender.reference_number}
            </div>

            <h2>{selectedTender.title}</h2>

            <p>
              {selectedTender.description ||
                "No description available."}
            </p>
          </div>

          <span
            className={getStatusClass(
              selectedTender.status
            )}
          >
            {formatStatus(selectedTender.status)}
          </span>
        </section>

        <section className="requirements-section">
          <div className="section-header">
            <div>
              <h3>Tender Requirements</h3>

              <p>
                Requirements that must be checked during
                bidder compliance verification.
              </p>
            </div>

            <span className="page-count">
              {requirements.length}{" "}
              {requirements.length === 1
                ? "Requirement"
                : "Requirements"}
            </span>
          </div>

          {requirementsLoading && (
            <div className="panel loading-panel">
              Loading requirements...
            </div>
          )}

          {requirementsError && (
            <div className="panel error-panel">
              {requirementsError}
            </div>
          )}

          {!requirementsLoading &&
            !requirementsError &&
            requirements.length === 0 && (
              <div className="panel empty-state">
                No requirements have been added for this
                tender yet.
              </div>
            )}

          {!requirementsLoading &&
            !requirementsError &&
            requirements.length > 0 && (
              <div className="requirements-list">
                {requirements.map((requirement) => (
                  <article
                    className="requirement-card"
                    key={requirement.id}
                  >
                    <div className="requirement-main">
                      <div className="requirement-top">
                        <span className="requirement-type">
                          {requirement.requirement_type}
                        </span>

                        <span
                          className={
                            requirement.is_required
                              ? "tag warning"
                              : "tag"
                          }
                        >
                          {requirement.is_required
                            ? "Required"
                            : "Optional"}
                        </span>
                      </div>

                      <h4>
                        {requirement.requirement_name}
                      </h4>

                      <p>
                        {requirement.description ||
                          "No description available."}
                      </p>
                    </div>

                    <div className="requirement-meta">
                      {requirement.source_document && (
                        <div>
                          <span>Source Document</span>

                          <strong>
                            {requirement.source_document}
                          </strong>
                        </div>
                      )}

                      {requirement.validation_config && (
                        <div>
                          <span>
                            Validation Configuration
                          </span>

                          <strong>
                            {requirement.validation_config}
                          </strong>
                        </div>
                      )}

                      {requirement.source_chunk_ids &&
                        requirement.source_chunk_ids.length >
                          0 && (
                          <div>
                            <span>Source Chunks</span>

                            <strong>
                              {
                                requirement
                                  .source_chunk_ids.length
                              }
                            </strong>
                          </div>
                        )}

                      <div>
                        <span>Created</span>

                        <strong>
                          {formatDate(
                            requirement.created_at
                          )}
                        </strong>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            )}
        </section>
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

          <h2>Tenders</h2>

          <p>
            View procurement tenders and their compliance
            requirements.
          </p>
        </div>

        <div className="page-count">
          {tenders.length}{" "}
          {tenders.length === 1 ? "Tender" : "Tenders"}
        </div>
      </div>

      {tenders.length === 0 ? (
        <div className="panel empty-state">
          No tenders found.
        </div>
      ) : (
        <section className="tenders-list">
          {tenders.map((tender) => (
            <button
              className="tender-card"
              key={tender.id}
              onClick={() => loadRequirements(tender)}
            >
              <div className="tender-main">
                <div className="tender-reference">
                  {tender.reference_number}
                </div>

                <h3>{tender.title}</h3>

                <p>
                  {tender.description ||
                    "No description available."}
                </p>
              </div>

              <div className="tender-details">
                <span
                  className={getStatusClass(
                    tender.status
                  )}
                >
                  {formatStatus(tender.status)}
                </span>

                <div className="tender-detail">
                  <span>Created</span>

                  <strong>
                    {formatDate(tender.created_at)}
                  </strong>
                </div>

                <span className="view-link">
                  View Requirements →
                </span>
              </div>
            </button>
          ))}
        </section>
      )}
    </main>
  );
}

export default Tenders;