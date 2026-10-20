import { PAYMENT_LABELS } from "../utils/format";

export default function PaymentBadge({ reservation }) {
  if (!["accepted", "completed"].includes(reservation.status)) return <span className="muted">-</span>;
  return <span className={`badge badge-pay-${reservation.payment_status}`}>{PAYMENT_LABELS[reservation.payment_status]}</span>;
}
