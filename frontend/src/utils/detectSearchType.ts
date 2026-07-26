// ==================== Detection Logic ====================

export function detectSearchType(query: string) {
  const ipRegex = /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/;
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const domainRegex = /^([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$/;
  const phoneRegex = /^\+?[\d\s-]{7,15}$/;

  if (ipRegex.test(query)) return 'ip' as const;
  if (emailRegex.test(query)) return 'email' as const;
  if (phoneRegex.test(query)) return 'phone' as const;
  if (domainRegex.test(query)) return 'domain' as const;
  return 'name' as const;
}
