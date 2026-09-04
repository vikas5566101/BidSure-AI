function StatCard({ label, value }) {
  return (
    <div className="stat-card">
      <span>{label}</span>

      <strong>{value}</strong>
    </div>
  );
}

export default StatCard;