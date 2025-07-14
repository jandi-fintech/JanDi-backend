import React, { useState, useEffect } from "react";
import axios from "axios";
import Input from "../../atoms/Input";
import Button from "../../atoms/Button";
import { useSelector } from "react-redux";

/* ───────────────────────────────────────────────────────────────
  Axios 인스턴스  (withCredentials=true → HttpOnly 쿠키 자동 전송)
──────────────────────────────────────────────────────────────── */
const useApi = (baseURL) => axios.create({ baseURL, withCredentials: true });

/* ───────────────────────────────────────────────────────────────
  잔돈 대시보드 컴포넌트
──────────────────────────────────────────────────────────────── */
export default function JandonTest() {
  /* 상태 */
  const [roundUnit, setRoundUnit] = useState(100);   // 서버의 현재 단위
  const [txId, setTxId] = useState("");
  const [amount, setAmount] = useState(0);
  const [spares, setSpares] = useState([]);
  const [summary, setSummary] = useState(null);
  const [periodStart, setPeriodStart] = useState("2025-07-01T00:00");
  const [periodEnd, setPeriodEnd] = useState("2025-08-01T00:00");

  /* API */
  const FIN_SERVER_URL = useSelector((s) => s.FIN_SERVER_URL);
  const api = useApi(`${FIN_SERVER_URL}/api/spare-change`);

  /* 1) 현재 라운드-업 단위 조회 */
  const fetchRoundUnit = async () => {
    try {
      const { data } = await api.get("/round-up-unit");
      setRoundUnit(data.round_up_unit);
    } catch (err) {
      console.error(err);
    }
  };

  /* 2) 단위 변경(패치) */
  const patchRoundUnit = async (e) => {
    e.preventDefault();
    try {
      await api.patch("/round-up-unit", { unit: roundUnit });
      fetchRoundUnit();
    } catch (err) {
      console.error(err);
    }
  };

  /* 3) 잔돈 내역 조회 */
  const fetchSpares = async () => {
    try {
      const { data } = await api.get("/");
      setSpares(data);
    } catch (err) {
      console.error(err);
    }
  };

  /* 4) 잔돈 생성 (amount·tx_id 전송) */
  const createSpare = async (e) => {
    e.preventDefault();
    try {
      await api.post("/", { tx_id: txId, amount });
      fetchSpares();
    } catch (err) {
      console.error(err);
    }
  };

  /* 5) 기간 합계 */
  const fetchSummary = async () => {
    try {
      const { data } = await api.get("/summary", {
        params: { period_start: periodStart, period_end: periodEnd },
      });
      setSummary(data);
    } catch (err) {
      console.error(err);
    }
  };

  /* 초기 로드 */
  useEffect(() => {
    fetchRoundUnit();
    fetchSpares();
  }, []);

  /* ─────────────────────────────────────────────────────────── */
  return (
    <>

      {/* 라운드-업 단위 설정 */}
      <section className="rounded-lg bg-white p-6 shadow">
        <h2 className="mb-4 text-2xl font-semibold text-gray-800">
          라운드-업 단위
        </h2>
        <form onSubmit={patchRoundUnit} className="flex items-center gap-4">
          <Input
            type="number"
            label="단위(원)"
            value={roundUnit}
            onChange={(e) => setRoundUnit(+e.target.value)}
          />
          <Button type="submit">변경</Button>
        </form>
      </section>

      {/* 잔돈 생성 & 목록 */}
      <section className="grid gap-6 md:grid-cols-2">
        {/* 생성 */}
        <div className="rounded-lg bg-white p-6 shadow">
          <h2 className="mb-4 text-2xl font-semibold text-gray-800">
            잔돈 생성
          </h2>
          <form onSubmit={createSpare} className="space-y-4">
            <Input
              type="text"
              label="거래 ID"
              value={txId}
              onChange={(e) => setTxId(e.target.value)}
            />
            <Input
              type="number"
              label="금액(원)"
              value={amount}
              onChange={(e) => setAmount(+e.target.value)}
            />
            <Button type="submit">추가</Button>
          </form>
        </div>

        {/* 목록 */}
        <div className="rounded-lg bg-white p-6 shadow">
          <h2 className="mb-4 text-2xl font-semibold text-gray-800">
            잔돈 목록
          </h2>
          <Button onClick={fetchSpares} className="bg-gray-200 text-gray-800">
            목록 갱신
          </Button>
          <ul className="mt-4 max-h-64 space-y-2 overflow-y-auto">
            {spares.map((s) => (
              <li
                key={s.tx_id}
                className="flex justify-between rounded border border-green-100 bg-green-50 p-3"
              >
                <span>거래: {s.tx_id}</span>
                <span className="font-medium">+{s.round_up}원</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* 요약 */}
      <section className="rounded-lg bg-white p-6 shadow">
        <h2 className="mb-4 text-2xl font-semibold text-gray-800">요약</h2>
        <div className="mb-4 flex flex-col gap-4 md:flex-row">
          <Input
            type="datetime-local"
            label="시작"
            value={periodStart}
            onChange={(e) => setPeriodStart(e.target.value)}
          />
          <Input
            type="datetime-local"
            label="종료"
            value={periodEnd}
            onChange={(e) => setPeriodEnd(e.target.value)}
          />
          <Button onClick={fetchSummary}>조회</Button>
        </div>
        {summary && (
          <div className="text-lg font-semibold text-indigo-600">
            총 잔돈: {summary.total_round_up}원
          </div>
        )}
      </section>
    </>
  );
}
