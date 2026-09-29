# Technical SEO fixes by stack

## Contents
- [Search Console, GA4, Bing](#search-console-ga4-bing)
- [Titles, meta, canonicals](#canonicals) (Next.js · Nuxt · Astro · WordPress · plain HTML)
- [Sitemaps and robots.txt](#sitemaps-and-robotstxt)
- [Redirects](#redirects)
- [JavaScript rendering](#javascript-rendering)
- [Core Web Vitals](#core-web-vitals)
- [Breadcrumbs](#breadcrumbs)
- [Structured data](#structured-data)

Detect the stack before editing: check `package.json` (next, nuxt, astro, @sveltejs/kit, gatsby, vite + vue/react), `wp-content/`, or static `.html` files. Use the framework's own metadata mechanism so tags stay unique and correct per route.

---

## Search Console, GA4, Bing

1. **GSC:** go to search.google.com/search-console > Add property > **Domain** (covers http/https/www/subdomains) and verify with the DNS TXT record at the registrar. Use a URL-prefix property only when DNS access is impossible.
2. **GA4:** go to analytics.google.com > create a property and a web data stream, then install the `G-XXXX` tag through gtag.js, GTM, or the framework integration (`@next/third-parties/google`, `nuxt-gtag`, a WordPress Site Kit plugin).
3. **Link them:** GA4 Admin > Product links > Search Console links.
4. **Bing:** go to bing.com/webmasters > Import from GSC (this imports the sites and sitemaps in one click). Optionally enable **IndexNow** so Bing and Yandex hear about updates quickly (many CMS plugins support it).
5. **Submit the sitemap** in GSC > Sitemaps (e.g. `sitemap.xml`) and in Bing > Sitemaps.

## Canonicals

Every indexable page needs a unique title and meta description, plus one absolute self-referencing canonical.

**Next.js (App Router)**
```ts
// app/layout.tsx - once, so relative canonicals resolve
export const metadata = { metadataBase: new URL('https://example.com') }

// app/blog/[slug]/page.tsx
export async function generateMetadata({ params }) {
  const { slug } = await params
  const post = await getPost(slug)
  return {
    title: post.seoTitle,                      // 50-60 chars
    description: post.seoDescription,          // ~120-160 chars
    alternates: { canonical: `/blog/${slug}` },
    openGraph: { title: post.seoTitle, description: post.seoDescription, images: [post.ogImage] },
  }
}
```
Pages Router: `<Head>` from `next/head` with `<link rel="canonical" href=... />`.

**Nuxt 3/4**
```ts
// pages/blog/[slug].vue <script setup>
const route = useRoute()
useSeoMeta({ title: post.seoTitle, description: post.seoDescription,
             ogTitle: post.seoTitle, ogDescription: post.seoDescription, ogImage: post.ogImage })
useHead({ link: [{ rel: 'canonical', href: `https://example.com${route.path}` }] })
```
The `@nuxtjs/seo` module (or its parts: `@nuxtjs/sitemap`, `@nuxtjs/robots`, `nuxt-schema-org`, `nuxt-og-image`) generates canonicals, sitemap, robots and schema from `site: { url }` in `nuxt.config`.

**Astro:** pass `title`, `description` and `canonicalURL = new URL(Astro.url.pathname, Astro.site)` into a shared `<BaseHead>` component. Set `site` in `astro.config.mjs`.

**SvelteKit:** use `<svelte:head>` in `+page.svelte`, with data from `+page.ts`.

**WordPress:** Yoast SEO or Rank Math handle titles, descriptions, canonicals, sitemaps, breadcrumbs and base schema. Configure the title templates there. Don't hard-code tags in the theme's `header.php`.

**Plain HTML**
```html
<title>Primary Keyword - Secondary Benefit | Brand</title>
<meta name="description" content="...">
<link rel="canonical" href="https://example.com/page">
<meta name="viewport" content="width=device-width, initial-scale=1">
```

Canonical rules: use absolute URLs, match the final URL exactly (protocol, host, trailing slash), and only one per page. Paginated pages self-canonicalize (don't point page 2 at page 1). Filtered or sorted variants point at the unfiltered URL.

## Sitemaps and robots.txt

**Next.js**
```ts
// app/sitemap.ts
import type { MetadataRoute } from 'next'
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const posts = await getPosts()
  return [
    { url: 'https://example.com/', lastModified: new Date() },
    ...posts.map(p => ({ url: `https://example.com/blog/${p.slug}`, lastModified: p.updatedAt })),
  ]
}
// app/robots.ts
export default function robots(): MetadataRoute.Robots {
  return { rules: { userAgent: '*', allow: '/', disallow: ['/api/', '/dashboard/'] },
           sitemap: 'https://example.com/sitemap.xml' }
}
```
**Nuxt:** `@nuxtjs/sitemap` + `@nuxtjs/robots`, configured by `site.url`. **Astro:** `@astrojs/sitemap`. **Static sites:** generate at build time. **WordPress:** core `wp-sitemap.xml`, or the SEO plugin's sitemap.

Rules for sitemap contents: include only canonical, indexable, 200-status URLs. Set `<lastmod>` only when the content actually changes. Keep each file under 50,000 URLs and 50 MB, and split with a sitemap index beyond that.

robots.txt template:
```
User-agent: *
Disallow: /api/
Disallow: /admin/
Sitemap: https://example.com/sitemap.xml
```
Never block CSS/JS or `/_next/static/`, `/_nuxt/`, `/assets/`: Google renders pages and needs them. To remove indexed pages, use `noindex` (with crawling allowed), not `Disallow`.

## Redirects

Use one hop, with a permanent status (301 or 308), from each old URL to its final destination.

| Where | Pattern |
|---|---|
| Next.js | `next.config.js` → `async redirects() { return [{ source: '/old', destination: '/new', permanent: true }] }` (308) |
| Nuxt | `routeRules: { '/old': { redirect: { to: '/new', statusCode: 301 } } }` |
| Vercel | `vercel.json` → `"redirects": [{ "source": "/old", "destination": "/new", "permanent": true }]` |
| Netlify | `_redirects` → `/old  /new  301` |
| Cloudflare | Bulk Redirects or a Redirect Rule |
| nginx | `location = /old { return 301 /new; }` and `server { server_name www.example.com; return 301 https://example.com$request_uri; }` |
| Apache | `Redirect 301 /old /new` |
| WordPress | Redirection plugin, or the SEO plugin's redirect manager |

Host consolidation: http→https and www↔apex should each land on the final origin in **one** hop. A common mistake is `http://www` → `https://www` → `https://apex`, which is two hops.

After a redirect ships, update internal links, canonicals and the sitemap to the new URL.

## JavaScript rendering

Google renders JavaScript, but later and less reliably than it processes HTML, and many AI crawlers don't render JS at all. Indexable content should be in the server response.

- **Next.js:** Server Components, SSG or ISR are the default. Don't fetch primary content in a client-side `useEffect`.
- **Nuxt:** SSR is the default. Use `routeRules` with `prerender: true` or `isr` for content pages, and never `ssr: false` on pages meant to rank.
- **Vite SPA (Vue/React):** migrate the content routes to Nuxt/Next/Astro, or prerender them (`vite-ssg`, `vite-plugin-prerender`, `react-snap`).
- **Links:** use `<a href="/path">` (NuxtLink and next/link render this). `<div onClick={navigate}>` is not crawlable.
- **Verify:** check that the `page` word count matches the rendered content, and use GSC URL Inspection > Test live URL > View tested page > HTML.

## Core Web Vitals

| Metric | Good | Most common fixes |
|---|---|---|
| **LCP** (largest paint) | ≤ 2.5 s | Serve the hero image as AVIF/WebP at the right size, add `fetchpriority="high"`, and never lazy-load it. Preload the hero font or image. Cut TTFB with a CDN and caching or SSG. Remove render-blocking CSS/JS. |
| **INP** (interaction delay) | ≤ 200 ms | Break up long tasks, defer third-party scripts (chat widgets, tag managers), reduce hydration cost (islands, lazy hydration), and avoid heavy work in input handlers. |
| **CLS** (layout shift) | ≤ 0.1 | Set `width`/`height` or `aspect-ratio` on images, video and embeds. Reserve space for ads and banners. Use `font-display: optional` or `swap` with size-adjusted fallbacks. Don't inject content above existing content. |

Framework helpers: `next/image` and `next/font`, `@nuxt/image` and `@nuxt/fonts`, and Astro `<Image>`. Measure again with `page --psi` after each change.

## Breadcrumbs

Show a visible trail (Home › Category › Page) and add JSON-LD that matches it:
```json
{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
 {"@type":"ListItem","position":1,"name":"Home","item":"https://example.com/"},
 {"@type":"ListItem","position":2,"name":"Blog","item":"https://example.com/blog"},
 {"@type":"ListItem","position":3,"name":"Post title"}]}
```

## Structured data

Use JSON-LD in `<script type="application/ld+json">`. Mark up only what is visible on the page.

| Page | Types |
|---|---|
| Homepage | `Organization` (name, url, logo, sameAs social profiles) + `WebSite` |
| Article/blog | `Article`/`BlogPosting` with `headline`, `author` (`Person` with url), `datePublished`, `dateModified`, `image` |
| Product/SaaS | `Product` with `offers`/`aggregateRating` only if real. `SoftwareApplication` for apps. |
| Local business | `LocalBusiness` (or subtype) with NAP, `openingHours`, `geo` |
| Inner pages | `BreadcrumbList` |
| Video | `VideoObject` |

Next.js injection (escape `<` to prevent script injection):
```tsx
<script type="application/ld+json"
  dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, '\\u003c') }} />
```
Nuxt: `useSchemaOrg([...])` from `nuxt-schema-org`, or `useHead({ script: [{ type: 'application/ld+json', innerHTML: JSON.stringify(jsonLd) }] })`.

Validate with the Rich Results Test (search.google.com/test/rich-results) and validator.schema.org. Then watch GSC > Enhancements for errors.
