import React, { useState } from "react";
import Input from "../../atoms/Input";
import Button from "../../atoms/Button";
import { useSelector } from "react-redux";

export default function DomesticPriceSection() {
  // 종목 코드 및 지수 코드 상태 관리
  const [stockCode, setStockCode] = useState("");
  const [indexCode, setIndexCode] = useState("");
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  // API 베이스 URL
  const baseUrl = useSelector((state) => state.FIN_SERVER_URL);

  // 데이터 조회 공통 함수
  const fetchData = async (endpoint, queryKey, queryValue) => {
    setError(null);
    setData(null);
    try {
      const url = `${baseUrl}${endpoint}?${queryKey}=${queryValue}`;
      const response = await fetch(url);
      if (!response.ok) throw new Error(await response.text());
      const json = await response.json();
      setData(json);
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <section className="space-y-4">
      <h3 className="text-lg font-semibold">국내 종목·지수 현재가</h3>

      <div className="flex flex-wrap gap-2 items-end">
        {/* 종목 조회 */}
        <Input
          label="종목 코드 (6자리)"
          value={stockCode}
          onChange={(e) => setStockCode(e.target.value)}
        />
        <Button onClick={() => fetchData("/api/fin/investments", "itm_no", stockCode)}>
          종목 조회
        </Button>

        {/* 지수 조회 */}
        <Input
          label="지수 코드 (4자리)"
          value={indexCode}
          onChange={(e) => setIndexCode(e.target.value)}
        />
        <Button onClick={() => fetchData("/api/fin/index", "idx_code", indexCode)}>
          지수 조회
        </Button>
      </div>

      {/* 에러 메시지 */}
      {error && <p className="text-sm text-red-500">{error}</p>}

      {/* 결과 출력 */}
      {data && (
        <pre className="overflow-x-auto rounded bg-gray-50 p-3 text-xs">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </section>
  );
}
