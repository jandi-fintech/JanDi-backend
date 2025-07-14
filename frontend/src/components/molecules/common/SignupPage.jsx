import React, { useState } from "react";
import axios from "axios";
import { useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";

// axios 인스턴스 생성 훅
const useApi = (baseURL) =>
  axios.create({ baseURL, withCredentials: true });

export default function SignupPage() {
  // Redux에서 서버 URL 가져오기
  const FIN_SERVER_URL = useSelector((s) => s.FIN_SERVER_URL);
  const api = useApi(FIN_SERVER_URL);
  const navigate = useNavigate(); // 페이지 이동 훅

  // 폼 상태 관리
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const { username, email, password, confirmPassword } = form;

  // 입력값 업데이트 공통 핸들러
  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  // 회원가입 요청 실행
  const handleSignup = async () => {
    if (password !== confirmPassword) {
      return alert("비밀번호가 일치하지 않습니다.");
    }

    try {
      await api.post("/api/user/create", {
        username,
        email,
        password1: password,
        password2: confirmPassword,
      });
      alert("회원가입 완료! 로그인 페이지로 이동합니다.");
      navigate("/login"); // 로그인 페이지로 이동
    } catch (e) {
      const msg = e.response?.data?.detail || "알 수 없는 오류";
      alert("회원가입 실패: " + msg);
      console.error(e);
    }
  };

  return (
    <main className="min-h-screen flex items-center justify-center bg-gray-50 p-6">
      <div className="w-full max-w-sm bg-white rounded-xl shadow p-8 space-y-4">
        <h1 className="text-2xl font-bold text-center">회원가입</h1>

        {/* 사용자명 입력 */}
        <input
          name="username"
          className="w-full border rounded px-3 py-2"
          placeholder="아이디"
          value={username}
          onChange={handleChange}
        />

        {/* 이메일 입력 */}
        <input
          name="email"
          className="w-full border rounded px-3 py-2"
          placeholder="이메일"
          value={email}
          onChange={handleChange}
        />

        {/* 비밀번호 입력 */}
        <input
          name="password"
          type="password"
          className="w-full border rounded px-3 py-2"
          placeholder="비밀번호"
          value={password}
          onChange={handleChange}
        />

        {/* 비밀번호 확인 입력 */}
        <input
          name="confirmPassword"
          type="password"
          className="w-full border rounded px-3 py-2"
          placeholder="비밀번호 확인"
          value={confirmPassword}
          onChange={handleChange}
        />

        {/* 회원가입 버튼 */}
        <button
          onClick={handleSignup}
          className="w-full bg-green-600 text-white py-2 rounded hover:bg-green-700"
        >
          회원가입
        </button>
      </div>
    </main>
  );
}
