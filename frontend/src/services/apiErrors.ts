export const NETWORK_ERROR_MESSAGE =
  'ShelfLife could not connect to the server. Check that the backend is running and try again.'

const httpStatusMessages: Record<number, string> = {
  400: 'Please review the information and try again.',
  404: 'That household, member, or inventory item could not be found. Please refresh and try again.',
  409: 'This change conflicts with the latest saved data. Refresh and try again.',
  422: 'Please review the form. Some information is missing or invalid.',
  500: 'ShelfLife encountered a server problem. Please try again shortly.',
  502: 'ShelfLife is temporarily unavailable. Please try again shortly.',
  503: 'ShelfLife is temporarily unavailable. Please try again shortly.',
  504: 'ShelfLife is temporarily unavailable. Please try again shortly.',
}

export function messageForHttpStatus(status: number): string {
  const knownMessage = httpStatusMessages[status]
  if (knownMessage) return knownMessage

  if (status >= 500) {
    return 'ShelfLife encountered a server problem. Please try again shortly.'
  }
  if (status >= 400) {
    return 'ShelfLife could not accept that request. Please review the information and try again.'
  }
  return 'ShelfLife received an unexpected server response. Please try again.'
}
