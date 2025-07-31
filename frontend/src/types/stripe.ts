/**
 * Stripe Payment Processing Types
 */

export interface StripeConfig {
  publishableKey: string;
  merchantId?: string;
  urlScheme?: string;
}

export interface StripeSubscription {
  id: string;
  object: 'subscription';
  application_fee_percent?: number;
  cancel_at?: number;
  cancel_at_period_end: boolean;
  canceled_at?: number;
  created: number;
  current_period_end: number;
  current_period_start: number;
  customer: string;
  description?: string;
  discount?: any;
  ended_at?: number;
  items: StripeSubscriptionItem[];
  latest_invoice?: string;
  livemode: boolean;
  metadata: Record<string, string>;
  plan: StripePlan;
  quantity: number;
  start: number;
  status: StripeSubscriptionStatus;
  tax_percent?: number;
  trial_end?: number;
  trial_start?: number;
}

export type StripeSubscriptionStatus = 
  | 'incomplete'
  | 'incomplete_expired'
  | 'trialing'
  | 'active'
  | 'past_due'
  | 'canceled'
  | 'unpaid';

export interface StripeSubscriptionItem {
  id: string;
  object: 'subscription_item';
  created: number;
  metadata: Record<string, string>;
  plan: StripePlan;
  quantity: number;
  subscription: string;
}

export interface StripePlan {
  id: string;
  object: 'plan';
  active: boolean;
  aggregate_usage?: string;
  amount: number;
  amount_decimal?: string;
  billing_scheme: 'per_unit' | 'tiered';
  created: number;
  currency: string;
  interval: 'day' | 'week' | 'month' | 'year';
  interval_count: number;
  livemode: boolean;
  metadata: Record<string, string>;
  nickname?: string;
  product: string;
  tiers?: StripePlanTier[];
  tiers_mode?: 'graduated' | 'volume';
  transform_usage?: any;
  trial_period_days?: number;
  usage_type: 'licensed' | 'metered';
}

export interface StripePlanTier {
  flat_amount?: number;
  flat_amount_decimal?: string;
  unit_amount?: number;
  unit_amount_decimal?: string;
  up_to?: number;
}

export interface StripeCustomer {
  id: string;
  object: 'customer';
  account_balance?: number;
  address?: StripeAddress;
  balance: number;
  created: number;
  currency?: string;
  default_source?: string;
  delinquent: boolean;
  description?: string;
  discount?: any;
  email?: string;
  invoice_prefix?: string;
  invoice_settings: StripeInvoiceSettings;
  livemode: boolean;
  metadata: Record<string, string>;
  name?: string;
  phone?: string;
  preferred_locales?: string[];
  shipping?: StripeShipping;
  sources?: any;
  subscriptions?: any;
  tax_exempt?: 'none' | 'exempt' | 'reverse';
  tax_ids?: any;
}

export interface StripeAddress {
  city?: string;
  country?: string;
  line1?: string;
  line2?: string;
  postal_code?: string;
  state?: string;
}

export interface StripeInvoiceSettings {
  custom_fields?: StripeCustomField[];
  default_payment_method?: string;
  footer?: string;
}

export interface StripeCustomField {
  name: string;
  value: string;
}

export interface StripeShipping {
  address: StripeAddress;
  carrier?: string;
  name: string;
  phone?: string;
  tracking_number?: string;
}

export interface StripePaymentIntent {
  id: string;
  object: 'payment_intent';
  amount: number;
  amount_capturable?: number;
  amount_received?: number;
  application?: string;
  application_fee_amount?: number;
  canceled_at?: number;
  cancellation_reason?: string;
  capture_method: 'automatic' | 'manual';
  charges?: any;
  client_secret: string;
  confirmation_method: 'automatic' | 'manual';
  created: number;
  currency: string;
  customer?: string;
  description?: string;
  invoice?: string;
  last_payment_error?: any;
  livemode: boolean;
  metadata: Record<string, string>;
  next_action?: any;
  on_behalf_of?: string;
  payment_method?: string;
  payment_method_options?: any;
  payment_method_types: string[];
  receipt_email?: string;
  setup_future_usage?: 'on_session' | 'off_session';
  shipping?: StripeShipping;
  source?: string;
  statement_descriptor?: string;
  statement_descriptor_suffix?: string;
  status: StripePaymentIntentStatus;
  transfer_data?: any;
  transfer_group?: string;
}

export type StripePaymentIntentStatus = 
  | 'requires_payment_method'
  | 'requires_confirmation'
  | 'requires_action'
  | 'processing'
  | 'requires_capture'
  | 'canceled'
  | 'succeeded';

export interface StripeError {
  type: string;
  code?: string;
  decline_code?: string;
  message: string;
  param?: string;
  payment_intent?: StripePaymentIntent;
  payment_method?: any;
  setup_intent?: any;
  source?: any;
}