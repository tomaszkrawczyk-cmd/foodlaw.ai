// foodlaw.ai and www.foodlaw.ai are this site.
// supplemental.pl is a separate site; never redirect to it.
// A zone-level redirect (www → supplemental.pl) currently runs before this
// Worker. This handler is the correct canonical once that rule is removed.

export const SECURITY_HEADERS = {
  'Content-Security-Policy':
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; upgrade-insecure-requests",
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
};

export async function handleRequest(request, env) {
  const url = new URL(request.url);
  if (url.hostname === 'www.foodlaw.ai') {
    url.hostname = 'foodlaw.ai';
    return Response.redirect(url.toString(), 301);
  }

  const response = await env.ASSETS.fetch(request);
  const headers = new Headers(response.headers);
  for (const [key, value] of Object.entries(SECURITY_HEADERS)) {
    headers.set(key, value);
  }
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}

export default {
  fetch: handleRequest,
};
