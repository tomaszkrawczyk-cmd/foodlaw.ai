// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
export default defineConfig({
  site: 'https://foodlaw.ai',
  trailingSlash: 'always',
  output: 'static',
  outDir: './dist/client',
  vite: {
    plugins: [tailwindcss()],
  },
});
