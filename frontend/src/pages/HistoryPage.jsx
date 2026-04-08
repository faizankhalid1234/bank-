import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ensureCsrf } from "../api.js";

const kindLabel = {
  credit: "Credit",
  debit: "Debit",
  payment_sent: "Payment sent",
  payment_received: "Received",
};

export function HistoryPage() {
  const [savedOnly, setSavedOnly] = useState(false);
  const [rows, setRows] = useState([]);
  const [err, setErr] = useState("");
  const [busyId, setBusyId] = useState(null);

  async function load() {
    setErr("");
    try {
      await ensureCsrf();
      const q = savedOnly ? "?saved=1" : "";
      const data = await api.get(`/history/${q}`);
      setRows(data.transactions || []);
    } catch (e) {
      setErr(e.message);
    }
  }

  useEffect(() => {
    load();
  }, [savedOnly]);

  async function toggleSave(tx) {
    if (tx.kind !== "payment_sent") return;
    setBusyId(tx.id);
    setErr("");
    try {
      await ensureCsrf();
      if (tx.user_saved) {
        await api.post(`/receipt/${tx.id}/unsave/`, {});
      } else {
        await api.post(`/receipt/${tx.id}/save/`, {});
      }
      await load();
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="history-page">
      <div className="history-head">
        <div>
          <p className="form-eyebrow">Ledger</p>
          <h1 className="form-title">Activity</h1>
          <p className="form-lead">Every movement on your demo account — newest first.</p>
        </div>
        <div className="history-filters">
          <button
            type="button"
            className={`chip ${!savedOnly ? "chip--on" : ""}`}
            onClick={() => setSavedOnly(false)}
          >
            All
          </button>
          <button
            type="button"
            className={`chip ${savedOnly ? "chip--on" : ""}`}
            onClick={() => setSavedOnly(true)}
          >
            Saved receipts
          </button>
        </div>
      </div>
      {err ? (
        <div className="alert alert--error" role="alert">
          {err}
        </div>
      ) : null}
      <div className="history-table-wrap">
        <table className="history-table">
          <thead>
            <tr>
              <th>When</th>
              <th>Type</th>
              <th className="right">Amount</th>
              <th>Details</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={5} className="muted">
                  No transactions yet.
                </td>
              </tr>
            ) : (
              rows.map((tx) => (
                <tr key={tx.id}>
                  <td className="mono">{new Date(tx.created_at).toLocaleString()}</td>
                  <td>
                    <span className="pill">{kindLabel[tx.kind] || tx.kind}</span>
                  </td>
                  <td className="right mono">
                    <strong>PKR {tx.amount}</strong>
                  </td>
                  <td className="muted">{tx.description || "—"}</td>
                  <td className="right">
                    {tx.kind === "payment_sent" ? (
                      <button
                        type="button"
                        className="link"
                        onClick={() => toggleSave(tx)}
                        disabled={busyId === tx.id}
                      >
                        {tx.user_saved ? "Unsave" : "Save"}
                      </button>
                    ) : (
                      <span className="muted">—</span>
                    )}
                    {tx.kind === "payment_sent" ? (
                      <Link className="link" to={`/receipt/${tx.id}`}>
                        {" "}
                        View
                      </Link>
                    ) : null}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <div className="form-actions" style={{ marginTop: "1rem" }}>
        <Link className="btn btn--ghost" to="/dashboard">
          Dashboard
        </Link>
      </div>
    </div>
  );
}
