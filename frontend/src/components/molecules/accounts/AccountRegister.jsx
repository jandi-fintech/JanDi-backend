import React, { useEffect, useState, Fragment } from "react";
import axios from "axios";
import { useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import { Combobox } from "@headlessui/react";
import { motion } from "framer-motion";

// ------------------------------------------------------------------
// Axios 인스턴스: withCredentials → HttpOnly 쿠키 자동 전송
// ------------------------------------------------------------------
const useApi = (baseURL) =>
  axios.create({
    baseURL: baseURL,
    withCredentials: true,
  });

// codef api 에서 제공하는 은행 계좌
// 은행 목록 (기관명 + 코드)
const BANKS = [
  { name: "산업은행", code: "0002" },
  { name: "기업은행", code: "0003" },
  { name: "국민은행", code: "0004" },
  { name: "수협은행", code: "0007" },
  { name: "농협은행", code: "0011" },
  { name: "우리은행", code: "0020" },
  { name: "SC은행", code: "0023" },
  { name: "씨티은행", code: "0027" },
  { name: "대구은행", code: "0031" },
  { name: "부산은행", code: "0032" },
  { name: "광주은행", code: "0034" },
  { name: "제주은행", code: "0035" },
  { name: "전북은행", code: "0037" },
  { name: "경남은행", code: "0039" },
  { name: "새마을금고", code: "0045" },
  { name: "신협은행", code: "0048" },
  { name: "우체국", code: "0071" },
  { name: "KEB하나은행", code: "0081" },
  { name: "신한은행", code: "0088" },
  { name: "K뱅크", code: "0089" },
];

export default function AccountRegister() {
  const FIN_SERVER_URL = useSelector((state) => state.FIN_SERVER_URL);
  const api = useApi(FIN_SERVER_URL);
  const navigate = useNavigate();

  // 인터넷뱅킹 등록 폼 상태
  const [ibForm, setIbForm] = useState({
    institution_code: "",
    banking_id: "",
    banking_password: "",
  });
  const [ibBankQuery, setIbBankQuery] = useState("");

  // 계좌 등록 폼 상태
  const [accForm, setAccForm] = useState({
    institution_code: "",
    account_number: "",
    account_password: "",
  });
  const [accBankQuery, setAccBankQuery] = useState("");

  // 필터된 은행 목록
  const filteredIbBanks = BANKS.filter((b) => b.name.startsWith(ibBankQuery));
  const filteredAccBanks = BANKS.filter((b) => b.name.startsWith(accBankQuery));

  // ─── 인터넷뱅킹 등록 ─────────────────────────────────────────────────
  const handleRegisterIB = async () => {
    try {
      await api.post("/api/account/register/ib", ibForm);
      alert("인터넷뱅킹 정보 등록 성공");
      setIbForm({ institution_code: "", banking_id: "", banking_password: "" });
      setIbBankQuery("");
    } catch (err) {
      const msg = err.response?.data?.detail ?? err.message;
      alert(`인터넷뱅킹 등록 실패: ${JSON.stringify(msg)}`);
      console.error(err);
    }
  };

  // ─── 계좌 등록 ───────────────────────────────────────────────────────
  const handleRegisterAccount = async () => {
    try {
      const res = await api.post("/api/account/register", accForm);
      alert("계좌 등록 성공");
      // 등록된 계좌 정보 화면 이동 등 추가 처리 가능
      setAccForm({ institution_code: "", account_number: "", account_password: "" });
      setAccBankQuery("");
    } catch (err) {
      const msg = err.response?.data?.detail ?? err.message;
      alert(`계좌 등록 실패: ${JSON.stringify(msg)}`);
      console.error(err);
    }
  };

  return (
    <section className="space-y-8">
      {/* 인터넷뱅킹 등록 섹션 */}
      <div>
        <h2 className="text-xl font-semibold mb-4">🔐 인터넷뱅킹 등록</h2>
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-3"
        >
          <Combobox
            value={ibForm.institution_code}
            onChange={(val) =>
              setIbForm({ ...ibForm, institution_code: val })
            }
          >
            <Combobox.Input
              className="w-full border rounded px-3 py-2"
              onChange={(e) => setIbBankQuery(e.target.value)}
              displayValue={(code) => {
                const bank = BANKS.find((b) => b.code === code);
                return bank ? bank.name : "";
              }}
              placeholder="은행을 선택하세요"
            />
            {filteredIbBanks.length > 0 && (
              <Combobox.Options className="border rounded mt-1 max-h-40 overflow-auto">
                {filteredIbBanks.map((bank) => (
                  <Combobox.Option
                    key={bank.code}
                    value={bank.code}
                    as={Fragment}
                  >
                    {({ active, selected }) => (
                      <li
                        className={`cursor-pointer select-none p-2 ${active ? "bg-indigo-100" : ""
                          } ${selected ? "font-semibold" : ""}`}
                      >
                        {bank.name} ({bank.code})
                      </li>
                    )}
                  </Combobox.Option>
                ))}
              </Combobox.Options>
            )}
          </Combobox>

          <input
            placeholder="인터넷뱅킹 ID"
            value={ibForm.banking_id}
            onChange={(e) =>
              setIbForm({ ...ibForm, banking_id: e.target.value })
            }
            className="w-full border rounded px-3 py-2"
          />
          <input
            placeholder="인터넷뱅킹 비밀번호"
            type="password"
            value={ibForm.banking_password}
            onChange={(e) =>
              setIbForm({ ...ibForm, banking_password: e.target.value })
            }
            className="w-full border rounded px-3 py-2"
          />
          <button
            onClick={handleRegisterIB}
            className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
          >
            인터넷뱅킹 등록
          </button>
        </motion.div>
      </div>

      {/* 계좌 등록 섹션 */}
      <div>
        <h2 className="text-xl font-semibold mb-4">📄 계좌 등록</h2>
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-3"
        >
          <Combobox
            value={accForm.institution_code}
            onChange={(val) =>
              setAccForm({ ...accForm, institution_code: val })
            }
          >
            <Combobox.Input
              className="w-full border rounded px-3 py-2"
              onChange={(e) => setAccBankQuery(e.target.value)}
              displayValue={(code) => {
                const bank = BANKS.find((b) => b.code === code);
                return bank ? bank.name : "";
              }}
              placeholder="은행을 선택하세요"
            />
            {filteredAccBanks.length > 0 && (
              <Combobox.Options className="border rounded mt-1 max-h-40 overflow-auto">
                {filteredAccBanks.map((bank) => (
                  <Combobox.Option
                    key={bank.code}
                    value={bank.code}
                    as={Fragment}
                  >
                    {({ active, selected }) => (
                      <li
                        className={`cursor-pointer select-none p-2 ${active ? "bg-indigo-100" : ""
                          } ${selected ? "font-semibold" : ""}`}
                      >
                        {bank.name} ({bank.code})
                      </li>
                    )}
                  </Combobox.Option>
                ))}
              </Combobox.Options>
            )}
          </Combobox>

          <input
            placeholder="계좌번호"
            value={accForm.account_number}
            onChange={(e) =>
              setAccForm({ ...accForm, account_number: e.target.value })
            }
            className="w-full border rounded px-3 py-2"
          />
          <input
            placeholder="계좌 비밀번호"
            type="password"
            value={accForm.account_password}
            onChange={(e) =>
              setAccForm({ ...accForm, account_password: e.target.value })
            }
            className="w-full border rounded px-3 py-2"
          />
          <button
            onClick={handleRegisterAccount}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          >
            계좌 등록
          </button>
        </motion.div>
      </div>
    </section>
  );
}
