import React, { use, useState } from "react";
import Input from "../atoms/Input";
import Button from "../atoms/Button";
import { useSelector } from "react-redux";

export default function DomesticPriceSection() {
  const [code, setCode] = useState("");
  const [idxCode, setIdxCode] = useState("");
  const [result, setResult] = useState(null);
  const [err, setErr] = useState(null);
  const FIN_SERVER_URL = useSelector((state) => state.FIN_SERVER_URL);

  const fetchStock = async () => {
    setErr(null);
    setResult(null);
    try {
      const res = await fetch(`${FIN_SERVER_URL}/investments?itm_no=${code}`);
      if (!res.ok) throw new Error(await res.text());
      setResult(await res.json());
    } catch (e) {
      setErr(e.message);
    }
  };
  const fetchIndex = async () => {
    setErr(null);
    setResult(null);
    try {
      const res = await fetch(`${FIN_SERVER_URL}/index-price?idx_code=${idxCode}`);
      if (!res.ok) throw new Error(await res.text());
      setResult(await res.json());
    } catch (e) {
      setErr(e.message);
    }
  };

  return (
    <div className="space-y-3">
      <h3 className="font-semibold text-lg">국내 종목·지수 현재가</h3>
      <div className="flex flex-wrap gap-2 items-end">
        <Input label="종목코드(6)" value={code} onChange={(e) => setCode(e.target.value)} />
        <Button onClick={fetchStock}>종목 조회</Button>
        <Input label="지수코드(4)" value={idxCode} onChange={(e) => setIdxCode(e.target.value)} />
        <Button onClick={fetchIndex}>지수 조회</Button>
      </div>
      {err && <p className="text-red-500 text-sm">{err}</p>}
      {result && (
        <pre className="bg-gray-50 p-3 rounded text-xs overflow-x-auto">{JSON.stringify(result, null, 2)}</pre>
      )}
    </div>
  );
}
