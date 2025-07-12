import React, { useState } from "react";
import fastapi from "../../lib/fastapi";
import Input from "../atoms/Input";
import Button from "../atoms/Button";

export default function LoginView({ onLoginSuccess }) {
  const [form, setForm] = useState({ username: "", password: "" });
  const [msg, setMsg] = useState(null);
  const [err, setErr] = useState(null);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const submit = (e) => {
    e.preventDefault();
    setMsg(null);
    setErr(null);
    fastapi("login", "/api/user/login", form, (json) => {
      localStorage.setItem("access_token", json.access_token);
      localStorage.setItem("username", json.username);
      setMsg("로그인 성공!");
      setTimeout(onLoginSuccess, 500);
    }, (e) => setErr(e.response?.data?.detail || "오류"));
  };

  return (
    <section className="bg-white rounded-2xl shadow p-8 space-y-4">
      <h2 className="text-xl font-bold text-indigo-600 text-center">Log In</h2>
      <form className="space-y-3" onSubmit={submit}>
        <Input label="Username" name="username" value={form.username} onChange={handleChange} required />
        <Input label="Password" type="password" name="password" value={form.password} onChange={handleChange} required />
        <Button className="w-full" type="submit">Log In</Button>
        {msg && <p className="text-green-600 text-sm text-center">{msg}</p>}
        {err && <p className="text-red-500 text-sm text-center">{err}</p>}
      </form>
    </section>
  );
}