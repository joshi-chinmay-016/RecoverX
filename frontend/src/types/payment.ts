export type PaymentStatus =
  | 'CREATED'
  | 'AUTHORIZED'
  | 'CAPTURED'
  | 'FAILED'
  | 'REFUNDED';

export interface PaymentAttempt {
  id?: string;
  attempt_number: number;
  status: string;
  method: string;
  failure_code?: string | null;
  failure_description?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface PaymentItem {
  id: string;
  razorpay_payment_id: string;
  razorpay_order_id?: string;
  merchant_id: string;
  customer_id: string;
  amount_minor: number;
  currency: string;
  status: PaymentStatus;
  method: string;
  failure_code?: string | null;
  failure_description?: string | null;
  created_at: string;
  attempts?: PaymentAttempt[];
}

export interface PaymentListResponse {
  payments: PaymentItem[];
  total: number;
  page: number;
  page_size: number;
}
