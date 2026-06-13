/**
 * Build a WebSocket URL base from the current page host.
 *
 * In Vite dev mode (port 3xxx), Vite's WebSocket proxy has issues
 * with browser connections. We connect directly to the backend on
 * port 8000 instead.
 *
 * In production (Nginx), the frontend and backend share the same
 * origin, so window.location.host works correctly.
 */
export function getWebSocketBase(): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host;

  // Detect Vite dev mode: any port in the 3000–3999 range
  const portStr = host.split(':')[1];
  if (portStr) {
    const port = parseInt(portStr, 10);
    if (!isNaN(port) && port >= 3000 && port <= 3999) {
      return `${protocol}//localhost:8000`;
    }
  }

  return `${protocol}//${host}`;
}
