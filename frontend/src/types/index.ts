// ─── Auth ──────────────────────────────────────────────────────────────────

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  bio: string;
  avatar_url: string;
  links_count: number;
  date_joined: string;
  created_at: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
}

// ─── Links ─────────────────────────────────────────────────────────────────

export interface ShortURL {
  id: string;
  original_url: string;
  slug: string;
  title: string;
  short_url: string;
  owner_email: string;
  is_active: boolean;
  is_expired: boolean;
  click_count: number;
  created_at: string;
  expires_at: string | null;
}

export interface CreateLinkPayload {
  original_url: string;
  slug?: string;
  title?: string;
  expires_at?: string | null;
}

// ─── Analytics ─────────────────────────────────────────────────────────────

export interface DailyClick {
  date: string;
  count: number;
}

export interface DeviceStat {
  device_type: string;
  count: number;
}

export interface ReferrerStat {
  referrer: string;
  count: number;
}

export interface LinkAnalytics {
  total_clicks: number;
  clicks_in_period: number;
  period_days: number;
  daily_clicks: DailyClick[];
  by_device: DeviceStat[];
  top_referrers: ReferrerStat[];
}

// ─── API responses ─────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  pagination: {
    count: number;
    next: string | null;
    previous: string | null;
    total_pages: number;
    current_page: number;
  };
  results: T[];
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, string[]>;
  };
}
