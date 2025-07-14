import React, { useState } from "react";
import Input from "../../atoms/Input";
import Button from "../../atoms/Button";
import { useSelector } from "react-redux";

export default function OverseasPriceSection() {
  // 심볼(ticker) 및 거래소 코드 상태 관리
  const [symbol, setSymbol] = useState("AAPL");
  const [exchange, setExchange] = useState("NAS");
  const [priceData, setPriceData] = useState(null);
  const [error, setError] = useState(null);

  // Redux에서 API 베이스 URL 조회
  const baseUrl = useSelector((state) => state.FIN_SERVER_URL);

  // 해외 종목 현재가 조회
  const fetchOverseasPrice = async () => {
    setError(null);
    setPriceData(null);

    try {
      // 쿼리 파라미터 생성, 거래소 코드는 대문자로 변환
      const params = new URLSearchParams({
        symb: symbol,
        excd: exchange.toUpperCase(),
      });

      const response = await fetch(`${baseUrl}/api/fin/overseas?${params}`);
      if (!response.ok) {
        // 에러 응답 처리
        throw new Error(await response.text());
      }

      // JSON 데이터 파싱 및 상태 업데이트
      const data = await response.json();
      setPriceData(data);
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <section className="space-y-4">
      <h3 className="text-lg font-semibold">해외 종목 현재가</h3>

      <div className="flex flex-wrap gap-2 items-end">
        {/* 티커 입력 */}
        <Input
          label="티커"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
        />

        {/* 거래소 입력 (대문자 자동 변환) */}
        <Input
          label="거래소"
          value={exchange}
          onChange={(e) => setExchange(e.target.value.toUpperCase())}
        />

        {/* 조회 버튼 */}
        <Button onClick={fetchOverseasPrice}>조회</Button>
      </div>

      {/* 에러 메시지 출력 */}
      {error && <p className="text-sm text-red-500">{error}</p>}

      {/* 결과 데이터 출력 */}
      {priceData && (
        <pre className="overflow-x-auto rounded bg-gray-50 p-3 text-xs">
          {JSON.stringify(priceData, null, 2)}
        </pre>
      )}
    </section>
  );
}
