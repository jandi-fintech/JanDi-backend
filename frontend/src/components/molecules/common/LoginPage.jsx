import React, { useState } from "react";
import axios from "axios";
import qs from "qs";
import { useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import Input from "../../atoms/Input";
import Button from "../../atoms/Button";

// axios 인스턴스 생성 훅 (withCredentials 설정 포함)
const useApiClient = (baseURL) =>
  axios.create({ baseURL, withCredentials: true });

export default function LoginPage() {
  // Redux에서 API 베이스 URL 조회
  const FIN_SERVER_URL = useSelector((state) => state.FIN_SERVER_URL);
  const api = useApiClient(FIN_SERVER_URL);
  const navigate = useNavigate(); // 페이지 이동 훅

  // 로그인 폼 상태 관리
  const [form, setForm] = useState({ username: "", password: "" });
  const { username, password } = form;

  // 입력값 공통 변경 핸들러
  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  // 로그인 요청 핸들러
  const handleLogin = async () => {
    try {
      // form 데이터를 x-www-form-urlencoded 형식으로 전송
      await api.post(
        "/api/user/login",
        qs.stringify({ username, password }),
        { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
      );

      alert("로그인 성공! 대시보드로 이동합니다.");
      navigate("/dashboard"); // 로그인 성공 후 이동
    } catch (error) {
      // 에러 메시지 추출 및 알림
      const message = error.response?.data?.detail || error.message;
      alert(`로그인 실패: ${message}`);
      console.error(error);
    }
  };

  return (
    <main className="min-h-screen flex items-center justify-center bg-gray-50 p-6">
      <section className="w-full max-w-sm bg-white rounded-xl shadow p-8 space-y-6">
        {/* 페이지 타이틀 */}
        <h1 className="text-2xl font-bold text-center">로그인</h1>

        {/* 로그인 폼 */}
        <div className="space-y-4">
          <Input
            name="username"
            label="아이디"
            value={username}
            onChange={handleChange}
          />

          <Input
            name="password"
            type="password"
            label="비밀번호"
            value={password}
            onChange={handleChange}
          />

          <Button onClick={handleLogin} className="w-full">
            로그인
          </Button>
        </div>

        {/* 회원가입 페이지 이동 링크 */}
        <div className="text-center mt-4">
          <button
            onClick={() => navigate("/signup")}
            className="text-sm text-gray-600 hover:underline"
          >
            계정이 없으신가요? 회원가입
          </button>
        </div>
      </section>
    </main>
  );
}
