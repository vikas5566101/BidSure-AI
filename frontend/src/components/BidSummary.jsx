function BidSummary({ submission }) {
  if (!submission) {
    return (
      <section className="bid-summary">
        <div>
          <span className="status">LOADING</span>

          <h3>Bid Submission</h3>

          <p>Loading bid submission details...</p>
        </div>
      </section>
    );
  }

  const displayStatus = submission.status
    ? submission.status.replaceAll("_", " ")
    : "UNKNOWN";

  return (
    <section className="bid-summary">
      <div>
        <span className="status">
          {displayStatus}
        </span>

        <h3>Bid Submission #{submission.id}</h3>

        <p>
          AI-assisted bidder compliance verification
        </p>

        <div className="bid-meta">
          <span>
            Tender ID: {submission.tender_id}
          </span>

          <span>
            Bidder ID: {submission.bidder_id}
          </span>

          <span>
            Submitted:{" "}
            {new Date(
              submission.submitted_at
            ).toLocaleDateString()}
          </span>
        </div>
      </div>

      <div className="score">
        <strong>—</strong>
        <span>/ 100</span>

        <small>Compliance Score</small>
      </div>
    </section>
  );
}

export default BidSummary;