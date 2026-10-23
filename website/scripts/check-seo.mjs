import assert from 'node:assert/strict';
import { readFileSync, existsSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

const root = new URL('..', import.meta.url);
const dist = new URL('./dist/client/', root);

function read(rel) {
  return readFileSync(new URL(rel, dist), 'utf8');
}

function walk(dir, acc = []) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) walk(path, acc);
    else acc.push(path);
  }
  return acc;
}

const htmlFiles = walk(dist.pathname).filter((file) => file.endsWith('.html'));
assert.ok(htmlFiles.length > 10, 'expected built html pages');

const sitemap = read('sitemap.xml');
const locs = [...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)].map((match) => match[1]);
assert.ok(locs.includes('https://foodlaw.ai/'));
assert.ok(locs.includes('https://foodlaw.ai/en/'));
assert.ok(locs.includes('https://foodlaw.ai/supplemental/'));
assert.ok(locs.includes('https://foodlaw.ai/rej/'));
assert.ok(!locs.some((loc) => loc.includes('/404')));
assert.match(sitemap, /hreflang="x-default"/);

for (const loc of locs) {
  const path = new URL(loc).pathname;
  const file = path.endsWith('/') ? `${path}index.html` : path;
  assert.ok(existsSync(new URL(`.${file}`, dist)), `sitemap loc missing file: ${loc}`);
}

for (const file of htmlFiles) {
  const html = readFileSync(file, 'utf8');
  assert.match(html, /<title>[^<]+<\/title>/);
  assert.match(html, /name="description"/);
  assert.match(html, /rel="canonical"/);
  assert.match(html, /og-image\.png/);
  assert.match(html, /twitter:card" content="summary_large_image"/);
  assert.match(html, /id="main"/);
  assert.doesNotMatch(html, /<style[\s>]/);
  const executableInline = [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g)]
    .filter((match) => !/type="application\/ld\+json"/.test(match[1]) && !/\ssrc=/.test(match[1]) && match[2].trim());
  assert.equal(executableInline.length, 0, `inline script in ${file}`);
}

const home = read('index.html');
assert.doesNotMatch(home, /SearchAction/);
assert.doesNotMatch(home, /href="#"/);
assert.match(home, /href="\/rej\/"/);
assert.match(home, /FAQPage|application\/ld\+json/);

const supplemental = read('supplemental/index.html');
assert.match(supplemental, /hreflang="pl" href="https:\/\/foodlaw\.ai\/supplemental\/"/);
assert.doesNotMatch(supplemental, /hreflang="en"/);

const faq = read('faq/czym-jest-prawo-zywnosciowe/index.html');
assert.match(faq, /"@type":"FAQPage"/);
assert.match(faq, /tomasz-krawczyk/);

const hub = read('huby/oswiadczenia-zdrowotne/index.html');
assert.match(hub, /"@type":"Article"/);
assert.match(hub, /BreadcrumbList/);

const missing = read('404.html');
assert.match(missing, /noindex/);

assert.ok(existsSync(new URL('./og-image.png', dist)));
assert.ok(existsSync(new URL('./images/app-claims.webp', dist)));
assert.ok(existsSync(new URL('./llms.txt', dist)));
assert.match(read('robots.txt'), /ClaudeBot/);
assert.match(read('robots.txt'), /PerplexityBot/);
assert.match(read('robots.txt'), /Google-Extended/);
assert.match(read('robots.txt'), /GPTBot/);

console.log(`seo check ok (${locs.length} urls, ${htmlFiles.length} html files)`);
