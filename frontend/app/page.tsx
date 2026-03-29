"use client";

import { useMemo, useState } from "react";

type ChatSession = {
  id: string;
  userId: string;
  title: string;
  createdAt: string;
};

type ChatMessage = {
  id: string;
  sessionId: string;
  role: "user" | "assistant";
  content: string;
  attachmentUrls: string[];
  createdAt: string;
};

type SendMessageResponse = {
  sessionId: string;
  userMessageId: string;
  assistantMessageId: string;
  assistantContent: string;
  attachmentUrls: string[];
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8080";

export default function Home() {
  const [userId, setUserId] = useState("u1");
  const [title, setTitle] = useState("");
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [content, setContent] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activeSession = useMemo(
    () => sessions.find((s) => s.id === activeSessionId) || null,
    [sessions, activeSessionId]
  );

  const clearError = () => setError(null);

  const loadSessions = async () => {
    clearError();
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/sessions?userId=${encodeURIComponent(userId)}`);
      if (!res.ok) {
        throw new Error("讀取會話失敗");
      }
      const data: ChatSession[] = await res.json();
      setSessions(data);
      if (data.length > 0 && !activeSessionId) {
        setActiveSessionId(data[0].id);
        await loadMessages(data[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "未知錯誤");
    } finally {
      setLoading(false);
    }
  };

  const createSession = async () => {
    if (!userId.trim() || !title.trim()) {
      setError("請輸入 userId 與標題");
      return;
    }
    clearError();
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ userId, title })
      });
      if (!res.ok) {
        throw new Error("建立會話失敗");
      }
      const session: ChatSession = await res.json();
      setSessions((prev) => [session, ...prev]);
      setActiveSessionId(session.id);
      setMessages([]);
      setTitle("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "未知錯誤");
    } finally {
      setLoading(false);
    }
  };

  const loadMessages = async (sessionId: string) => {
    clearError();
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/sessions/${sessionId}/messages`);
      if (!res.ok) {
        throw new Error("讀取訊息失敗");
      }
      const data: ChatMessage[] = await res.json();
      setMessages(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "未知錯誤");
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!activeSessionId) {
      setError("請先選擇會話");
      return;
    }
    if (!content.trim()) {
      setError("請輸入訊息內容");
      return;
    }
    clearError();
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("content", content);
      if (file) {
        formData.append("file", file);
      }
      const res = await fetch(`${API_BASE}/api/chat/${activeSessionId}/send`, {
        method: "POST",
        body: formData
      });
      if (!res.ok) {
        throw new Error("送出訊息失敗");
      }
      const data: SendMessageResponse = await res.json();
      setContent("");
      setFile(null);
      await loadMessages(data.sessionId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "未知錯誤");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <div className="hero">
        <h1>AI Chat Sessions</h1>
        <p>Spring Boot + MongoDB + MinIO 的最小可用前端</p>
      </div>

      <div className="layout">
        <div className="panel">
          <div className="section-title">使用者與會話</div>
          <label className="muted">User ID</label>
          <input
            className="input"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            placeholder="例如 u1"
          />
          <button className="button secondary" onClick={loadSessions} disabled={loading}>
            讀取會話
          </button>

          <div style={{ marginTop: 16 }}>
            <label className="muted">建立新會話</label>
            <input
              className="input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="會話標題"
            />
            <button className="button" onClick={createSession} disabled={loading}>
              建立會話
            </button>
          </div>

          <div style={{ marginTop: 16 }} className="section-title">
            會話列表
          </div>
          <div className="list">
            {sessions.length === 0 && <div className="muted">尚無會話</div>}
            {sessions.map((session) => (
              <div
                key={session.id}
                className={`card ${session.id === activeSessionId ? "active" : ""}`}
                onClick={() => {
                  setActiveSessionId(session.id);
                  loadMessages(session.id);
                }}
              >
                <div>{session.title}</div>
                <div className="muted">{session.createdAt}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <div className="section-title">
            {activeSession ? `對話：${activeSession.title}` : "請先選擇會話"}
          </div>
          <div className="messages">
            {messages.length === 0 && (
              <div className="muted">沒有訊息，開始聊天吧。</div>
            )}
            {messages.map((msg) => (
              <div key={msg.id} className={`message ${msg.role}`}>
                <div className="muted">{msg.role}</div>
                <div>{msg.content}</div>
                {msg.attachmentUrls && msg.attachmentUrls.length > 0 && (
                  <div className="attachments">
                    {msg.attachmentUrls.map((url) => (
                      <span key={url} className="tag">
                        {url}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>

          <div style={{ marginTop: 16 }}>
            <label className="muted">訊息內容</label>
            <textarea
              className="textarea"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="輸入你要傳給 AI 的內容"
            />
            <label className="muted">附件（選填）</label>
            <input
              className="file"
              type="file"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
            />
            <button className="button" onClick={sendMessage} disabled={loading}>
              送出訊息
            </button>
          </div>

          {error && <div className="error" style={{ marginTop: 12 }}>{error}</div>}
        </div>
      </div>
    </div>
  );
}
