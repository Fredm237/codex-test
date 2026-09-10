import type { Metadata } from "next";
import { notFound } from "next/navigation";
import "@/components/immersive-lab/immersive-lab.global.css";
import { ImmersiveLab } from "@/components/immersive-lab/ImmersiveLab";
import { getImmersiveExactProductProof } from "@/lib/immersive-proof";
import { isImmersiveLabEnabled } from "@/lib/immersive-lab-access";
import { getProof } from "@/lib/proof";

export const metadata: Metadata = {
  title: "Laboratoire immersif — FILON",
  description: "Prototype isolé de la grammaire visuelle immersive FILON.",
  robots: { index: false, follow: false },
};

export const revalidate = 600;

export default async function ImmersiveExperienceLabPage() {
  if (!isImmersiveLabEnabled()) notFound();

  const [proof, exactProduct] = await Promise.all([
    getProof(),
    getImmersiveExactProductProof(),
  ]);
  return <ImmersiveLab proof={proof} exactProduct={exactProduct} />;
}
