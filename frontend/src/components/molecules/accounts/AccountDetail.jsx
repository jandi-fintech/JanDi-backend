import React, { useEffect, useState, Fragment } from "react";
import axios from "axios";
import { useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import { Combobox } from '@headlessui/react';
import { motion } from 'framer-motion';

// ------------------------------------------------------------------
// Axios 인스턴스: withCredentials → HttpOnly 쿠키 자동 전송
// ------------------------------------------------------------------
const useApi = (baseURL) =>
  axios.create({ baseURL, withCredentials: true });

export default function AccountDetail() {
  const FIN_SERVER_URL = useSelector((state) => state.FIN_SERVER_URL);
  const api = useApi(FIN_SERVER_URL);
  const navigate = useNavigate();

  const [accountDeailForm, setAccountDeailForm] = useState({
    account_number: "",
    start: "",
    end: "",
  });
  const [accountDetail, setAccountDetail] = useState(null);

  // YYYY-MM-DD → YYYYMMDD 변환 (빈 문자열은 undefined)
  const toParamDate = (iso) => (iso ? iso.replace(/-/g, "") : undefined);

  const handleGetAccountDetail = async () => {
    const { account_number, start, end } = accountDeailForm;

    // 계좌번호 유효성 검사 (10~20자리 숫자)
    if (!/^\d{10,20}$/.test(account_number)) {
      alert("계좌번호는 10~20자리 숫자여야 합니다.");
      return;
    }

    // 쿼리 파라미터 조립
    const params = {};
    const s = toParamDate(start);
    const e = toParamDate(end);
    if (s) params.start = s;
    if (e) params.end = e;

    try {
      const res = await api.get(
        `/api/account/detail/${account_number}`,
        { params }
      );
      setAccountDetail(res.data);
    } catch (err) {
      console.error("서버 응답 전체:", err.response?.data);
      // FastAPI에서 던진 detail 메시지를 우선 보여주고, 없으면 원본 에러 출력
      const msg =
        err.response?.data?.detail ||
        JSON.stringify(err.response?.data) ||
        "서버 에러가 발생했습니다.";
      alert(`조회 실패: ${msg}`);
      setAccountDetail(null);
    }
  };


  return (
    <section>
      {/* 계좌번호로 단일 조회 */}
      <h2 className="text-xl font-semibold mb-4">🔍 계좌번호로 조회</h2>
      <div className="flex flex-wrap items-center space-x-2 mb-4">
        {/* 계좌번호 */}
        <input
          type="text"
          placeholder="계좌번호 (10~20자리 숫자)"
          value={accountDeailForm.account_number}
          onChange={(e) =>
            setAccountDeailForm({ ...accountDeailForm, account_number: e.target.value.trim() })
          }
          className="flex-1 border rounded px-3 py-2"
        />

        {/* 시작일 */}
        <input
          type="text"
          value={accountDeailForm.start}
          onChange={(e) => setAccountDeailForm({ ...accountDeailForm, start: e.target.value })}
          className="border rounded px-3 py-2"
        />

        {/* 종료일 */}
        <input
          type="text"
          value={accountDeailForm.end}
          onChange={(e) => setAccountDeailForm({ ...accountDeailForm, end: e.target.value })}
          className="border rounded px-3 py-2"
        />

        <button
          onClick={handleGetAccountDetail}
          className="bg-indigo-500 text-white px-4 py-2 rounded hover:bg-indigo-600"
        >
          조회
        </button>
      </div>

      {accountDetail && (
        <pre className="bg-gray-100 p-4 rounded text-sm overflow-x-auto">
          {JSON.stringify(accountDetail, null, 2)}
        </pre>
      )}
    </section>
  );
}
