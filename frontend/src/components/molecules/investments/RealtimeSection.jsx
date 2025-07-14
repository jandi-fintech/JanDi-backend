import React, { useState, useRef, useEffect } from "react";
import Input from "../../atoms/Input";
import Button from "../../atoms/Button";
import { useSelector } from "react-redux";

export default function RealtimeSection() {
  // WebSocket 경로 및 심볼, 실시간 데이터 관리
  const [wsPath, setWsPath] = useState("/api/fin/ws/investments");
  const [symbol, setSymbol] = useState("005930");
  const [priceData, setPriceData] = useState(null);
  const wsRef = useRef(null);
  const baseUrl = useSelector((state) => state.FIN_SERVER_URL);

  // 컴포넌트 언마운트 시 WS 닫기
  useEffect(() => {
    return () => wsRef.current?.close();
  }, []);

  // WS 연결 핸들러
  const handleConnect = () => {
    wsRef.current?.close(); // 기존 연결 종료
    const url = `${baseUrl}${wsPath}`;
    console.log(`WS 연결: ${url}, 심볼: ${symbol}`);

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => ws.send(symbol); // 연결 시 심볼 전송
    ws.onmessage = (e) => setPriceData(JSON.parse(e.data)); // 메시지 수신 처리
    ws.onerror = () => setPriceData({ error: "WebSocket error" }); // 에러 처리
  };

  // WS 연결 해제 핸들러
  const handleDisconnect = () => {
    wsRef.current?.close();
    setPriceData(null);
    console.log("WS 연결 해제");
  };

  return (
    <section className="space-y-4">
      <h3 className="text-lg font-semibold">실시간 WebSocket 시세</h3>
      <p className="text-sm text-gray-600">
        REST API 앞에 <code>/ws</code>를 붙여 WebSocket에 연결합니다.
      </p>

      <div className="flex flex-wrap gap-2 items-end">
        <Input
          label="WS 경로"
          value={wsPath}
          onChange={(e) => setWsPath(e.target.value)}
        />
        <Input
          label="심볼"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
        />
        <Button onClick={handleConnect}>Connect</Button>
        <Button onClick={handleDisconnect}>Disconnect</Button>
      </div>

      {priceData && (
        <pre className="overflow-x-auto rounded bg-gray-50 p-3 text-xs">
          {JSON.stringify(priceData, null, 2)}
        </pre>
      )}
    </section>
  );
}
