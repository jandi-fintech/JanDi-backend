import React, { useState } from "react";
import Input from "../atoms/Input";
import Button from "../atoms/Button";
import { useSelector } from "react-redux";

export default function OverseasPriceSection() {
  const [symb, setSymb] = useState("AAPL");
  const [excd, setExcd] = useState("NAS");
  const [result, setResult] = useState(null);
  const [err, setErr] = useState(null);
  const FIN_SERVER_URL = useSelector((state) => state.FIN_SERVER_URL);

  const fetchPrice = async () => {
    setErr(null);
    setResult(null);
    try {
      const qs = new URLSearchParams({ symb, excd });
      const res = await fetch(`${FIN_SERVER_URL}/overseas?${qs}`);
      if (!res.ok) throw new Error(await res.text());
      setResult(await res.json());
    } catch (e) {
      setErr(e.message);
    }
  };

  return (
    <div className="space-y-3">
      <h3 className="font-semibold text-lg">해외 종목 현재가</h3>
      <div className="flex flex-wrap gap-2 items-end">
        <Input label="티커" value={symb} onChange={(e) => setSymb(e.target.value)} />
        <Input label="거래소" value={excd} onChange={(e) => setExcd(e.target.value.toUpperCase())} />
        <Button onClick={fetchPrice}>조회</Button>
      </div>
      {err && <p className="text-red-500 text-sm">{err}</p>}
      {result && (
        <pre className="bg-gray-50 p-3 rounded text-xs overflow-x-auto">{JSON.stringify(result, null, 2)}</pre>
      )}
    </div>
  );
}