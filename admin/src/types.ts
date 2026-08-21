export type UserRole = 'admin' | 'athlete' | 'scout'

export interface User {
  id: number
  email: string
  full_name: string
  role: UserRole
  is_active: boolean
  is_approved: boolean
  created_at: string
}

export interface Court {
  id: number
  name: string
  city_id?: number | null
  city_name?: string | null
  address: string | null
  is_active: boolean
  created_at: string
  device_api_key?: string | null
}

export interface City {
  id: number
  name: string
  is_active: boolean
  created_at: string
  court_count: number
}

export interface Device {
  id: number
  court_id: number
  camera_index: number
  name: string
  is_online: boolean
  last_heartbeat: string | null
}

export interface CourtAccessRequest {
  id: number
  user_id: number
  court_id: number
  status: 'pending' | 'approved' | 'rejected'
  play_started_at?: string | null
  play_ended_at?: string | null
  created_at: string
  reviewed_at: string | null
  user?: User | null
  court?: Court | null
}

export interface Recording {
  id: number
  court_id: number
  camera_index: number
  duration_seconds: number
  triggered_at: string
  expires_at: string
  created_at: string
  download_url?: string | null
  court_name?: string | null
  status?: 'available' | 'expired'
}

export interface DayCount {
  date: string
  count: number
}

export interface CourtStatusItem {
  id: number
  name: string
  online: boolean
  device_count: number
}

export interface AdminStats {
  users: number
  active_users: number
  courts: number
  courts_online: number
  courts_offline: number
  devices_online: number
  devices_total: number
  devices_offline: number
  recordings: number
  recordings_today: number
  pending_access_requests: number
  pending_scouts: number
  storage_used_gb: number
  storage_limit_gb: number
  storage_limit_tb: number
  recordings_by_day: DayCount[]
  court_status: CourtStatusItem[]
}

export interface ActivityItem {
  message: string
  created_at: string
  kind: string
}

export interface PlatformSettings {
  platform_name: string
  support_email: string
  timezone: string
  language: string
  storage_limit_tb: number
  retention_hours: number
}

export interface MessageResponse {
  message: string
}

export type ToastType = 'success' | 'error' | 'info'

export interface Toast {
  id: string
  message: string
  type: ToastType
}
