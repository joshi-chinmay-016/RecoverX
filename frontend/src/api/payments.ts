import { apiClient } from './client';
import { PaymentListResponse, PaymentItem } from '@/types/payment';

export async function listPayments(
  status?: string,
  page: number = 1,
  pageSize: number = 20
): Promise<PaymentListResponse> {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  params.append('page', page.toString());
  params.append('page_size', pageSize.toString());

  return apiClient<PaymentListResponse>(`/payments?${params.toString()}`);
}

export async function getPayment(paymentId: string): Promise<PaymentItem> {
  return apiClient<PaymentItem>(`/payments/${paymentId}`);
}

export async function listRecoveryCases(
  status?: string,
  page: number = 1,
  pageSize: number = 20
): Promise<{ total: number; page: number; page_size: number; cases: any[] }> {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  params.append('page', page.toString());
  params.append('page_size', pageSize.toString());

  return apiClient(`/recovery/cases?${params.toString()}`);
}
