export type UserRole = 'athlete' | 'scout' | 'admin'

export type User = {
  id: number
  email: string
  full_name: string
  role: UserRole
  is_active: boolean
  is_approved: boolean
  avatar_url?: string | null
  created_at: string
}

export type City = {
  id: number
  name: string
  is_active: boolean
  created_at: string
  court_count: number
}

export type Court = {
  id: number
  name: string
  city_id: number | null
  city_name: string | null
  address: string | null
  is_active: boolean
  created_at: string
}

export type Recording = {
  id: number
  court_id: number
  camera_index: number
  duration_seconds: number
  triggered_at: string
  expires_at: string
  created_at: string
  download_url?: string | null
  court_name?: string | null
}

export type CourtAccess = {
  id: number
  user_id: number
  court_id: number
  granted_at: string
  court?: Court | null
}

export type CourtAccessRequest = {
  id: number
  user_id: number
  court_id: number
  status: string
  play_started_at?: string | null
  play_ended_at?: string | null
  created_at: string
  court?: Court | null
}
