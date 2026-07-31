import type { Metadata } from "next";
import { Suspense } from "react";
import { buildMetadata } from "@/lib/seo";
import { ProductDetail } from "@/components/editorial/ProductDetail";

// Fiche produit générique (rendu client sous export statique). La version
// indexable par produit viendra avec la migration ISR/Vercel.
export const metadata: Metadata = buildMetadata({
  path: "/produit",
  title: "Fiche produit",
  description: "Le prix, l'historique et la meilleure offre d'un produit, comparés par FILON.",
});

export default function ProduitPage() {
  return (
    <section className="ed-band" style={{ paddingTop: "clamp(90px, 12vw, 130px)" }}>
      <div className="ed-wrap">
        <Suspense fallback={<p style={{ color: "var(--ink-3)" }}>…</p>}>
          <ProductDetail />
        </Suspense>
      </div>
    </section>
  );
}
