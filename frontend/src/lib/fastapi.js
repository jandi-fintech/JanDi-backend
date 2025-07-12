// fastapi.js – React 친화적인 fetch 헬퍼 (바닐라 JS)
// ------------------------------------------------------
// 사용 예시:
//   import fastapi from "./lib/fastapi";
//   // 로그인 (x-www-form-urlencoded 사용)
//   fastapi("login", "/api/user/login", { username, password }, onSuccess, onError);
//   // 사용자 생성 (POST JSON)
//   fastapi("post",   "/api/user/create",   userObj,             onSuccess, onError);
//   // 서버 핑 (GET)
//   fastapi("get",    "/api/ping",         {},                  onSuccess, onError);
//
// 환경 변수 (.env 또는 .env.local):
//   VITE_SERVER_URL=http://localhost:8000
//
// 디버그 모드:
//   debug=true 이면 요청·응답 상세 로그를 콘솔에 출력합니다.
// ------------------------------------------------------
import qs from "qs";

export default function fastapi(
    operation,
    url,
    params = {},
    success_callback,
    failure_callback,
    debug = true
) {
    // HTTP 메서드 및 기본 헤더/바디 설정
    let method = operation;
    let content_type = "application/json";
    let body = JSON.stringify(params);

    // 로그인 전용 처리: x-www-form-urlencoded
    if (operation === "login") {
        method = "post";
        content_type = "application/x-www-form-urlencoded";
        body = qs.stringify(params);
    }

    // 전체 URL 생성
    const baseUrl = import.meta.env.VITE_SERVER_URL || "http://localhost:8000";
    let _url = baseUrl + url;

    // GET 요청 시 쿼리 파라미터 추가
    if (method === "get") {
        _url += "?" + new URLSearchParams(params);
    }

    // fetch 옵션 준비
    const options = {
        method,
        headers: { "Content-Type": content_type },
    };

    // localStorage에서 JWT 토큰 가져와 Authorization 헤더에 Bearer 스킴으로 설정
    const token = localStorage.getItem("access_token");
    if (token) {
        options.headers["Authorization"] = "Bearer " + token;
    }

    // GET이 아닐 때 바디 포함
    if (method !== "get") {
        options.body = body;
    }

    // --- 디버그: 요청 로그 ---
    if (debug) {
        console.groupCollapsed(`[fastapi] ${method.toUpperCase()} ${_url}`);
        console.log("Headers:", options.headers);
        if (method !== "get") console.log("Body:", body);
        console.groupEnd();
    }
    // ----------------------

    // fetch 실행
    fetch(_url, options)
        .then(async (res) => {
            let json = null;
            try {
                json = await res.clone().json();
            } catch (_) {
                // JSON 응답 없음
            }

            // --- 디버그: 응답 로그 ---
            if (debug) {
                console.groupCollapsed(
                    `[fastapi] ↩ ${res.status} ${res.statusText}`
                );
                console.log("URL:", res.url);
                console.log("Headers:", Object.fromEntries(res.headers.entries()));
                if (json) console.log("Body:", json);
                console.groupEnd();
            }
            // ------------------------

            // 내용 없음(204) 처리
            if (res.status === 204) {
                success_callback?.();
                return;
            }

            // 성공 처리
            if (res.ok) {
                success_callback?.(json);
            }
            // 로그인 제외 401 Unauthorized 처리
            else if (operation !== "login" && res.status === 401) {
                localStorage.removeItem("access_token");
                alert("로그인이 필요합니다. 다시 로그인해 주세요.");
                failure_callback?.({ detail: "Unauthorized" });
            }
            // 기타 에러 처리
            else {
                if (failure_callback) {
                    failure_callback(json);
                } else {
                    alert(JSON.stringify(json));
                }
            }
        })
        .catch((err) => {
            // 네트워크 오류 처리
            if (debug) console.error("[fastapi] Network Error:", err);
            alert("Network Error: " + err);
        });
}
