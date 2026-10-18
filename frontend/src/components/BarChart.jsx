export default function BarChart({ title, data, valueKey, format = (v) => v }) {
  const max = Math.max(1, ...data.map((d) => d[valueKey]));
  return (
    <figure className="chart">
      <figcaption>{title}</figcaption>
      <div className="chart-bars">
        {data.map((d) => (
          <div className="chart-col" key={d.label}>
            <span className="chart-value">{format(d[valueKey])}</span>
            <div className="chart-bar" style={{ height: `${(d[valueKey] / max) * 100}%` }} />
            <span className="chart-label">{d.label}</span>
          </div>
        ))}
      </div>
    </figure>
  );
}
