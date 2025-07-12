import React, { useState } from "react";
import Input from "../atoms/Input";
import Button from "../atoms/Button";
import { useSelector } from "react-redux";

export default function RealtimeSection() {
  const [path, setPath] = useState("/ws/investments");
  const [code, setCode] = useState("005930");
  const [price, setPrice] = useState(null);
  const wsRef = useRef(null);
  const FIN_SERVER_URL = useSelector((state) => state.FIN_SERVER_URL);

  useEffect(() => {
    // cleanup on unmount
    return () => {
      wsRef.current?.close();
    };
  }, []);

  const connect = () => {
    wsRef.current?.close();
    console.log(`Connecting to WebSocket: ${FIN_SERVER_URL + path} with code: ${code}`);
    const ws = new WebSocket(FIN_SERVER_URL + path);
    wsRef.current = ws;
    ws.onopen = () => ws.send(code);
    ws.onmessage = (e) => {
      const json = JSON.parse(e.data);
      setPrice(json.price);
    };
    ws.onerror = () => setPrice("error");
  };

  return (
    <div className="space-y-3">
      <h3 className="font-semibold text-lg">실시간 WebSocket 시세</h3>
      <p className="text-sm text-gray-600">
        ▶ 실시간 시세 스트리밍
        REST API 엔드포인트 앞에 <code>/ws</code>를 붙여 WebSocket에 연결합니다.
        <br />
        <code>/ws/investments?...</code>
        이런 식으로 하면 웹소켓 연결이 됩니다.
      </p>
      <div className="flex flex-wrap gap-2 items-end">
        <Input label="WS Path" value={path} onChange={(e) => setPath(e.target.value)} />
        <Input label="Code/Symbol" value={code} onChange={(e) => setCode(e.target.value)} />
        <Button onClick={connect}>Connect</Button>
        {price && <span className="font-mono text-lg ml-4">{price}</span>}
      </div>
    </div>
  );
}
