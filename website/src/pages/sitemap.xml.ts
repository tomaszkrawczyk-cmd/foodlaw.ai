import type { APIRoute } from 'astro';
import { faqs, hubs, faqUrl, hubUrl, faqIndexUrl, hubIndexUrl } from '../data/geo';

export const prerender = true;

const LASTMOD = '2026-10-23';

type Alt = { hreflang: string; href: string };

function entry(loc: string, alts: Alt[], priority: string) {
  const links = alts
    .map((alt) => `    <xhtml:link rel="alternate" hreflang="${alt.hreflang}" href="${alt.href}" />`)
    .join('\n');
  return `  <url>
    <loc>${loc}</loc>
    <lastmod>${LASTMOD}</lastmod>
    <priority>${priority}</priority>
${links}
  </url>`;
}

function pair(pl: string, en: string, priorityPl: string, priorityEn: string) {
  const alts: Alt[] = [
    { hreflang: 'pl', href: pl },
    { hreflang: 'en', href: en },
    { hreflang: 'x-default', href: pl },
  ];
  return [entry(pl, alts, priorityPl), entry(en, alts, priorityEn)].join('\n');
}

function mono(url: string, priority: string) {
  return entry(url, [
    { hreflang: 'pl', href: url },
    { hreflang: 'x-default', href: url },
  ], priority);
}

export const GET: APIRoute = () => {
  const blocks = [
    pair('https://foodlaw.ai/', 'https://foodlaw.ai/en/', '1.0', '0.9'),
    pair(faqIndexUrl('pl'), faqIndexUrl('en'), '0.8', '0.7'),
    ...faqs.pl.map((item) => pair(faqUrl('pl', item.slug), faqUrl('en', item.altSlug), '0.7', '0.6')),
    pair(hubIndexUrl('pl'), hubIndexUrl('en'), '0.8', '0.7'),
    ...hubs.pl.map((hub) => pair(hubUrl('pl', hub.slug), hubUrl('en', hub.altSlug), '0.7', '0.6')),
    mono('https://foodlaw.ai/supplemental/', '0.6'),
    mono('https://foodlaw.ai/rej/', '0.5'),
  ];

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
${blocks.join('\n')}
</urlset>
`;

  return new Response(xml, {
    headers: { 'Content-Type': 'application/xml; charset=utf-8' },
  });
};
