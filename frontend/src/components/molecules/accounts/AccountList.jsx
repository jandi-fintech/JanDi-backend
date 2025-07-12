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
  axios.create({
    baseURL,
    withCredentials: true,
  });

export default function AccountList() {
  const FIN_SERVER_URL = useSelector((state) => state.FIN_SERVER_URL);
  const api = useApi(FIN_SERVER_URL);

  const [accounts, setAccounts] = useState(null);

  // 계좌 목록 조회
  const handleGetAccounts = async () => {
    try {
      const res = await api.get("/api/account/list");
      setAccounts(res.data);
    } catch (err) {
      alert("목록 조회 실패");
      console.error(err);
    }
  };

  return (
    <section>
      {/* 계좌 목록 조회 */}
      <h2 className="text-xl font-semibold mb-4">📋 계좌 목록 조회</h2>
      <button
        onClick={handleGetAccounts}
        className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
      >
        계좌 목록 가져오기
      </button>
      <ul className="list-disc list-inside mt-4">
        {accounts && (
          <pre className="bg-gray-100 p-4 rounded text-sm overflow-x-auto">
            {JSON.stringify(accounts, null, 2)}
          </pre>
        )}
      </ul>
    </section>
  );
}
