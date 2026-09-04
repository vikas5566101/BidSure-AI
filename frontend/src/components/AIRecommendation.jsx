function AIRecommendation() {
  return (
    <div className="panel recommendation">
      <div className="panel-header">
        <h3>AI Recommendation</h3>

        <span className="tag warning">Medium Risk</span>
      </div>

      <p className="recommendation-text">
        The bidder appears largely compliant, but some documents
        are still pending verification.
      </p>

      <div className="recommendation-list">
        <div>
          <span>✓</span>
          <p>GST certificate information is consistent.</p>
        </div>

        <div>
          <span>✓</span>
          <p>Udyam certificate information is consistent.</p>
        </div>

        <div>
          <span>!</span>
          <p>PAN verification is still pending.</p>
        </div>

        <div>
          <span>!</span>
          <p>Income Tax document requires verification.</p>
        </div>
      </div>

      <div className="recommendation-footer">
        <strong>Suggested action</strong>

        <p>
          Complete the pending document verification before making
          the final procurement decision.
        </p>
      </div>
    </div>
  );
}

export default AIRecommendation;