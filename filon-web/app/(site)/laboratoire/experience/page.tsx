import type { Metadata } from "next";
import { ImmersiveLab } from "@/components/immersive-lab/ImmersiveLab";
import { getImmersiveExactProductProof } from "@/lib/immersive-proof";
import { getProof } from "@/lib/proof";

export const metadata: Metadata = {
  title: "Laboratoire immersif — FILON",
  description: "Prototype isolé de la grammaire visuelle immersive FILON.",
  robots: { index: false, follow: false },
};

export const revalidate = 600;

export default async function ImmersiveExperienceLabPage() {
  const [proof, exactProduct] = await Promise.all([
    getProof(),
    getImmersiveExactProductProof(),
  ]);
  return <ImmersiveLab proof={proof} exactProduct={exactProduct} />;
}
