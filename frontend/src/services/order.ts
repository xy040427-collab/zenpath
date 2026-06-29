import api from './api';
import type { Order, PricingPlan } from '../types';

export async function createOrder(params: {
  userId: string;
  plan: PricingPlan;
}): Promise<Order> {
  const { data } = await api.post('/orders', params);
  return data.data;
}

export async function getOrder(id: string): Promise<Order> {
  const { data } = await api.get(`/orders/${id}`);
  return data.data;
}

export async function getOrderHistory(userId: string): Promise<Order[]> {
  const { data } = await api.get('/orders', { params: { userId } });
  return data.data;
}

export async function cancelOrder(id: string): Promise<Order> {
  const { data } = await api.post(`/orders/${id}/cancel`);
  return data.data;
}
