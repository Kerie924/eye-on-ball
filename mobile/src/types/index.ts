export type UserRole = 'athlete' | 'scout' | 'admin'

export type AccessRequestStatus = 'pending' | 'approved' | 'rejected'

export interface User {
  id: number
  email: string
  full_name: string
  role: UserRole
  is_active: boolean
  is_approved: boolean
  avatar_url?: string | null
  created_at: string
}

export interface Court {
  id: number
  name: string
  address: string | null
  is_active: boolean
  created_at: string
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
}

export interface CourtAccessRequest {
  id: number
  user_id: number
  court_id: number
  status: AccessRequestStatus
  created_at: string
  reviewed_at: string | null
  court?: Court | null
}

export interface CourtAccess {
  id: number
  user_id: number
  court_id: number
  granted_at: string
  court?: Court | null
}

export interface TokenResponse {
  access_token: string
  token_type: string
}
