export const PLAY_STORE_URL =
  import.meta.env.VITE_PLAY_STORE_URL ||
  'https://play.google.com/store/apps/details?id=com.lanceon.app'

export const APP_STORE_URL = import.meta.env.VITE_APP_STORE_URL || ''

export type DeviceKind = 'ios' | 'android' | 'other'

export function deviceKind(): DeviceKind {
  if (typeof navigator === 'undefined') return 'other'
  const ua = navigator.userAgent
  if (/iPad|iPhone|iPod/.test(ua)) return 'ios'
  if (/Android/i.test(ua)) return 'android'
  return 'other'
}

/** Store URL for the given device. Android always uses the Play Store HTTPS link. */
export function storeHref(kind: DeviceKind = deviceKind()) {
  if (kind === 'ios' && APP_STORE_URL) return APP_STORE_URL
  return PLAY_STORE_URL
}

export function openAppDownload() {
  const kind = deviceKind()
  if (kind === 'ios') {
    if (APP_STORE_URL) {
      window.location.href = APP_STORE_URL
      return
    }
    window.location.href = '/baixar'
    return
  }
  window.open(PLAY_STORE_URL, '_blank', 'noopener,noreferrer')
}
