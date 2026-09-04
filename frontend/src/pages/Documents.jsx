import { useEffect, useState } from "react";

import api from "../services/api";

function Documents({
  bidSubmissionId,
  setCurrentPage,
}) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [processingId, setProcessingId] = useState(null);

  const [extractions, setExtractions] = useState({});
  const [extractionLoading, setExtractionLoading] =
    useState({});

  useEffect(() => {
    if (bidSubmissionId) {
      loadDocuments();
    }
  }, [bidSubmissionId]);

  async function loadDocuments() {
    try {
      setLoading(true);
      setError("");

      const response = await api.get(
        `/bid-submissions/${bidSubmissionId}/documents`
      );

      const documentList = response.data;

      setDocuments(documentList);

      await loadExtractions(documentList);
    } catch (err) {
      console.error(
        "Failed to load documents:",
        err
      );

      setError(
        err.response?.data?.detail ||
          "Failed to load documents."
      );
    } finally {
      setLoading(false);
    }
  }

  async function loadExtractions(documentList) {
    const extractionResults = {};

    for (const document of documentList) {
      try {
        setExtractionLoading((previous) => ({
          ...previous,
          [document.id]: true,
        }));

        const response = await api.get(
          `/bid-submissions/documents/${document.id}/extraction`
        );

        extractionResults[document.id] =
          response.data;
      } catch (err) {
        if (err.response?.status !== 404) {
          console.error(
            `Failed to load extraction for document ${document.id}:`,
            err
          );
        }
      } finally {
        setExtractionLoading((previous) => ({
          ...previous,
          [document.id]: false,
        }));
      }
    }

    setExtractions(extractionResults);
  }

  async function processDocument(documentId) {
    try {
      setProcessingId(documentId);
      setError("");

      const response = await api.post(
        `/bid-submissions/documents/${documentId}/process`
      );

      setExtractions((previous) => ({
        ...previous,
        [documentId]: response.data,
      }));

      await loadDocuments();
    } catch (err) {
      console.error(
        "Failed to process document:",
        err
      );

      setError(
        err.response?.data?.detail ||
          "Failed to process document."
      );
    } finally {
      setProcessingId(null);
    }
  }

  function getStatusClass(status) {
    switch (status) {
      case "COMPLETED":
      case "UPLOADED":
        return "tag success";

      case "PROCESSING":
      case "PENDING":
        return "tag warning";

      case "FAILED":
        return "tag error";

      default:
        return "tag";
    }
  }

  function getStatusLabel(status) {
    if (!status) {
      return "UNKNOWN";
    }

    return status.replaceAll("_", " ");
  }

  function formatConfidence(value) {
    if (
      value === null ||
      value === undefined
    ) {
      return "—";
    }

    return `${Math.round(value * 100)}%`;
  }

  if (loading) {
    return (
      <main className="page">
        <div className="panel loading-panel">
          Loading documents...
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="page">
        <button
          className="back-button"
          onClick={() =>
            setCurrentPage("submission")
          }
        >
          ← Back to Submission
        </button>

        <div className="panel error-panel">
          {error}
        </div>
      </main>
    );
  }

  return (
    <main className="page">
      <button
        className="back-button"
        onClick={() =>
          setCurrentPage("submission")
        }
      >
        ← Back to Submission
      </button>

      <div className="page-header">
        <div>
          <p className="header-label">
            CPCL • GeM Procurement
          </p>

          <h2>Bid Documents</h2>

          <p>
            Documents submitted for Bid Submission #
            {bidSubmissionId}.
          </p>
        </div>

        <div className="page-count">
          {documents.length}{" "}
          {documents.length === 1
            ? "Document"
            : "Documents"}
        </div>
      </div>

      {documents.length === 0 ? (
        <div className="panel empty-state">
          No documents have been uploaded for this
          submission.
        </div>
      ) : (
        <section className="documents-list">
          {documents.map((document) => {
            const extraction =
              extractions[document.id];

            const isProcessing =
              processingId === document.id;

            const extractionIsLoading =
              extractionLoading[document.id];

            return (
              <article
                className="document-card"
                key={document.id}
              >
                <div className="document-card-header">
                  <div>
                    <h3>
                      {document.file_name}
                    </h3>

                    <span className="document-type">
                      {document.document_type ||
                        "Document"}
                    </span>
                  </div>

                  <span
                    className={getStatusClass(
                      document.status
                    )}
                  >
                    {getStatusLabel(
                      document.status
                    )}
                  </span>
                </div>

                <div className="document-info-grid">
                  <div>
                    <span>Document ID</span>

                    <strong>
                      {document.id}
                    </strong>
                  </div>

                  <div>
                    <span>Uploaded</span>

                    <strong>
                      {document.created_at
                        ? new Date(
                            document.created_at
                          ).toLocaleDateString()
                        : "—"}
                    </strong>
                  </div>
                </div>

                {extractionIsLoading ? (
                  <div className="extraction-loading">
                    Loading extraction...
                  </div>
                ) : extraction ? (
                  <div className="extraction-section">
                    <div className="extraction-header">
                      <h4>
                        Document Intelligence
                      </h4>

                      <span>
                        {extraction.classification ||
                          "—"}
                      </span>
                    </div>

                    <div className="extraction-grid">
                      <div>
                        <span>
                          Classification Confidence
                        </span>

                        <strong>
                          {formatConfidence(
                            extraction.classification_confidence
                          )}
                        </strong>
                      </div>

                      <div>
                        <span>
                          Extraction Method
                        </span>

                        <strong>
                          {extraction.extraction_method ||
                            "—"}
                        </strong>
                      </div>
                    </div>

                    {extraction.extracted_fields && (
                      <div className="extracted-fields">
                        <h4>
                          Extracted Fields
                        </h4>

                        <div className="fields-list">
                          {Object.entries(
                            extraction.extracted_fields
                          ).map(
                            ([key, value]) => (
                              <div
                                className="field-row"
                                key={key}
                              >
                                <span>{key}</span>

                                <strong>
                                  {typeof value ===
                                  "object"
                                    ? JSON.stringify(
                                        value
                                      )
                                    : String(
                                        value
                                      )}
                                </strong>
                              </div>
                            )
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ) : null}

                <div className="document-actions">
                  <button
                    className="process-button"
                    onClick={() =>
                      processDocument(
                        document.id
                      )
                    }
                    disabled={isProcessing}
                  >
                    {isProcessing
                      ? "Processing..."
                      : document.status ===
                        "COMPLETED"
                      ? "Process Again"
                      : "Process Document"}
                  </button>
                </div>
              </article>
            );
          })}
        </section>
      )}
    </main>
  );
}

export default Documents;