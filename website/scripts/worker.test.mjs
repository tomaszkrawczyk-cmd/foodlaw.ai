import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { handleRequest, isLegacyWordpressPath, SECURITY_HEADERS } from '../worker.js';

test('wrangler runs the worker before static assets so www can 301', () => {
  const toml = readFileSync(new URL('../wrangler.toml', import.meta.url), 'utf8');
  assert.match(toml, /run_worker_first\s*=\s*true/);
});

test('www.foodlaw.ai redirects to the apex and keeps path and query', async () => {
  let fetched = false;
  const response = await handleRequest(new Request('https://www.foodlaw.ai/faq/?x=1'), {
    ASSETS: {
      fetch() {
        fetched = true;
        throw new Error('assets should not be fetched');
      },
    },
  });
  assert.equal(fetched, false);
  assert.equal(response.status, 301);
  assert.equal(response.headers.get('location'), 'https://foodlaw.ai/faq/?x=1');
});

test('apex responses keep the body and gain security headers', async () => {
  const response = await handleRequest(new Request('https://foodlaw.ai/faq/'), {
    ASSETS: {
      fetch: async () => new Response('<html></html>', {
        status: 200,
        headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'public, max-age=300' },
      }),
    },
  });
  assert.equal(response.status, 200);
  assert.equal(await response.text(), '<html></html>');
  assert.equal(response.headers.get('cache-control'), 'public, max-age=300');
  for (const [key, value] of Object.entries(SECURITY_HEADERS)) {
    assert.equal(response.headers.get(key), value);
  }
  assert.match(response.headers.get('content-security-policy'), /frame-ancestors 'none'/);
});

// The 30 <loc> values from website/src/pages/sitemap.xml.ts.
const SITEMAP_PATHS = [
  '/',
  '/en/',
  '/serwer-mcp/',
  '/en/mcp-server/',
  '/faq/',
  '/en/faq/',
  '/faq/czym-jest-prawo-zywnosciowe/',
  '/faq/jak-notyfikowac-suplement-diety/',
  '/faq/co-to-sa-oswiadczenia-zdrowotne/',
  '/faq/czym-jest-novel-food/',
  '/faq/jak-dziala-system-rasff/',
  '/en/faq/what-is-food-law/',
  '/en/faq/how-to-notify-a-food-supplement/',
  '/en/faq/what-are-health-claims/',
  '/en/faq/what-is-novel-food/',
  '/en/faq/how-does-rasff-work/',
  '/huby/',
  '/en/hubs/',
  '/huby/oswiadczenia-zdrowotne/',
  '/huby/suplementy-diety/',
  '/huby/nowa-zywnosc/',
  '/huby/znakowanie-zywnosci/',
  '/huby/prawo-zywnosciowe/',
  '/en/hubs/health-claims/',
  '/en/hubs/dietary-supplements/',
  '/en/hubs/novel-food/',
  '/en/hubs/food-labelling/',
  '/en/hubs/food-law/',
  '/supplemental/',
  '/rej/',
];

const LEGACY_URLS = [
  'https://foodlaw.ai/blog/',
  'https://foodlaw.ai/blog',
  'https://foodlaw.ai/blog/older-post/',
  'https://foodlaw.ai/blog/?p=1',
  'https://foodlaw.ai/hello-world/',
  'https://foodlaw.ai/hello-world',
  'https://foodlaw.ai/HELLO-WORLD/',
  'https://foodlaw.ai/category/uncategorized/',
  'https://foodlaw.ai/category/uncategorized',
  'https://foodlaw.ai/category/uncategorized/feed/',
  'https://foodlaw.ai/wp-content/',
  'https://foodlaw.ai/wp-content/uploads/2020/01/pic.jpg',
  'https://foodlaw.ai/wp-login.php',
  'https://foodlaw.ai/wp-login.php?redirect_to=/wp-admin/',
  'https://foodlaw.ai/WP-Login.PHP',
  'https://foodlaw.ai/xmlrpc.php',
  'https://foodlaw.ai/xmlrpc.php/',
  'https://foodlaw.ai/wp-cron.php',
  'https://foodlaw.ai/wp-config.php',
  'https://foodlaw.ai/wp-comments-post.php',
  'https://foodlaw.ai/%62log/',
];

function refusingAssets() {
  return {
    ASSETS: {
      fetch() {
        throw new Error('assets should not be fetched');
      },
    },
  };
}

test('legacy WordPress paths are 410 and are not redirected', async () => {
  assert.equal(SITEMAP_PATHS.length, 30);
  for (const url of LEGACY_URLS) {
    const response = await handleRequest(new Request(url), refusingAssets());
    assert.equal(response.status, 410, url);
    assert.equal(response.headers.get('location'), null, url);
    assert.equal(response.headers.get('content-type'), 'text/plain; charset=utf-8', url);
    assert.equal(response.headers.get('cache-control'), 'public, max-age=86400', url);
    assert.equal(await response.text(), 'Gone\n', url);
    for (const [key, value] of Object.entries(SECURITY_HEADERS)) {
      assert.equal(response.headers.get(key), value, `${url} ${key}`);
    }
  }
});

test('www still 301s legacy paths to the apex instead of answering 410', async () => {
  const response = await handleRequest(new Request('https://www.foodlaw.ai/blog/?x=1'), refusingAssets());
  assert.equal(response.status, 301);
  assert.equal(response.headers.get('location'), 'https://foodlaw.ai/blog/?x=1');

  const login = await handleRequest(new Request('http://www.foodlaw.ai/wp-login.php'), refusingAssets());
  assert.equal(login.status, 301);
  assert.equal(login.headers.get('location'), 'http://foodlaw.ai/wp-login.php');
});

test('sitemap URLs, /rej, and other real paths are not 410', async () => {
  const passthrough = [
    ...SITEMAP_PATHS.map((path) => `https://foodlaw.ai${path}`),
    'https://foodlaw.ai/rej',
    'https://foodlaw.ai/?p=1',
    'https://foodlaw.ai/blog/../faq/',
    'https://foodlaw.ai/not-a-real-page/',
    'https://foodlaw.ai/category/news/',
    'https://foodlaw.ai/hello-world-extra/',
    'https://foodlaw.ai/wp-admin/',
    'https://foodlaw.ai/wp-includes/js/jquery.js',
    'https://foodlaw.ai/sitemap.xml',
    'https://foodlaw.ai/robots.txt',
    'https://foodlaw.ai/images/rej-hero.webp',
  ];

  for (const url of passthrough) {
    assert.equal(isLegacyWordpressPath(new URL(url).pathname), false, url);
    let fetched = 0;
    const response = await handleRequest(new Request(url), {
      ASSETS: {
        fetch: async () => {
          fetched += 1;
          return new Response('page', {
            status: 200,
            headers: { 'content-type': 'text/html; charset=utf-8' },
          });
        },
      },
    });
    assert.equal(fetched, 1, url);
    assert.equal(response.status, 200, url);
    assert.equal(await response.text(), 'page', url);
  }
});

test('/rej without a slash still returns the asset redirect', async () => {
  let fetched = 0;
  const response = await handleRequest(new Request('https://foodlaw.ai/rej'), {
    ASSETS: {
      fetch: async () => {
        fetched += 1;
        return new Response(null, { status: 307, headers: { location: '/rej/' } });
      },
    },
  });
  assert.equal(fetched, 1);
  assert.equal(response.status, 307);
  assert.equal(response.headers.get('location'), '/rej/');
  for (const [key, value] of Object.entries(SECURITY_HEADERS)) {
    assert.equal(response.headers.get(key), value);
  }
});
