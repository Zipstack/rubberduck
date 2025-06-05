export interface User {
  id: string;
  email: string;
  is_active: boolean;
  is_verified: boolean;
}

export interface Proxy {
  id: number;
  name: string;
  provider: string;
  description?: string;
  tags?: string[];
  port: number;
  status: 'running' | 'stopped';
  user_id: string;
  failure_config?: FailureConfig;
}

export interface FailureConfig {
  timeout_enabled: boolean;
  timeout_seconds?: number;
  timeout_rate: number;
  error_injection_enabled: boolean;
  error_rates: Record<number, number>;
  ip_filtering_enabled: boolean;
  ip_allowlist: string[];
  ip_blocklist: string[];
  rate_limiting_enabled: boolean;
  requests_per_minute: number;
}

export interface LogEntry {
  id: number;
  timestamp: string;
  proxy_id: number;
  ip_address: string;
  status_code: number;
  latency: number;
  cache_hit: boolean;
  prompt_hash: string;
  token_usage?: number;
  cost?: number;
  failure_type?: string;
}

export interface DashboardStats {
  total_proxies: number;
  running_proxies: number;
  stopped_proxies: number;
  cache_hit_rate: number;
  error_rate: number;
  total_rpm: number;
  total_cost: number;
  in_flight_requests: number;
}

export interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}