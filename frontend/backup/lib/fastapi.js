// fastapi.js – React‑friendly fetch helper (Vanilla JS)
//------------------------------------------------------
// 사용법 예시:
//   import fastapi from "./lib/fastapi";
//   fastapi("login", "/api/user/login", { username, password }, cb, errCb);
//   fastapi("post",  "/api/user/create", userObj, cb, errCb);
//   fastapi("get",   "/api/ping", {}, cb, errCb);
//
// 환경변수
//   .env (또는 .env.local)
//     VITE_SERVER_URL=http://localhost:8000
//
// notice: debug=true 이면 콘솔에 요청·응답 로그 출력
//------------------------------------------------------
import qs from "qs";

export default function fastapi(
    operation,
    url,
    params = {},
    success_callback,
    failure_callback,
    debug = true
) {
    let method = operation;
    let content_type = "application/json";
    let body = JSON.stringify(params);

    // 로그인 전용: x-www-form-urlencoded
    if (operation === "login") {
        method = "post";
        content_type = "application/x-www-form-urlencoded";
        body = qs.stringify(params);
    }

    let _url = import.meta.env.VITE_SERVER_URL + url;
    if (method === "get") {
        _url += "?" + new URLSearchParams(params);
    }

    const options = {
        method,
        headers: { "Content-Type": content_type },
    };

    const token = localStorage.getItem("access_token");
    if (token) options.headers["Authorization"] = "Bearer " + token;
    if (method !== "get") options.body = body;

    /* ---------- DEBUG: 요청 ---------- */
    if (debug) {
        console.groupCollapsed(`[fastapi] ${method.toUpperCase()} ${_url}`);
        console.log("Headers:", options.headers);
        if (method !== "get") console.log("Body:", body);
        console.groupEnd();
    }
    /* --------------------------------- */

    fetch(_url, options)
        .then(async (res) => {
            let json = null;
            try {
                json = await res.clone().json();
            } catch (_) {
                /* no json */
            }

            /* ---------- DEBUG: 응답 ---------- */
            if (debug) {
                console.groupCollapsed(
                    `[fastapi] ↩ ${res.status} ${res.statusText}`
                );
                console.log("URL:", res.url);
                console.log("Headers:", Object.fromEntries(res.headers.entries()));
                if (json) console.log("Body:", json);
                console.groupEnd();
            }
            /* -------------------------------- */

            if (res.status === 204) {
                success_callback?.();
                return;
            }

            if (res.ok) {
                success_callback?.(json);
            } else if (operation !== "login" && res.status === 401) {
                localStorage.removeItem("access_token");
                alert("로그인이 필요합니다. 다시 로그인해 주세요.");
                failure_callback?.({ detail: "Unauthorized" });
            } else {
                failure_callback
                    ? failure_callback(json)
                    : alert(JSON.stringify(json));
            }
        })
        .catch((err) => {
            if (debug) console.error("[fastapi] Network Error:", err);
            alert("Network Error: " + err);
        });
}
