import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, ensureCsrf } from "../api.js";
import { useAuth } from "../auth.jsx";

export function PaymentPage() {
  const { refreshMe } = useAuth();
  const navigate = useNavigate();
  const [to_account_or_iban, setTo] = useState("");
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setErr("");
    setBusy(true);
    try {
      await ensureCsrf();
      const data = await api.post("/pay/", { to_account_or_iban, amount, description });
      await refreshMe();
      if (data.receipt_id) navigate(`/receipt/${data.receipt_id}`, { replace: true });
    } catch (ex) {
      setErr(ex.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="form-page">
      <div className="form-hero">
        <p className="form-eyebrow">Transfers</p>
        <h1 className="form-title">Send payment</h1>
        <p className="form-lead">Use another AlyBank account number or IBAN — same demo rails.</p>
      </div>
      <form className="form-card" onSubmit={onSubmit}>
        {err ? (
          <div className="alert alert--error" role="alert">
            {err}
          </div>
        ) : null}
        <label className="field">
          <span>To account or IBAN</span>
          <input
            className="input mono"
            value={to_account_or_iban}
            onChange={(e) => setTo(e.target.value)}
            placeholder="e.g. 1000000001 or ALYBANK10000000001"
            required
          />
        </label>
        <label className="field">
          <span>Amount (PKR)</span>
          <input
            className="input"
            type="number"
            inputMode="decimal"
            min="0.01"
            step="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            required
          />
        </label>
        <label className="field">
          <span>Reference (optional)</span>
          <input
            className="input"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g. Demo rent"
          />
        </label>
        <div className="form-actions">
          <button className="btn btn--primary" type="submit" disabled={busy}>
            {busy ? "Sending…" : "Send payment"}
          </button>
          <Link className="btn btn--ghost" to="/dashboard">
            Back
          </Link>
        </div>
      </form>
    </div>
  );
}
