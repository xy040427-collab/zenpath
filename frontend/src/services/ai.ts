import api from './api';
import type { ChatMessage, ChatSession, Preference } from '../types';

export async function sendMessage(params: {
  sessionId: string;
  content: string;
  context?: Preference;
}): Promise<ChatMessage> {
  const { data } = await api.post('/ai/chat', params);
  return data.data;
}

export async function createChatSession(userId: string): Promise<ChatSession> {
  const { data } = await api.post('/ai/sessions', { userId });
  return data.data;
}

export async function getChatHistory(sessionId: string): Promise<ChatMessage[]> {
  const { data } = await api.get(`/ai/sessions/${sessionId}/messages`);
  return data.data;
}

export async function getChatSessions(userId: string): Promise<ChatSession[]> {
  const { data } = await api.get('/ai/sessions', { params: { userId } });
  return data.data;
}
