import { expect, test } from '@playwright/test';
import { existsSync, readFileSync } from 'node:fs';
import { extname, resolve } from 'node:path';

const ROOT = resolve('.');
const PUBLIC_ORIGIN = 'https://smart-kozeni.com';
const TRANSPARENT_IMAGE =
  'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=';

function publicPaths() {
  const sitemap = readFileSync('sitemap.xml', 'utf8');
  const paths = [...sitemap.matchAll(/<loc>https:\/\/smart-kozeni\.com([^<]*)<\/loc>/g)]
    .map((match) => match[1] || '/')
    .sort();
  expect(paths).toHaveLength(66);
  return [...paths, '/404.html'];
}

function htmlFileFor(path) {
  if (path === '/') return resolve(ROOT, 'index.html');
  if (path === '/404.html') return resolve(ROOT, '404.html');
  return resolve(ROOT, path.replace(/^\//, ''), 'index.html');
}

function localPath(url) {
  return resolve(ROOT, url.split('?', 1)[0].replace(/^\//, ''));
}

function imageDataUri(src) {
  if (!src.startsWith('/assets/')) return TRANSPARENT_IMAGE;
  const path = localPath(src);
  const mime = {
    '.gif': 'image/gif',
    '.ico': 'image/x-icon',
    '.jpeg': 'image/jpeg',
    '.jpg': 'image/jpeg',
    '.png': 'image/png',
    '.svg': 'image/svg+xml',
    '.webp': 'image/webp',
  }[extname(path).toLowerCase()];
  if (!mime) throw new Error(`unsupported local image type: ${src}`);
  return `data:${mime};base64,${readFileSync(path).toString('base64')}`;
}

function assertReferencedAssetsExist(html, sourcePath) {
  const refs = [...html.matchAll(/(?:src|href)="(\/(?:assets\/[^"?#]+|site\.webmanifest)(?:\?[^"#]*)?)"/g)]
    .map((match) => match[1]);
  for (const ref of refs) {
    const asset = localPath(ref);
    if (!existsSync(asset)) throw new Error(`${sourcePath}: missing local asset ${ref}`);
  }
}

function browserDocument(path) {
  const source = htmlFileFor(path);
  if (!existsSync(source)) throw new Error(`missing generated page: ${path}`);
  let html = readFileSync(source, 'utf8');
  assertReferencedAssetsExist(html, source);

  html = html.replace(
    /<link rel="stylesheet" href="(\/assets\/[^"?]+\.css)(?:\?[^"#]*)?">/g,
    (_tag, href) => `<style data-browser-source="${href}">${readFileSync(localPath(href), 'utf8')}</style>`,
  );
  html = html.replace(
    /<script defer src="\/assets\/kozeni-analytics\.v1\.js"><\/script>/g,
    '<!-- analytics runtime is exercised separately without network -->',
  );

  let deferredScripts = '';
  html = html.replace(
    /<script defer src="(\/assets\/[^"?]+\.js)(?:\?[^"#]*)?"><\/script>/g,
    (_tag, src) => {
      deferredScripts += `<script data-browser-source="${src}">${readFileSync(localPath(src), 'utf8')}</script>`;
      return '';
    },
  );
  html = html.replace(/<link rel="(?:icon|apple-touch-icon|manifest)"[^>]*>/g, '');
  html = html.replace(/(<img\b[^>]*\bsrc=")([^"]+)("[^>]*>)/g, (_tag, prefix, src, suffix) => `${prefix}${imageDataUri(src)}${suffix}`);
  html = html.replace('</body>', `${deferredScripts}</body>`);
  return html;
}

function observeRuntime(page) {
  const errors = [];
  page.on('pageerror', (error) => errors.push(`pageerror: ${error.message}`));
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(`console: ${message.text()}`);
  });
  page.on('request', (request) => {
    errors.push(`unexpected network request: ${request.url()}`);
  });
  return errors;
}

const pages = publicPaths();

test('all public pages render without runtime or responsive failures', async ({ page }) => {
  const runtimeErrors = [];
  let currentPath = '';
  page.on('pageerror', (error) => runtimeErrors.push(`${currentPath}: pageerror: ${error.message}`));
  page.on('console', (message) => {
    if (message.type() === 'error') runtimeErrors.push(`${currentPath}: console: ${message.text()}`);
  });
  page.on('request', (request) => {
    runtimeErrors.push(`${currentPath}: unexpected network request: ${request.url()}`);
  });

  const failures = [];
  for (const path of pages) {
    currentPath = path;
    await test.step(path, async () => {
      await page.setContent(browserDocument(path), { waitUntil: 'load' });
      const contract = await page.evaluate(() => {
        const visible = (element) => {
          if (!element) return false;
          const style = getComputedStyle(element);
          const rect = element.getBoundingClientRect();
          return style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0;
        };
        const ids = [...document.querySelectorAll('[id]')].map((element) => element.id);
        const duplicateIds = [...new Set(ids.filter((id, index) => ids.indexOf(id) !== index))];
        const invalidLinks = [...document.querySelectorAll('a[href]')]
          .map((anchor) => anchor.getAttribute('href'))
          .filter((href) => !href || href.trim() === '' || href.startsWith('javascript:'));
        const canonical = [...document.querySelectorAll('link[rel="canonical"]')];
        const robots = document.querySelector('meta[name="robots"]')?.getAttribute('content') || '';
        return {
          readyState: document.readyState,
          mainCount: document.querySelectorAll('main#main').length,
          mainVisible: visible(document.querySelector('main#main')),
          h1Count: document.querySelectorAll('h1').length,
          h1Visible: visible(document.querySelector('h1')),
          canonicalCount: canonical.length,
          canonical: canonical[0]?.getAttribute('href') || '',
          title: document.title.trim(),
          robots,
          duplicateIds,
          invalidLinks,
          htmlScrollWidth: document.documentElement.scrollWidth,
          htmlClientWidth: document.documentElement.clientWidth,
          bodyScrollWidth: document.body.scrollWidth,
          bodyClientWidth: document.body.clientWidth,
        };
      });

      const expectedCanonical = `${PUBLIC_ORIGIN}${path}`;
      const checks = [
        [contract.readyState === 'complete', `readyState=${contract.readyState}`],
        [contract.mainCount === 1, `main#main count=${contract.mainCount}`],
        [contract.mainVisible, 'main#main is not visible'],
        [contract.h1Count === 1, `h1 count=${contract.h1Count}`],
        [contract.h1Visible, 'h1 is not visible'],
        [contract.canonicalCount === 1, `canonical count=${contract.canonicalCount}`],
        [contract.canonical === expectedCanonical, `canonical=${contract.canonical}`],
        [contract.title.length > 0, 'title is empty'],
        [path === '/404.html' ? contract.robots === 'noindex,follow' : !contract.robots.includes('noindex'), `robots=${contract.robots}`],
        [contract.duplicateIds.length === 0, `duplicate IDs=${contract.duplicateIds.join(',')}`],
        [contract.invalidLinks.length === 0, `invalid links=${contract.invalidLinks.join(',')}`],
        [contract.htmlScrollWidth <= contract.htmlClientWidth + 1, `html overflow ${contract.htmlScrollWidth}>${contract.htmlClientWidth}`],
        [contract.bodyScrollWidth <= contract.bodyClientWidth + 1, `body overflow ${contract.bodyScrollWidth}>${contract.bodyClientWidth}`],
      ];
      for (const [ok, message] of checks) {
        if (!ok) failures.push(`${path}: ${message}`);
      }
    });
  }

  failures.push(...runtimeErrors);
  expect(failures).toEqual([]);
});

test('analytics runtime initializes both providers without external requests', async ({ page }) => {
  const errors = observeRuntime(page);
  await page.setContent('<!doctype html><html><head></head><body></body></html>');
  await page.evaluate(() => {
    window.__appendedScripts = [];
    const original = document.head.appendChild.bind(document.head);
    document.head.appendChild = (node) => {
      if (node instanceof HTMLScriptElement && /^https:\/\//.test(node.src)) {
        window.__appendedScripts.push(node.src);
        return node;
      }
      return original(node);
    };
  });
  await page.addScriptTag({ content: readFileSync('assets/kozeni-analytics.v1.js', 'utf8') });

  const state = await page.evaluate(() => ({
    loaded: window.__kozeniAnalyticsLoaded,
    dataLayerLength: window.dataLayer?.length,
    scripts: window.__appendedScripts,
  }));
  expect(state.loaded).toBe(true);
  expect(state.dataLayerLength).toBe(2);
  expect(state.scripts).toEqual([
    'https://www.googletagmanager.com/gtag/js?id=G-V140MZBPKB',
    'https://www.clarity.ms/tag/wmurko5bi1',
  ]);
  expect(errors).toEqual([]);
});

test('home menu opens, closes with Escape, and restores focus', async ({ page }) => {
  const errors = observeRuntime(page);
  await page.setContent(browserDocument('/'), { waitUntil: 'load' });

  const button = page.locator('[data-foundation-menu-toggle]');
  const menu = page.locator('[data-foundation-menu]');
  await expect(button).toBeVisible();
  await expect(button).toHaveAttribute('aria-expanded', 'false');
  await expect(menu).toHaveAttribute('aria-hidden', 'true');
  await expect(menu).toHaveAttribute('inert', '');

  await button.click();
  await expect(button).toHaveAttribute('aria-expanded', 'true');
  await expect(menu).toHaveAttribute('aria-hidden', 'false');
  await expect(menu).not.toHaveAttribute('inert', '');
  await expect(page.locator('body')).toHaveClass(/foundation-menu-open/);

  await page.keyboard.press('Escape');
  await expect(button).toHaveAttribute('aria-expanded', 'false');
  await expect(menu).toHaveAttribute('aria-hidden', 'true');
  await expect(button).toBeFocused();
  expect(errors).toEqual([]);
});
