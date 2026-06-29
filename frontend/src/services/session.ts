import api from './api';
import type { User } from '../types';

export async function createSession(phone: string): Promise<User> {
  const { data } = await api.post('/sessions', { phone });
  return data.data;
}

export async function getSession(id: string): Promise<User> {
  const { data } = await api.get(`/sessions/${id}`);
  return data.data;
}

export async function updateSession(id: string, updates: Partial<User>): Promise<User> {
  const { data } = await api.patch(`/sessions/${id}`, updates);
  return data.data;
}
