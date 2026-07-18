import type { Metadata } from "next";
import { site } from "./site";

/** Build page metadata with sensible FILON defaults + Open Graph / Twitter. */
export function buildMetadata(input: {
  title?: string;
  description?: string;
  path?: string;
}): Metadata {
  const title = input.title ? `${input.title} — ${site.name}` : `${site.name} — ${site.tagline}`;
  const description = input.description ?? site.description;
  const url = `${site.url}${input.path ?? "/"}`;

  const ogImage = { url: "/og.png", width: 1200, height: 630, alt: `${site.name} — ${site.tagline}` };

  return {
    title,
    description,
    alternates: { canonical: url },
    openGraph: {
      type: "website",
      locale: site.locale,
      url,
      siteName: site.name,
      title,
      description,
      images: [ogImage],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      site: site.twitter,
      images: ["/og.png"],
    },
  };
}

/** JSON-LD: Organization. */
export function organizationSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: site.name,
    url: site.url,
    description: site.description,
    founder: { "@type": "Person", name: site.founder },
    slogan: site.tagline,
    address: { "@type": "PostalAddress", addressLocality: site.city, addressCountry: "BE" },
  };
}

/** JSON-LD: WebSite with a search action. */
export function websiteSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: site.name,
    url: site.url,
    inLanguage: "fr",
    potentialAction: {
      "@type": "SearchAction",
      target: `${site.url}/recherche?q={query}`,
      "query-input": "required name=query",
    },
  };
}

/** JSON-LD: FAQPage from a list of Q/A. */
export function faqSchema(items: { q: string; a: string }[]) {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: items.map((it) => ({
      "@type": "Question",
      name: it.q,
      acceptedAnswer: { "@type": "Answer", text: it.a },
    })),
  };
}

/** JSON-LD: Article (blog posts). */
export function articleSchema(a: { title: string; description: string; path: string; datePublished: string }) {
  return {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: a.title,
    description: a.description,
    author: { "@type": "Organization", name: site.name },
    publisher: {
      "@type": "Organization",
      name: site.name,
      logo: { "@type": "ImageObject", url: `${site.url}/icon.png` },
    },
    datePublished: a.datePublished,
    dateModified: a.datePublished,
    mainEntityOfPage: `${site.url}${a.path}`,
    image: `${site.url}/og.png`,
    inLanguage: "fr",
  };
}

/** JSON-LD: BreadcrumbList. */
export function breadcrumbSchema(items: { name: string; path: string }[]) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((it, i) => ({
      "@type": "ListItem",
      position: i + 1,
      name: it.name,
      item: `${site.url}${it.path}`,
    })),
  };
}

/** Small helper to render a JSON-LD <script> safely. */
export function JsonLd({ data }: { data: unknown }) {
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }}
    />
  );
}
