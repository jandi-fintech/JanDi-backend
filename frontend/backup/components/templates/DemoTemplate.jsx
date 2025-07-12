import React, { useState } from "react";
import SignupView from "../molecules/SignupView";
import LoginView from "../molecules/LoginView";
import Dashboard from "../organisms/Dashboard";

export default function DemoTemplate() {
  // 로그인 상태. localStorage 에 토큰 존재 여부로 간단 판정
  const [loggedIn, setLoggedIn] = useState(
    Boolean(localStorage.getItem("access_token"))
  );
  const [view, setView] = useState(loggedIn ? "dashboard" : "signup");

  const handleLogin = () => {
    setLoggedIn(true);
    setView("dashboard");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 p-4">
      <div className="max-w-4xl mx-auto space-y-6">
        {view === "signup" && <SignupView onDone={() => setView("login")} />}
        {view === "login" && <LoginView onLoginSuccess={handleLogin} />}
        {view === "dashboard" && <Dashboard />}
      </div>
    </div>
  );
}