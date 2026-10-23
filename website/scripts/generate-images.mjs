import { readdirSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = new URL('..', import.meta.url);
const pnpm = new URL('./node_modules/.pnpm/', root);
const dir = readdirSync(pnpm).find((name) => name.startsWith('sharp@'));
if (!dir) throw new Error('sharp is not installed');
const sharpMod = await import(pathToFileURL(`${pnpm.pathname}${dir}/node_modules/sharp/lib/index.js`).href);
const sharp = sharpMod.default;

const og = `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1e3a5f"/>
      <stop offset="100%" stop-color="#0b1627"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#g)"/>
  <rect x="0" y="0" width="14" height="630" fill="#c9a227"/>
  <text x="72" y="250" font-family="Liberation Sans, DejaVu Sans, sans-serif" font-size="78" font-weight="700" fill="#ffffff">FOODLAW.ai</text>
  <text x="72" y="330" font-family="Liberation Sans, DejaVu Sans, sans-serif" font-size="34" fill="#c5d5e8">Prawo żywnościowe UE i Polski</text>
  <text x="72" y="390" font-family="Liberation Sans, DejaVu Sans, sans-serif" font-size="28" fill="#d3b84e">EU and Polish food law</text>
  <text x="72" y="520" font-family="Liberation Sans, DejaVu Sans, sans-serif" font-size="22" fill="#9fb9d9">Tomasz Krawczyk · supplemental.pl</text>
</svg>`;

await sharp(Buffer.from(og)).png().toFile(fileURLToPath(new URL('./public/og-image.png', root)));

const shots = [
  ['app-claims.png', 1280, 720],
  ['nutrimetr.png', 1280, 720],
  ['supplemental-ai.png', 1280, 720],
  ['rej-hero.png', 1600, 840],
];

for (const [name, width, height] of shots) {
  const input = fileURLToPath(new URL(`./public/images/${name}`, root));
  const output = fileURLToPath(new URL(`./public/images/${name.replace('.png', '.webp')}`, root));
  await sharp(input).resize(width, height, { fit: 'cover' }).webp({ quality: 72 }).toFile(output);
  console.log('wrote', output);
}

console.log('wrote og-image.png');
