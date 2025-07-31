/**
 * Plaid Integration Types
 */

export interface PlaidConfig {
  environment: 'sandbox' | 'development' | 'production';
  publicKey: string;
  clientName: string;
  countryCodes: string[];
  language: string;
  products: PlaidProduct[];
}

export type PlaidProduct = 
  | 'transactions' 
  | 'auth' 
  | 'identity' 
  | 'assets' 
  | 'liabilities' 
  | 'investments';

export interface PlaidLinkSuccess {
  publicToken: string;
  metadata: PlaidLinkMetadata;
}

export interface PlaidLinkMetadata {
  institution: {
    name: string;
    institution_id: string;
  };
  accounts: PlaidAccount[];
  link_session_id: string;
  transfer_status?: string;
}

export interface PlaidAccount {
  id: string;
  name: string;
  type: string;
  subtype: string;
  mask: string;
}

export interface PlaidTransaction {
  account_id: string;
  amount: number;
  iso_currency_code: string;
  unofficial_currency_code?: string;
  category: string[];
  category_id: string;
  date: string;
  authorized_date?: string;
  location: PlaidLocation;
  name: string;
  merchant_name?: string;
  payment_meta: PlaidPaymentMeta;
  pending: boolean;
  pending_transaction_id?: string;
  account_owner?: string;
  transaction_id: string;
  transaction_type: string;
}

export interface PlaidLocation {
  address?: string;
  city?: string;
  region?: string;
  postal_code?: string;
  country?: string;
  lat?: number;
  lon?: number;
  store_number?: string;
}

export interface PlaidPaymentMeta {
  by_order_of?: string;
  payee?: string;
  payer?: string;
  payment_method?: string;
  payment_processor?: string;
  ppd_id?: string;
  reason?: string;
  reference_number?: string;
}

export interface PlaidBalance {
  available?: number;
  current: number;
  limit?: number;
  iso_currency_code: string;
  unofficial_currency_code?: string;
}

export interface PlaidAccountBalance {
  account_id: string;
  balances: PlaidBalance;
  mask: string;
  name: string;
  official_name: string;
  subtype: string;
  type: string;
}

export interface PlaidWebhookData {
  webhook_type: string;
  webhook_code: string;
  item_id: string;
  error?: PlaidError;
  new_transactions?: number;
  removed_transactions?: string[];
}

export interface PlaidError {
  error_type: string;
  error_code: string;
  error_message: string;
  display_message?: string;
  request_id: string;
  causes?: any[];
  status?: number;
  documentation_url?: string;
  suggested_action?: string;
}