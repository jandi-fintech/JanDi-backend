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

// codef api 에서 제공하는 은행 계좌
// 은행 목록 (기관명 + 코드)
const BANKS = [
  { name: '산업은행', code: '0002' },
  { name: '기업은행', code: '0003' },
  { name: '국민은행', code: '0004' },
  { name: '수협은행', code: '0007' },
  { name: '농협은행', code: '0011' },
  { name: '우리은행', code: '0020' },
  { name: 'SC은행', code: '0023' },
  { name: '씨티은행', code: '0027' },
  { name: '대구은행', code: '0031' },
  { name: '부산은행', code: '0032' },
  { name: '광주은행', code: '0034' },
  { name: '제주은행', code: '0035' },
  { name: '전북은행', code: '0037' },
  { name: '경남은행', code: '0039' },
  { name: '새마을금고', code: '0045' },
  { name: '신협은행', code: '0048' },
  { name: '우체국', code: '0071' },
  { name: 'KEB하나은행', code: '0081' },
  { name: '신한은행', code: '0088' },
  { name: 'K뱅크', code: '0089' },
];

export default function AccountTestPage() {
  const FIN_SERVER_URL = useSelector((state) => state.FIN_SERVER_URL);
  const api = useApi(FIN_SERVER_URL);
  const navigate = useNavigate();

  // 로그인 체크
  useEffect(() => {
    api.get("/api/user/check_login").catch(() => {
      alert("로그인이 필요합니다. 로그인 페이지로 이동합니다.");
      navigate("/login");
    });
  }, [api, navigate]);

  // 폼 상태: 기관코드 필드로 변경
  const [registerForm, setRegisterForm] = useState({
    institution_code: "",
    banking_id: "",
    banking_password: "",
    account_number: "",
    account_password: "",
  });
  const [bankQuery, setBankQuery] = useState("");
  const [accounts, setAccounts] = useState([]);

  const filteredBanks = BANKS.filter((b) => b.name.startsWith(bankQuery));

  // 계좌 등록
  const handleRegister = async () => {
    try {
      await api.post("/api/account/register", registerForm);
      alert("계좌 등록 성공");
      setRegisterForm({
        institution_code: "",
        banking_id: "",
        banking_password: "",
        account_number: "",
        account_password: "",
      });
      setBankQuery("");
    } catch (err) {
      const msg = err.response?.data?.detail ?? err.message;
      alert(`등록 실패: ${JSON.stringify(msg)}`);
      console.error(err);
    }
  };

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
    <main className="p-6 max-w-[800px] mx-auto space-y-10">
      {/* 계좌 등록 */}
      <section>
        <h2 className="text-xl font-semibold mb-4">📄 계좌 등록</h2>
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="space-y-3">
          <Combobox
            value={registerForm.institution_code}
            onChange={(val) =>
              setRegisterForm({ ...registerForm, institution_code: val })
            }
          >
            <Combobox.Input
              className="w-full border rounded px-3 py-2"
              onChange={(e) => setBankQuery(e.target.value)}
              displayValue={(code) => {
                const bank = BANKS.find((b) => b.code === code);
                return bank ? bank.name : "";
              }}
              placeholder="은행을 선택하세요"
            />
            {filteredBanks.length > 0 && (
              <Combobox.Options className="border rounded mt-1 max-h-40 overflow-auto">
                {filteredBanks.map((bank) => (
                  <Combobox.Option key={bank.code} value={bank.code} as={Fragment}>
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
            value={registerForm.banking_id}
            onChange={(e) =>
              setRegisterForm({ ...registerForm, banking_id: e.target.value })
            }
            className="w-full border rounded px-3 py-2"
          />
          <input
            placeholder="인터넷뱅킹 비밀번호"
            type="password"
            value={registerForm.banking_password}
            onChange={(e) =>
              setRegisterForm({ ...registerForm, banking_password: e.target.value })
            }
            className="w-full border rounded px-3 py-2"
          />
          <input
            placeholder="계좌번호"
            value={registerForm.account_number}
            onChange={(e) =>
              setRegisterForm({ ...registerForm, account_number: e.target.value })
            }
            className="w-full border rounded px-3 py-2"
          />
          <input
            placeholder="계좌 비밀번호"
            type="password"
            value={registerForm.account_password}
            onChange={(e) =>
              setRegisterForm({ ...registerForm, account_password: e.target.value })
            }
            className="w-full border rounded px-3 py-2"
          />
          <button
            onClick={handleRegister}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          >
            계좌 등록
          </button>
        </motion.div>
      </section>

      {/* 계좌 목록 조회 */}
      <section>
        <h2 className="text-xl font-semibold mb-4">📋 계좌 목록 조회</h2>
        <button
          onClick={handleGetAccounts}
          className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
        >
          계좌 목록 가져오기
        </button>
        <ul className="list-disc list-inside mt-4">
          {accounts.map((acc) => (
            <li key={acc.id} className="py-1">
              {acc.id} - {acc.account_number} ({acc.banking_id}, 코드: {acc.institution_code})
            </li>
          ))}
        </ul>
      </section>

      {/* 계좌번호로 단일 조회 */}
      <section>
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
    </main>
  );
}
