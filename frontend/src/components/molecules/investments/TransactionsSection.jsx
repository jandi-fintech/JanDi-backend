import React, { useState } from "react";
import Input from "../../atoms/Input";
import Button from "../../atoms/Button";
import { useSelector } from "react-redux";

export default function TransactionsSection() {
  // 조회 기간: 시작일, 종료일 (YYYY-MM-DD)
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  // API 응답 데이터 및 에러 메시지
  const [transactions, setTransactions] = useState(null);
  const [error, setError] = useState(null);

  // Redux에서 서버 URL 가져오기
  const FIN_SERVER_URL = useSelector((state) => state.FIN_SERVER_URL);

  /**
   * 거래내역 조회 실행
   */
  const fetchTransactions = async () => {
    setError(null);
    setTransactions(null);

    try {
      // 날짜 포맷 변경 (YYYYMMDD)
      const params = new URLSearchParams({
        start: startDate.replaceAll("-", ""),
        end: endDate.replaceAll("-", ""),
      });

      const response = await fetch(
        `${FIN_SERVER_URL}/api/fin/transactions?${params}`
      );

      if (!response.ok) {
        // HTTP 에러 처리
        throw new Error(await response.text());
      }

      const data = await response.json();

      if (!Array.isArray(data) || data.length === 0) {
        // 데이터 없을 때 예외 처리
        throw new Error("해당 기간에 거래내역이 없습니다.");
      }

      setTransactions(data);
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">거래내역 조회</h3>

      <div className="flex flex-wrap gap-2 items-end">
        <Input
          type="date"
          label="시작일"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
        />
        <Input
          type="date"
          label="종료일"
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
        />
        <Button onClick={fetchTransactions}>조회</Button>
      </div>

      {error && (
        <p className="text-sm text-red-500">
          {/* 에러 메시지 표시 */}
          {error}
        </p>
      )}

      {transactions && (
        <pre className="overflow-x-auto rounded bg-gray-50 p-4 text-xs">
          {JSON.stringify(transactions, null, 2)}
        </pre>
      )}
    </div>
  );
}
