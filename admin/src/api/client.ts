import type {
  ActivityItem,
  AdminStats,
  City,
  Court,
  CourtAccessRequest,
  Device,
  FeedbackReport,
  MessageResponse,
  PlatformSettings,
  Recording,
  User,
  UserRole,
} from '../types'

const API_BASE = import.meta.env.VITE_API_URL ?? ''

class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

function getToken(): string | null {
  return localStorage.getItem('token')
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)

  if (!(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }

  const token = getToken()
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    let message = 'Erro na requisicao'
    try {
      const data = await response.json()
      message = typeof data.detail === 'string' ? data.detail : message
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
    return request<{ access_token: string; token_type: string }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
  },

  me() {
    return request<User>('/api/auth/me')
  },

  stats() {
    return request<AdminStats>('/api/admin/stats')
  },

  activity() {
    return request<ActivityItem[]>('/api/admin/activity')
  },

  settings() {
    return request<PlatformSettings>('/api/admin/settings')
  },

  feedbackReports() {
    return request<FeedbackReport[]>('/api/admin/feedback')
  },

  markFeedbackRead(reportId: number) {
    return request<FeedbackReport>(`/api/admin/feedback/${reportId}`, {
      method: 'PATCH',
    })
  },

  updateSettings(payload: Partial<PlatformSettings>) {
    return request<PlatformSettings>('/api/admin/settings', {
      method: 'PUT',
      body: JSON.stringify(payload),
    })
  },

  users() {
    return request<User[]>('/api/admin/users')
  },

  createUser(payload: {
    email: string
    password: string
    full_name: string
    role: UserRole
  }) {
    return request<User>('/api/admin/users', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  updateUser(userId: number, payload: { is_active?: boolean; is_approved?: boolean }) {
    return request<User>(`/api/admin/users/${userId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
  },

  pendingScouts() {
    return request<User[]>('/api/admin/scouts/pending')
  },

  approveScout(userId: number) {
    return request<MessageResponse>(`/api/admin/scouts/${userId}/approve`, {
      method: 'POST',
    })
  },

  rejectScout(userId: number) {
    return request<MessageResponse>(`/api/admin/scouts/${userId}/reject`, {
      method: 'POST',
    })
  },

  courts(cityId?: number) {
    const query = cityId ? `?city_id=${cityId}` : ''
    return request<Court[]>(`/api/courts${query}`)
  },

  cities(includeInactive = false) {
    const query = includeInactive ? '?include_inactive=true' : ''
    return request<City[]>(`/api/cities${query}`)
  },

  createCity(name: string) {
    return request<City>('/api/cities', {
      method: 'POST',
      body: JSON.stringify({ name }),
    })
  },

  updateCity(cityId: number, payload: { name?: string; is_active?: boolean }) {
    return request<City>(`/api/cities/${cityId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
  },

  deactivateCity(cityId: number) {
    return request<MessageResponse>(`/api/cities/${cityId}`, {
      method: 'DELETE',
    })
  },

  createCourt(name: string, address: string, cameraCount = 2, cityId: number) {
    return request<Court>('/api/courts', {
      method: 'POST',
      body: JSON.stringify({
        name,
        address: address || null,
        camera_count: cameraCount,
        city_id: cityId,
      }),
    })
  },

  updateCourt(
    courtId: number,
    payload: {
      name?: string
      address?: string | null
      camera_count?: number
      city_id?: number
    },
  ) {
    return request<Court>(`/api/courts/${courtId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
  },

  courtDevices(courtId: number) {
    return request<Device[]>(`/api/courts/${courtId}/devices`)
  },

  rotateCourtKey(courtId: number) {
    return request<Court>(`/api/courts/${courtId}/rotate-key`, {
      method: 'POST',
    })
  },

  deactivateCourt(courtId: number) {
    return request<MessageResponse>(`/api/courts/${courtId}`, {
      method: 'DELETE',
    })
  },

  triggerCapture(courtId: number, cameraIndex?: number) {
    return request<{
      message: string
      court_id: number
      court_name: string
      cameras: number[]
      device_online: boolean
    }>('/api/recordings/trigger', {
      method: 'POST',
      body: JSON.stringify({
        court_id: courtId,
        camera_index: cameraIndex ?? null,
      }),
    })
  },

  accessRequests() {
    return request<CourtAccessRequest[]>('/api/access-requests')
  },

  approveAccessRequest(requestId: number) {
    return request<MessageResponse>(`/api/access-requests/${requestId}/approve`, {
      method: 'POST',
    })
  },

  rejectAccessRequest(requestId: number) {
    return request<MessageResponse>(`/api/access-requests/${requestId}/reject`, {
      method: 'POST',
    })
  },

  recordings(courtId?: number, status?: 'available' | 'expired' | 'all') {
    const params = new URLSearchParams()
    if (courtId) params.set('court_id', String(courtId))
    if (status) params.set('status', status)
    const query = params.toString() ? `?${params.toString()}` : ''
    return request<Recording[]>(`/api/admin/recordings${query}`)
  },

  deleteRecording(recordingId: number) {
    return request<MessageResponse>(`/api/recordings/${recordingId}`, {
      method: 'DELETE',
    })
  },

  /** Authenticated stream URL (works even when S3 is private). */
  recordingStreamUrl(recordingId: number, download = false) {
    const token = getToken()
    const params = new URLSearchParams()
    if (token) params.set('token', token)
    if (download) params.set('download', 'true')
    const query = params.toString() ? `?${params.toString()}` : ''
    return `${API_BASE}/api/recordings/${recordingId}/stream${query}`
  },

  async downloadRecordingFile(recordingId: number, downloadUrl?: string | null) {
    if (downloadUrl) {
      const anchor = document.createElement('a')
      anchor.href = downloadUrl
      anchor.download = `lance-${recordingId}.mp4`
      anchor.rel = 'noreferrer'
      document.body.appendChild(anchor)
      anchor.click()
      anchor.remove()
      return
    }

    const token = getToken()
    const response = await fetch(
      `${API_BASE}/api/recordings/${recordingId}/stream?download=true`,
      {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      },
    )
    if (!response.ok) {
      let message = 'Erro ao baixar video'
      try {
        const data = await response.json()
        message = typeof data.detail === 'string' ? data.detail : message
      } catch {
        /* ignore */
      }
      throw new ApiError(response.status, message)
    }
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `lance-${recordingId}.mp4`
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
    URL.revokeObjectURL(url)
  },
}

export { ApiError }
