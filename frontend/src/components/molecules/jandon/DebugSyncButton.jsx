import React from 'react';
import axios from 'axios';
import Button from '../../atoms/Button';
import { useSelector } from 'react-redux';

export default function DebugSyncButton() {
    const FIN_SERVER_URL = useSelector(state => state.FIN_SERVER_URL);

    // Axios 인스턴스 (HttpOnly 쿠키 포함)
    const api = axios.create({
        baseURL: FIN_SERVER_URL + '/api/debug',
        withCredentials: true,
    });

    const triggerSync = async () => {
        try {
            // POST /api/debug/sync-now 호출
            const { data } = await api.post('/sync-now');
            console.log('Sync queued:', data);
            alert(`작업이 큐에 등록되었습니다.\nTask ID: ${data.task_id}`);
        } catch (error) {
            console.error('Sync failed:', error.response || error);
            alert(`동기화 요청 중 오류가 발생했습니다:\n${error.response?.data?.detail || error.message}`);
        }
    };

    return (
        <div>
            <Button onClick={triggerSync} className="bg-red-500 text-white">
                지금 동기화 실행
            </Button>
        </div>
    );
}
