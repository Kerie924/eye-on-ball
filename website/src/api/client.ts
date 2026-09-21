import type {
  City,
  Court,
  CourtAccess,
  CourtAccessRequest,
  Recording,
  User,
  UserRole,
} from '../types'

const API_BASE = import.meta.env.VITE_API_URL ?? ''

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

function getToken() {
  return localStorage.getItem('lanceon_token')
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem('lanceon_token', token)
  else localStorage.removeItem('lanceon_token')
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  if (!(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }
  const token = getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)

  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`, { ...options, headers })
  } catch {
    throw new ApiError(0, 'Sem conexao com o servidor. Confira a internet e tente de novo.')
  }

  if (!response.ok) {
    let message = 'Erro na requisicao'
    try {
      const data = await response.json()
      if (typeof data.detail === 'string') message = data.detail
      else if (Array.isArray(data.detail)) {
        message = data.detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join(' ') || message
      }
    } catch {
      message = response.statusText || message
    }
    throw new ApiError(response.status, message)
  }

  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const LEGAL = {
  privacy: `${API_BASE || 'https://api.lanceonpara.com.br'}/api/legal/privacy`,
  terms: `${API_BASE || 'https://api.lanceonpara.com.br'}/api/legal/terms`,
}

export const api = {
  login(email: string, password: string) {
    return request<{ access_token: string }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
  },

  register(payload: {
    email: string
    password: string
    full_name: string
    role: Extract<UserRole, 'athlete' | 'scout'>
  }) {
    return request<User>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  me() {
    return request<User>('/api/auth/me')
  },

  updateProfile(payload: {
    full_name?: string
    email?: string
    avatar_url?: string | null
    current_password?: string
    new_password?: string
  }) {
    return request<User>('/api/auth/me', {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
  },

  deleteAccount() {
    return request<{ message: string }>('/api/auth/me', { method: 'DELETE' })
  },

  forgotPassword(email: string) {
    return request<{ message: string }>('/api/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email }),
    })
  },

  cities() {
    return request<City[]>('/api/cities')
  },

  courts(cityId?: number) {
    const query = cityId ? `?city_id=${cityId}` : ''
    return request<Court[]>(`/api/courts${query}`)
  },

  recordings(courtId?: number, playDate?: string, startTime?: string, endTime?: string) {
    const params = new URLSearchParams()
    if (courtId) params.set('court_id', String(courtId))
    if (playDate) params.set('play_date', playDate)
    if (startTime) params.set('start_time', startTime)
    if (endTime) params.set('end_time', endTime)
    const query = params.toString() ? `?${params}` : ''
    return request<Recording[]>(`/api/recordings${query}`)
  },

  recording(id: number) {
    return request<Recording>(`/api/recordings/${id}`)
  },

  recordingStreamUrl(id: number, download = false) {
    const token = getToken()
    const params = new URLSearchParams()
    if (token) params.set('token', token)
    if (download) params.set('download', 'true')
    const q = params.toString()
    return `${API_BASE}/api/recordings/${id}/stream${q ? `?${q}` : ''}`
  },

  myCourtAccess() {
    return request<CourtAccess[]>('/api/access/mine')
  },

  myAccessRequests() {
    return request<CourtAccessRequest[]>('/api/access-requests/mine')
  },

  requestCourtAccess(courtId: number, playStartedAt: string, playEndedAt: string) {
    return request<CourtAccessRequest>('/api/access-requests', {
      method: 'POST',
      body: JSON.stringify({
        court_id: courtId,
        play_started_at: playStartedAt,
        play_ended_at: playEndedAt,
      }),
    })
  },

  async submitFeedback(message: string, files: File[]) {
    const body = new FormData()
    body.append('message', message)
    for (const file of files) body.append('images', file)
    return request<{ message: string }>('/api/feedback', { method: 'POST', body })
  },

  triggerCapture(courtId: number, cameraIndex?: number) {
    return request<{ message: string; cameras: number[]; device_online: boolean }>(
      '/api/recordings/trigger',
      {
        method: 'POST',
        body: JSON.stringify({
          court_id: courtId,
          camera_index: cameraIndex ?? null,
        }),
      },
    )
  },
}
