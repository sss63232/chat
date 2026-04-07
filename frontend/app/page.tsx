"use client";

import { useEffect, useMemo, useState } from "react";

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

const BACKEND_OPTIONS = {
  fastapi: {
    label: "FastAPI",
    baseUrl: process.env.NEXT_PUBLIC_FASTAPI_API_BASE || "http://localhost:8000"
  },
  spring: {
    label: "Spring Boot",
    baseUrl: process.env.NEXT_PUBLIC_SPRING_API_BASE || "http://localhost:8080"
  }
} as const;

type BackendKey = keyof typeof BACKEND_OPTIONS;

const DEFAULT_BACKEND = (
  process.env.NEXT_PUBLIC_DEFAULT_BACKEND === "spring" ? "spring" : "fastapi"
) as BackendKey;
const BACKEND_STORAGE_KEY = "chat-backend-target";

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
  const [backend, setBackend] = useState<BackendKey>(DEFAULT_BACKEND);

  const activeSession = useMemo(
    () => sessions.find((s) => s.id === activeSessionId) || null,
    [sessions, activeSessionId]
  );
  const apiBase = BACKEND_OPTIONS[backend].baseUrl;

  useEffect(() => {
    const savedBackend = window.localStorage.getItem(BACKEND_STORAGE_KEY);
    if (savedBackend === "fastapi" || savedBackend === "spring") {
      setBackend(savedBackend);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem(BACKEND_STORAGE_KEY, backend);
  }, [backend]);

  const clearError = () => setError(null);

  const resetConversationState = () => {
    setSessions([]);
    setActiveSessionId(null);
    setMessages([]);
    setError(null);
  };

  const loadSessions = async () => {
    clearError();
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/sessions?userId=${encodeURIComponent(userId)}`);
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
      const res = await fetch(`${apiBase}/api/sessions`, {
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
      const res = await fetch(`${apiBase}/api/sessions/${sessionId}/messages`);
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
      await sendMessageStreaming();
    } catch (err) {
      setError(err instanceof Error ? err.message : "未知錯誤");
    } finally {
      setLoading(false);
    }
  };

  const sendMessageStreaming = async () => {
    if (!activeSessionId) {
      return;
    }
    const formData = new FormData();
    formData.append("content", content);
    if (file) {
      formData.append("file", file);
    }

    const tempUserId = `temp-user-${Date.now()}`;
    const tempAssistantId = `temp-assistant-${Date.now()}`;
    const now = new Date().toISOString();
    try {
      setMessages((prev) => [
        ...prev,
        {
          id: tempUserId,
          sessionId: activeSessionId,
          role: "user",
          content,
          attachmentUrls: file ? [file.name] : [],
          createdAt: now
        },
        {
          id: tempAssistantId,
          sessionId: activeSessionId,
          role: "assistant",
          content: "",
          attachmentUrls: [],
          createdAt: now
        }
      ]);

      setContent("");
      setFile(null);

      const res = await fetch(`${apiBase}/api/chat/${activeSessionId}/stream`, {
        method: "POST",
        body: formData
      });

      if (!res.ok || !res.body) {
        throw new Error("串流回覆失敗");
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";
      let eventName = "message";
      let dataLines: string[] = [];

      const flushEvent = () => {
        if (dataLines.length === 0) {
          eventName = "message";
          return;
        }
        const data = dataLines.join("\n");
        if (eventName === "delta") {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === tempAssistantId
                ? { ...msg, content: msg.content + data }
                : msg
            )
          );
        } else if (eventName === "done") {
          const payload = JSON.parse(data) as SendMessageResponse;
          setMessages((prev) =>
            prev.map((msg) => {
              if (msg.id === tempUserId) {
                return {
                  ...msg,
                  id: payload.userMessageId,
                  attachmentUrls: payload.attachmentUrls
                };
              }
              if (msg.id === tempAssistantId) {
                return {
                  ...msg,
                  id: payload.assistantMessageId,
                  content: payload.assistantContent
                };
              }
              return msg;
            })
          );
        }
        dataLines = [];
        eventName = "message";
      };

      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          break;
        }
        buffer += decoder.decode(value, { stream: true });
        let lineEnd = buffer.indexOf("\n");
        while (lineEnd !== -1) {
          const rawLine = buffer.slice(0, lineEnd);
          buffer = buffer.slice(lineEnd + 1);
          const line = rawLine.replace(/\r$/, "");
          if (line === "") {
            flushEvent();
          } else if (line.startsWith("event:")) {
            eventName = line.slice("event:".length).trim();
          } else if (line.startsWith("data:")) {
            dataLines.push(line.slice("data:".length).trimStart());
          }
          lineEnd = buffer.indexOf("\n");
        }
      }

      flushEvent();
    } catch (err) {
      setMessages((prev) =>
        prev.filter((msg) => msg.id !== tempUserId && msg.id !== tempAssistantId)
      );
      throw err;
    }
  };

  return (
    <div className="container">
      <div className="hero">
        <h1>AI Chat Sessions</h1>
        <p>可切換 FastAPI / Spring Boot 的聊天前端</p>
      </div>

      <div className="layout">
        <div className="panel">
          <div className="backend-bar">
            <div>
              <div className="section-title">後端目標</div>
              <div className="muted">目前連線到 {BACKEND_OPTIONS[backend].label}</div>
            </div>
            <div className="backend-selector">
              <select
                className="select"
                value={backend}
                disabled={loading}
                onChange={(e) => {
                  const nextBackend = e.target.value as BackendKey;
                  setBackend(nextBackend);
                  resetConversationState();
                }}
              >
                {Object.entries(BACKEND_OPTIONS).map(([key, option]) => (
                  <option key={key} value={key}>
                    {option.label}
                  </option>
                ))}
              </select>
              <div className="backend-hint">{apiBase}</div>
            </div>
          </div>

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
