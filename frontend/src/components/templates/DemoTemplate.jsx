// AppRoutes.jsx
import React, { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";

import LoginPage from "../molecules/common/LoginPage";
import SignupPage from "../molecules/common/SignupPage";
import Investments from "../organisms/Investments";
import Accounts from "../organisms/Accounts";
import Jandon from "../organisms/Jandon";
import Divider from "../atoms/Divider";

import { useSelector } from "react-redux";
import axios from "axios";

const useApi = (baseURL) =>
  axios.create({
    baseURL,
    withCredentials: true,
  });

export default function DemoTemplate() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

function Dashboard() {
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
  return (
    <section className="bg-white rounded-2xl shadow p-8 space-y-8">
      <h2 className="text-2xl font-bold text-indigo-700 text-center mb-6">API Dashboard</h2>
      <Investments />
      <Divider />
      <Accounts />
      <Divider />
      <Jandon />
    </section>
  );
}