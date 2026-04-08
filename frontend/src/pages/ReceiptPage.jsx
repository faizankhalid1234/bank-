import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, ensureCsrf } from "../api.js";

export function ReceiptPage() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    setErr("");
    try {
      await ensureCsrf();
      const j = await api.get(`/receipt/${id}/`);
      setData(j);
    } catch (e) {
      setErr(e.message);
    }
  }

  useEffect(() => {
    load();
  }, [id]);

  async function save() {
    setBusy(true);
    try {
      await ensureCsrf();
      await api.post(`/receipt/${id}/save/`, {});
      await load();
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  if (err && !data) {
    return (
      <div className="form-page">
        <div className="alert alert--error">{err}</div>
        <Link className="btn btn--ghost" to="/history">
          Back to activity
        </Link>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="shell shell--center">
        <p className="muted">Loading receipt…</p>
      </div>
    );
  }

  const tx = data.transaction;

  return (
    <div className="receipt-page">
      <div className="receipt-card">
        <div className="receipt-top">
          <div>
            <p className="receipt-eyebrow">Payment sent</p>
            <h1 className="receipt-title">Receipt</h1>
            <p className="receipt-sub">To {data.recipient_label}</p>
          </div>
          <div className="receipt-amt">
            <span className="muted">PKR</span> <strong>{tx.amount}</strong>
          </div>
        </div>
        <dl className="receipt-dl">
          <div className="receipt-row">
            <dt>When</dt>
            <dd>{new Date(tx.created_at).toLocaleString()}</dd>
          </div>
          <div className="receipt-row">
            <dt>Reference</dt>
            <dd>{tx.description || "—"}</dd>
          </div>
          <div className="receipt-row">
            <dt>To IBAN</dt>
            <dd className="mono">{tx.counterparty_iban || "—"}</dd>
          </div>
          <div className="receipt-row">
            <dt>Your balance after</dt>
            <dd>
              <strong>PKR {tx.balance_after}</strong>
            </dd>
          </div>
        </dl>
        {err ? (
          <div className="alert alert--error" role="alert">
            {err}
          </div>
        ) : null}
        <div className="form-actions">
          <button type="button" className="btn btn--primary" onClick={save} disabled={busy || tx.user_saved}>
            {tx.user_saved ? "Saved" : busy ? "Saving…" : "Save to list"}
          </button>
          <Link className="btn btn--ghost" to="/history">
            Activity
          </Link>
          <Link className="btn btn--ghost" to="/dashboard">
            Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
