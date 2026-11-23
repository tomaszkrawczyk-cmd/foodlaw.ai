// foodlaw.ai and www.foodlaw.ai are this site.
// supplemental.pl is a separate site; never redirect to it.
// This redirect runs only when worker.js runs. Static assets are served first
// unless wrangler.toml sets assets.run_worker_first = true.
// Legacy WordPress URLs are 410 from this worker, with no Location header.
// www → apex still happens first. Sitemap URLs and /rej are not in this set,
// so /rej keeps the asset trailing-slash redirect.

export const SECURITY_HEADERS = {
  'Content-Security-Policy':
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; upgrade-insecure-requests",
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
};

// Matched with or without a trailing slash, and any path under them.
// /wp-*.php is only a site-root filename (wp-login.php, wp-cron.php, ...).
// xmlrpc.php does not match that glob; Search Console still requests it.
const LEGACY_WORDPRESS_PREFIXES = [
  '/blog',
  '/hello-world',
  '/category/uncategorized',
  '/wp-content',
];

export function isLegacyWordpressPath(pathname) {
  let path = pathname;
  try {
    path = decodeURIComponent(pathname);
  } catch {
    path = pathname;
  }
  path = path.toLowerCase().replace(/\/{2,}/g, '/');
  if (path.length > 1 && path.endsWith('/')) path = path.slice(0, -1);

  for (const prefix of LEGACY_WORDPRESS_PREFIXES) {
    if (path === prefix || path.startsWith(`${prefix}/`)) return true;
  }
  if (path === '/xmlrpc.php') return true;
  return /^\/wp-[^/]+\.php$/.test(path);
}

function legacyGone() {
  const headers = new Headers(SECURITY_HEADERS);
  headers.set('Content-Type', 'text/plain; charset=utf-8');
  headers.set('Cache-Control', 'public, max-age=86400');
  return new Response('Gone\n', { status: 410, headers });
}

export async function handleRequest(request, env) {
  const url = new URL(request.url);
  if (url.hostname === 'www.foodlaw.ai') {
    url.hostname = 'foodlaw.ai';
    return Response.redirect(url.toString(), 301);
  }

  if (isLegacyWordpressPath(url.pathname)) {
    return legacyGone();
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
