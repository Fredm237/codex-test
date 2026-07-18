import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ClosingCta } from "@/components/editorial/ContentPage";
import { FaqBlock } from "@/components/editorial/Faq";
import { Reveal } from "@/components/editorial/Reveal";

export const metadata: Metadata = buildMetadata({
  path: "/tarifs",
  title: "Tarifs — gratuit, et Filon Pro",
  description:
    "FILON est gratuit pour toujours : le copilote d'achat qui trouve le meilleur prix réel avant chaque commande. Filon Pro (7,99€/mois) ajoute les alertes de prix, l'historique illimité et la protection anti-mauvais-achat.",
});

const FAQ = [
  { q: "FILON restera-t-il gratuit ?", a: "Oui. Le cœur de FILON — l'analyse d'achat, la comparaison cashback / reconditionné / codes promo et le verdict « acheter ou attendre » — est gratuit et le restera. Nous nous rémunérons via une part de la commission d'apport des plateformes partenaires, jamais en vous facturant." },
  { q: "Qu'apporte Filon Pro de plus ?", a: "Pro s'adresse à celles et ceux qui achètent souvent : alertes automatiques dès qu'un prix baisse, historique de prix illimité, recommandations personnalisées selon vos usages, et la protection anti-mauvais-achat qui vous alerte avant une décision risquée (prix gonflé, vendeur peu fiable, meilleure alternative)." },
  { q: "Puis-je annuler Filon Pro à tout moment ?", a: "Oui, sans engagement ni frais. Vous gardez l'accès jusqu'à la fin de la période payée, puis vous repassez automatiquement sur la version gratuite." },
  { q: "Le prix payé change-t-il si je passe par FILON ?", a: "Jamais. Que vous soyez gratuit ou Pro, le prix chez le marchand est identique. FILON ne fait que vous orienter vers le meilleur coût réel — la commission d'apport est payée par la plateforme, pas par vous." },
];

export default function TarifsPage() {
  return (
    <>
      <ContentHero
        eyebrow="Tarifs"
        title={<>Gratuit pour décider mieux. <span className="it">Pro</span> pour ne rien rater.</>}
        intro="Le copilote d'achat de FILON est gratuit — et le restera. Pour celles et ceux qui achètent souvent, Filon Pro ajoute la surveillance des prix et la protection avant chaque décision."
        breadcrumb={[{ name: "Tarifs", path: "/tarifs" }]}
      />

      <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="ed-wrap">
          <Reveal>
            <div className="ed-pricing">
              <div className="ed-plan">
                <span className="tag">Toujours gratuit</span>
                <div className="name">Filon</div>
                <div className="price">0€ <small>/ pour toujours</small></div>
                <p className="lede">Le copilote d&apos;achat complet. Posez votre besoin, obtenez le meilleur coût réel et le verdict « acheter ou attendre ».</p>
                <ul>
                  <li>Analyse d&apos;achat par l&apos;IA (besoin → recommandation)</li>
                  <li>Comparaison cashback, reconditionné et codes promo</li>
                  <li>Verdict « acheter maintenant » ou « attendre »</li>
                  <li>Meilleur vendeur et prix réel le plus bas</li>
                  <li>Extension navigateur incluse</li>
                  <li className="off">Alertes automatiques de baisse de prix</li>
                  <li className="off">Historique de prix illimité</li>
                  <li className="off">Protection anti-mauvais-achat</li>
                </ul>
                <div className="cta-wrap">
                  <a className="ed-btn" href="/#installer" style={{ textDecoration: "none" }}>Commencer gratuitement</a>
                </div>
              </div>

              <div className="ed-plan featured">
                <span className="tag">Filon Pro</span>
                <div className="name">Pro</div>
                <div className="price">7,99€ <small>/ mois · sans engagement</small></div>
                <p className="lede">Pour acheter souvent, sans jamais surpayer. Tout le gratuit, plus la surveillance et la protection en continu.</p>
                <ul>
                  <li><b>Tout ce qui est inclus dans la version gratuite</b></li>
                  <li>Alertes automatiques dès qu&apos;un prix baisse</li>
                  <li>Historique de prix illimité</li>
                  <li>Recommandations personnalisées selon vos usages</li>
                  <li>Analyse approfondie avant achat</li>
                  <li>Protection anti-mauvais-achat (vendeur, prix gonflé, alternative)</li>
                  <li>Listes intelligentes et suivi de souhaits</li>
                </ul>
                <div className="cta-wrap">
                  <a className="ed-btn wave" href="/#installer" style={{ textDecoration: "none" }}>Rejoindre la liste Pro</a>
                </div>
              </div>
            </div>
          </Reveal>
          <p style={{ textAlign: "center", color: "var(--ink-3)", fontSize: 13.5, marginTop: 22 }}>
            Le prix chez le marchand est le même dans les deux cas. FILON ne facture jamais l&apos;utilisateur pour trouver le meilleur prix.
          </p>
        </div>
      </section>

      <FaqBlock items={FAQ} eyebrow="Tarifs · FAQ" title="Ce que « gratuit » veut vraiment dire." />
      <ClosingCta title={<>Commencez <span className="it">gratuitement</span>.</>} sub="Le copilote d'achat, sans carte bancaire. Passez à Pro seulement si vous achetez souvent." />
    </>
  );
}
