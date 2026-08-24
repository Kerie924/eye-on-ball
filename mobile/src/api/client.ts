import { Platform } from 'react-native'

import { API_URL } from '../config'
import type {
  City,
  Court,
  CourtAccess,
  CourtAccessRequest,
  FeedbackSubmitResponse,
  Recording,
  TokenResponse,
  User,
  UserRole,
} from '../types'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

function isFormData(body: BodyInit | null | undefined): body is FormData {
  return typeof FormData !== 'undefined' && body instanceof FormData
}

function messageFromApiDetail(detail: unknown, fallback: string) {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    const parts = detail.map((item) => {
      if (typeof item === 'string') return item
      if (item && typeof item === 'object' && 'msg' in item) {
        return String((item as { msg: unknown }).msg)
      }
      return ''
    })
    return parts.filter(Boolean).join(' ') || fallback
  }
  return fallback
}

let authToken: string | null = null

export function setAuthToken(token: string | null) {
  authToken = token
}

export function getAuthToken() {
  return authToken
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)

  if (isFormData(options.body)) {
    headers.delete('Content-Type')
  } else if (!(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }

  if (authToken) {
    headers.set('Authorization', `Bearer ${authToken}`)
  }

  let response: Response
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers,
    })
  } catch {
    throw new ApiError(
      0,
      `Sem conexao com a API (${API_URL}). Verifique se o backend esta rodando e se EXPO_PUBLIC_API_URL esta correto.`,
    )
  }

  if (!response.ok) {
    let message = 'Erro na requisicao'
    try {
      const data = await response.json()
      message = messageFromApiDetail(data.detail, message)
    } catch {
      message = response.statusText || message
    }
    throw new ApiError(response.status, message)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

export const api = {
  login(email: string, password: string) {
    return request<TokenResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
  },

  register(payload: {
    email: string
    password: string
    full_name: string
    role: UserRole
  }) {
    return request<User>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  googleLogin(idToken: string, role: UserRole = 'athlete') {
    return request<TokenResponse>('/api/auth/google', {
      method: 'POST',
      body: JSON.stringify({ id_token: idToken, role }),
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

  forgotPassword(email: string) {
    return request<{ message: string }>(
      '/api/auth/forgot-password',
      {
        method: 'POST',
        body: JSON.stringify({ email }),
      },
    )
  },

  resetPassword(token: string, password: string) {
    return request<{ message: string }>('/api/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify({ token, password }),
    })
  },

  courts(cityId?: number) {
    const query = cityId ? `?city_id=${cityId}` : ''
    return request<Court[]>(`/api/courts${query}`)
  },

  cities() {
    return request<City[]>('/api/cities')
  },

  recordings(courtId?: number, playDate?: string, startTime?: string, endTime?: string) {
    const params = new URLSearchParams()
    if (courtId) params.set('court_id', String(courtId))
    if (playDate) params.set('play_date', playDate)
    if (startTime) params.set('start_time', startTime)
    if (endTime) params.set('end_time', endTime)
    const query = params.toString() ? `?${params.toString()}` : ''
    return request<Recording[]>(`/api/recordings${query}`)
  },

  recording(recordingId: number) {
    return request<Recording>(`/api/recordings/${recordingId}`)
  },

  recordingStreamUrl(recordingId: number) {
    return `${API_URL}/api/recordings/${recordingId}/stream`
  },

  recordingSaveUrl(recordingId: number) {
    const token = getAuthToken()
    const params = new URLSearchParams()
    if (token) params.set('token', token)
    const query = params.toString()
    return `${API_URL}/api/recordings/${recordingId}/save${query ? `?${query}` : ''}`
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

  async submitFeedback(
    message: string,
    images: { uri: string; name: string; type: string }[],
  ) {
    const body = new FormData()
    body.append('message', message)
    for (const image of images) {
      const type = image.type || 'image/jpeg'
      if (Platform.OS === 'web') {
        const blob = await fetch(image.uri).then((res) => res.blob())
        const file = new File([blob], image.name, {
          type: type || blob.type || 'image/jpeg',
        })
        body.append('images', file)
        continue
      }
      body.append('images', {
        uri: image.uri,
        name: image.name,
        type,
      } as unknown as Blob)
    }
    return request<FeedbackSubmitResponse>('/api/feedback', {
      method: 'POST',
      body,
    })
  },
}
