# Get pages out of Google (and the FAQ schema question)

**Skill:** `seo-technical`. Claude explains the robots.txt vs noindex trap, gives Next.js code for each option, and heads off an FAQ-schema plan that wouldn't work anyway.

## You

> Two questions about my Next.js blog. 1) I added `Disallow: /old-blog/` to robots.txt three weeks ago to get 200 outdated posts out of Google, but they still show up (with no description). Why, and how do I actually remove them? 2) Should I add FAQPage schema to every post so we get the FAQ dropdowns in Google results?

## Claude

### 1) Why the old posts are still in Google

`robots.txt` controls crawling. It doesn't control indexing. `Disallow: /old-blog/` tells Googlebot not to fetch those pages. Google already knows the URLs, though, and other pages and sitemaps still link to them, so it keeps them in the index. It just can't read them anymore. That's why they show with no description ("No information is available for this page"). The Disallow also stops Google from seeing any `noindex` or 404 you add to those pages, so as long as it's there the URLs can stay indexed indefinitely.

**How to actually remove them:**

1. **Remove the `Disallow: /old-blog/` line.** Google has to be able to crawl the pages to see that they're gone.
2. **Give each URL a clear signal.** Pick one per post:
   - **301 redirect** to a newer post on the same topic. This keeps any backlinks. Use it wherever you have a real replacement.
   - **410 Gone (or 404)** if the post is simply dead. 410 is slightly faster.
   - **`noindex`** if you want people to still be able to open the page but don't want it in Google.

   In Next.js:
   ```js
   // next.config.js: noindex the whole section via header
   async headers() {
     return [{ source: '/old-blog/:path*', headers: [{ key: 'X-Robots-Tag', value: 'noindex' }] }];
   },
   // or redirect ones that have a replacement
   async redirects() {
     return [{ source: '/old-blog/some-post', destination: '/blog/some-post-2026', permanent: true }];
   },
   ```
   For the App Router, you can instead put `export const metadata = { robots: { index: false } }` in the old-blog page. For a 410, return `new NextResponse(null, { status: 410 })` from `middleware.ts` for `/old-blog/:path*`. Calling `notFound()` gives a 404, which also works.
3. **Hide them now while that takes effect.** In Search Console, go to Indexing → Removals → New request and use "Remove all URLs with this prefix" for `/old-blog/`. This hides them for about 6 months while Google recrawls and drops them for good. The Removals tool on its own is only temporary, so you still need step 2.
4. **Optional, to speed things up:** submit a temporary sitemap that lists only the old URLs so Google recrawls them sooner. Delete it once they've dropped out. Also remove the old URLs from your main sitemap and from any internal links.
5. After they're gone, which usually takes a few weeks, you can add the Disallow back if you want to, but you don't need it.

### 2) FAQPage schema on every post: no

- **You won't get the dropdowns.** Since August 2023, Google only shows FAQ rich results for well-known, authoritative government and health sites. A regular blog won't get them, whatever markup it has.
- **It can hurt you.** Structured data has to match content that's visible on the page. Adding FAQPage to posts that don't have a real Q&A section breaks Google's guidelines and can lead to a manual action for spammy structured data.
- **What to do instead:**
  - Add `BlogPosting` (or `Article`) JSON-LD to each post, with `headline`, `author` (linked to an author page), `datePublished`, `dateModified` and `image`.
  - Add `BreadcrumbList`.

  Those are what help Google understand your posts and qualify them for article features. If a post really does have an FAQ section on the page, marking it up is harmless and helps search engines and AI answer tools understand it, but it won't produce dropdowns. Check it with the Rich Results Test.

There's no Next.js code in this working directory, so I couldn't look at your actual robots/sitemap setup. If you point me at the repo, I can make these changes: the old-blog redirects or noindex, cleaning up the sitemap, and adding BlogPosting schema.
---
<sub>Real, unedited output recorded on 2026-09-29 during the plugin's eval run (Claude Code, Opus 5.5, seo-checklist v1.0.0). "Acme Invoice" is a fictional demo company.</sub>
