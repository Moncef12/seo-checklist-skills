# Content templates

## Contents
- [Content plan](#content-plan)
- [Page brief](#page-brief)
- [Comparison page (X vs Y)](#comparison-page)
- [Alternatives page](#alternatives-page)
- [Best-X listicle](#best-x-listicle)
- [Feature page](#feature-page)
- [Use-case / audience page](#use-case-page)
- [Author bio block](#author-bio-block)

---

## Content plan

| Priority | Keyword | Volume | KD | Intent | Page type | URL (new/existing) | Cluster | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | invoice software for freelancers | 1,900 | 18 | commercial | landing | /freelancers (new) | Invoicing | competitor X ranks #2 with thin page |

Put quick consolidations and refreshes above net-new pages, since they usually pay off faster.

## Page brief

```
Target keyword: ...        Secondary: ...        Intent: ...
SERP pattern: <what the top 5 are, their length, angle, and features like PAA or video>
Title (50-60): ...         Meta (120-160): ...    URL: /...
H1: ...
First 2 lines (the answer): ...
Outline: H2 ... / H3 ...  (cover the PAA questions as H2/H3s)
Must include: <original data, screenshots, table, FAQ>
Internal links: to <pillar>, <money page>; from <pages to update>
Schema: Article + BreadcrumbList (+ Product/SoftwareApplication if relevant)
```

## Comparison page

**Title:** `[You] vs [Competitor]: [Key Difference] ([Year])`

1. **TL;DR verdict** in the first two lines: who each tool is best for.
2. **At-a-glance table:** pricing (dated), key features, integrations, support, ideal user.
3. **Where [Competitor] is better.** Be honest; this section builds trust.
4. **Where [You] are better,** with proof (screenshots, benchmarks, reviews).
5. **Pricing compared,** with the date and a source link.
6. **Migration / switching** (if relevant).
7. **FAQ,** taken from PAA.
8. **CTA.**

Keep it fair: no invented weaknesses, current information only, and cite sources.

## Alternatives page

**Title:** `[N] Best [Competitor] Alternatives in [Year] (Free & Paid)`

1. **Why people look for alternatives:** real reasons from reviews, Reddit and G2.
2. **Quick list table:** tool, best for, price from, standout feature.
3. **One section per alternative:** a summary, pros, cons, pricing, and who it's for. Place yourself honestly, and explain why.
4. **How we chose** (methodology).
5. **FAQ.**

## Best-X listicle

**Title:** `[N] Best [Category] for [Audience] in [Year]`

1. **Top picks in the first two lines** (best overall, best budget, best for X).
2. **Comparison table.**
3. **Per item:** a screenshot, what it is, key features, pros and cons, pricing, and a "choose if..." line.
4. **Buying criteria / methodology.**
5. **FAQ.**

Update it at least yearly. Change the year in the title only when the content is actually refreshed.

## Feature page

**Title:** `[Feature] for [Audience/Outcome] | [Brand]`
1. The outcome headline plus a one-line answer of what the feature does.
2. How it works in 3 steps, with visuals.
3. Use cases and examples.
4. Proof: a metric, testimonial or logo.
5. Related features (internal links).
6. FAQ.
7. CTA.

## Use-case page

**Title:** `[Product Category] for [Audience]: [Specific Outcome]`
1. The audience's specific pain in their own words.
2. How the product solves *their* workflow. This must differ materially from other use-case pages.
3. A template, example or case study specific to the audience.
4. Features that matter most to them (with links).
5. Testimonial from that audience.
6. FAQ.
7. CTA.

If you can't write section 2 differently from another use-case page, don't create the page. Doorway pages hurt the whole site.

## Author bio block

```html
<aside class="author">
  <img src="/authors/jane.webp" alt="Jane Doe" width="64" height="64">
  <p><a href="/authors/jane-doe">Jane Doe</a> is a CPA with 12 years in small-business accounting.
     She has reviewed 40+ invoicing tools. <a href="https://www.linkedin.com/in/...">LinkedIn</a></p>
</aside>
```
```json
"author": {"@type":"Person","name":"Jane Doe","url":"https://example.com/authors/jane-doe",
           "jobTitle":"CPA","sameAs":["https://www.linkedin.com/in/..."]}
```
