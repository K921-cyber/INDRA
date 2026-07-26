/**
 * Build a WebSocket URL base from the current page host.
 *
 * In Vite dev mode, the proxy is configured to forward /ws requests
 * to the backend, so we use the same origin as the page.
 *
 * In production (Nginx), the frontend and backend share the same
 * origin, so window.location.host works correctly.
 */
export function getWebSocketBase(): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host;

  // Use the same origin as the page — the Vite proxy handles forwarding
  // /ws/* to the backend. This works in both dev and production.
  return `${protocol}//${host}`;
}
