import React, { useState } from "react";
import fastapi from "../../lib/fastapi";
import Input from "../atoms/Input";
import Button from "../atoms/Button";

export default function SignupView({ onDone }) {
  const [form, setForm] = useState({ username: "", password1: "", password2: "", email: "" });
  const [msg, setMsg] = useState(null);
  const [err, setErr] = useState(null);


  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const submit = (e) => {
    e.preventDefault();
    setMsg(null);
    setErr(null);
    fastapi("post", "/api/user/create", form, () => {
      setMsg("회원가입 완료! 로그인 해주세요.");
      setTimeout(onDone, 1000);
    }, (e) => setErr(e.response?.data?.detail || "오류"));
  };

  return (
    <section className="bg-white rounded-2xl shadow p-8 space-y-4">
      <h2 className="text-xl font-bold text-indigo-600 text-center">Sign Up</h2>
      <form className="space-y-3" onSubmit={submit}>
        <Input label="Username" name="username" value={form.username} onChange={handleChange} required />
        <Input label="Password" type="password" name="password1" value={form.password1} onChange={handleChange} required />
        <Input label="Confirm Password" type="password" name="password2" value={form.password2} onChange={handleChange} required />
        <Input label="Email" type="email" name="email" value={form.email} onChange={handleChange} />
        <Button className="w-full" type="submit">Sign Up</Button>
        {msg && <p className="text-green-600 text-sm text-center">{msg}</p>}
        {err && <p className="text-red-500 text-sm text-center">{err}</p>}
      </form>
    </section>
  );
}