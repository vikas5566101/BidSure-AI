function DocumentStatus({ documents }) {
  const processedCount = documents.filter(
    (document) =>
      document.status === "COMPLETED" ||
      document.status === "PROCESSED"
  ).length;

  return (
    <div className="panel">
      <div className="panel-header">
        <h3>Document Status</h3>

        <span>
          {processedCount} / {documents.length} processed
        </span>
      </div>

      {documents.length === 0 ? (
        <div className="empty-state">
          No documents found for this bid submission.
        </div>
      ) : (
        documents.map((document) => (
          <Document
            key={document.id}
            name={document.file_name}
            type={document.document_type}
            status={document.status}
            confidence="—"
          />
        ))
      )}
    </div>
  );
}

function Document({
  name,
  type,
  status,
  confidence,
}) {
  const processed =
    status === "COMPLETED" ||
    status === "PROCESSED";

  const displayStatus = processed
    ? "Processed"
    : status === "PROCESSING"
      ? "Processing"
      : status === "FAILED"
        ? "Failed"
        : "Pending";

  let tagClass = "tag pending";

  if (processed) {
    tagClass = "tag success";
  } else if (status === "FAILED") {
    tagClass = "tag error";
  } else if (status === "PROCESSING") {
    tagClass = "tag warning";
  }

  return (
    <div className="document-row">
      <div>
        <strong>{name}</strong>

        <span>{type}</span>
      </div>

      <div className="document-right">
        <span className={tagClass}>
          {displayStatus}
        </span>

        <span>{confidence}</span>
      </div>
    </div>
  );
}

export default DocumentStatus;