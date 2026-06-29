import api from './api';
import type { Preference, Recommendation } from '../types';

export async function submitApplication(preference: Preference): Promise<Recommendation> {
  const { data } = await api.post('/applications', preference);
  return data.data;
}

export async function getApplication(id: string): Promise<Recommendation> {
  const { data } = await api.get(`/applications/${id}`);
  return data.data;
}

export async function getApplicationHistory(userId: string): Promise<Recommendation[]> {
  const { data } = await api.get(`/applications`, { params: { userId } });
  return data.data;
}
