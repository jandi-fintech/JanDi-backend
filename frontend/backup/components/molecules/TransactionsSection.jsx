import React, { useState } from "react";
import Input from "../atoms/Input";
import Button from "../atoms/Button";
import { useSelector } from "react-redux";

const FIN_SERVER_URL = useSelector((state) => state.FIN_SERVER_URL);

export default function TransactionsSection() {
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [rows, setRows] = useState(null);
  const [err, setErr] = useState(null);
  const FIN_SERVER_URL = useSelector((state) => state.FIN_SERVER_URL);

  const fetchTx = async () => {
    setErr(null);
    setRows(null);
    try {
      const qs = new URLSearchParams({ start: start.replaceAll("-", ""), end: end.replaceAll("-", "") });
      const res = await fetch(`${FIN_SERVER_URL}/transactions?${qs}`);
      if (!res.ok) throw new Error(await res.text());
      const json = await res.json();
      if (!Array.isArray(json) || json.length === 0) {
        throw new Error("No transactions found for the given date range.");
      }
      setRows(json);
    } catch (e) {
      setErr(e.message);
    }
  };

  return (
    <div className="space-y-3">
      <h3 className="font-semibold text-lg">거래내역 조회</h3>
      <div className="flex flex-wrap gap-2 items-end">
        <Input type="date" label="Start" value={start} onChange={(e) => setStart(e.target.value)} />
        <Input type="date" label="End" value={end} onChange={(e) => setEnd(e.target.value)} />
        <Button onClick={fetchTx}>조회</Button>
      </div>
      {err && <p className="text-red-500 text-sm">{err}</p>}
      {rows && (
        <pre className="bg-gray-50 p-3 rounded text-xs overflow-x-auto">{JSON.stringify(rows, null, 2)}</pre>
      )}
    </div>
  );
}
