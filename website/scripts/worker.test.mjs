import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { handleRequest, SECURITY_HEADERS } from '../worker.js';

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
