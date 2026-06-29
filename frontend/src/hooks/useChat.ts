import { useState, useCallback } from 'react';
import type { ChatMessage, ChatSession } from '../types';

const API_BASE = '/api/chat';
const API_TIMEOUT_MS = 30_000;

interface SessionListItem {
  id: string;
  title: string;
  updated_at: string;
  message_count: number;
}

interface SendResponse {
  success: boolean;
  answer: string;
  intent?: string;
  answerable?: boolean;
  sources?: Array<{
    title: string;
    source_url: string;
    doc_type: string;
    school_name?: string;
  }>;
  structured?: Record<string, unknown>;
}

export function useChat() {
  const [session, setSession] = useState<ChatSession | null>(null);
  const [sessions, setSessions] = useState<SessionListItem[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [userLevel] = useState<'free' | 'basic' | 'advanced' | 'premium'>('free');

  // Fetch session list
  const fetchSessions = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/sessions`);
      if (!res.ok) throw new Error('获取会话列表失败');
      const data = await res.json();
      setSessions(data?.sessions ?? []);
    } catch (err) {
      console.error('fetchSessions error:', err);
    }
  }, []);

  // Create a new session
  const createSession = useCallback(async (title?: string) => {
    try {
      const res = await fetch(`${API_BASE}/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(title ? { title } : {}),
      });
      if (!res.ok) throw new Error('创建会话失败');
      const data = await res.json();
      const newSession: ChatSession = {
        id: data.session_id,
        userId: '',
        title: title || data.title || '新对话',
        messages: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
      setSession(newSession);
      setMessages([]);
      setError(null);
      // Refresh session list
      await fetchSessions();
      return newSession;
    } catch (err) {
      setError('创建会话失败，请稍后重试');
      return null;
    }
  }, [fetchSessions]);

  // Switch to a session and load its messages
  const switchSession = useCallback(async (sessionId: string) => {
    setLoading(true);
    setError(null);
    try {
      const [sessionRes, messagesRes] = await Promise.all([
        fetch(`${API_BASE}/sessions/${sessionId}`),
        fetch(`${API_BASE}/sessions/${sessionId}/messages`),
      ]);
      if (!sessionRes.ok || !messagesRes.ok) throw new Error('获取会话失败');

      const sessionJson = await sessionRes.json();
      const messagesJson = await messagesRes.json();
      const sessionData = sessionJson?.session ?? sessionJson;
      const messagesData = messagesJson?.messages ?? [];

      const loadedSession: ChatSession = {
        id: sessionData.id ?? sessionId,
        userId: sessionData.user_id ?? '',
        title: sessionData.title ?? '对话',
        messages: [],
        message_count: sessionData.message_count ?? (messagesData as ChatMessage[]).length,
        createdAt: sessionData.created_at ?? new Date().toISOString(),
        updatedAt: sessionData.updated_at ?? new Date().toISOString(),
      };

      setSession(loadedSession);
      setMessages(messagesData);
    } catch (err) {
      setError('加载会话失败');
    } finally {
      setLoading(false);
    }
  }, []);

  // Delete a session
  const deleteSession = useCallback(async (sessionId: string) => {
    try {
      const res = await fetch(`${API_BASE}/sessions/${sessionId}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('删除会话失败');
      if (session?.id === sessionId) {
        setSession(null);
        setMessages([]);
      }
      await fetchSessions();
    } catch (err) {
      setError('删除会话失败');
    }
  }, [session, fetchSessions]);

  // Send a message in the current session
  const sendMessage = useCallback(async (content: string, useRag = true) => {
    if (!content.trim()) return null;
    // Auto-create session if needed
    let currentSession = session;
    if (!currentSession) {
      const ns = await createSession(content.slice(0, 30).trim());
      if (!ns) return null;
      currentSession = ns;
    }

    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setSending(true);
    setError(null);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT_MS);

    try {
      const response = await fetch(`${API_BASE}/sessions/${currentSession.id}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: content,
          use_rag: useRag,
          use_recommendation_context: true,
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error('网络连接失败，请稍后重试');
      }

      const data: SendResponse = await response.json();

      if (!data.success) {
        throw new Error('服务器返回异常，请稍后重试');
      }

      const assistantMessage: ChatMessage = {
        id: `msg_${Date.now() + 1}`,
        role: 'assistant',
        content: data.answer,
        timestamp: new Date().toISOString(),
        sources: data.sources ?? [],
        answerable: data.answerable ?? true,
        intent: data.intent,
        structured: data.structured,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      // Refresh session list to update message_count
      fetchSessions();
      return assistantMessage;
    } catch (err) {
      let message = '网络连接失败，请稍后重试';
      if (err instanceof DOMException && err.name === 'AbortError') {
        message = '请求超时，请稍后重试';
      } else if (err instanceof TypeError && err.message === 'Failed to fetch') {
        message = '网络连接失败，请稍后重试';
      }
      setError(message);
      return null;
    } finally {
      clearTimeout(timeoutId);
      setSending(false);
    }
  }, [session, fetchSessions]);

  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  // Retry last user message
  const retryLastMessage = useCallback(async () => {
    const lastUserMsg = [...messages].reverse().find((m) => m.role === 'user');
    if (lastUserMsg) {
      // Remove the last assistant message if there was an error
      setMessages((prev) => {
        const last = prev[prev.length - 1];
        if (last?.role === 'assistant') {
          return prev.slice(0, -1);
        }
        return prev;
      });
      await sendMessage(lastUserMsg.content);
    }
  }, [messages, sendMessage]);

  return {
    session,
    sessions,
    messages,
    loading,
    sending,
    error,
    userLevel,
    sendMessage,
    clearChat,
    createSession,
    switchSession,
    deleteSession,
    fetchSessions,
    retryLastMessage,
    setSession,
  };
}
