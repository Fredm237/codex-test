import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, InfoGrid, ClosingCta } from "@/components/editorial/ContentPage";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/transparence",
  title: "Transparence & affiliation",
  description:
    "Comment FILON gagne de l'argent : liens d'affiliation, sans surcoût pour vous, sans jamais fausser un conseil. Neutralité, gratuité et clarté, expliquées.",
});

function TransparenceFR() {
  return (
    <>
      <ContentHero
        eyebrow="Transparence"
        title={
          <>
            Comment FILON gagne sa vie, <span className="it">sans jamais vous coûter plus cher</span>.
          </>
        }
        intro={
          <>
            Un service gratuit doit s&apos;expliquer. Voici, sans détour, notre modèle : d&apos;où vient
            l&apos;argent, ce que ça change pour vous (rien), et ce que nous nous interdisons.
          </>
        }
        breadcrumb={[{ name: "Transparence", path: "/transparence" }]}
      />

      <ProseBlock heading={<>Nous sommes rémunérés par <span className="it">l&apos;affiliation</span>.</>}>
        <p>
          Quand vous cliquez sur «&nbsp;Voir l&apos;offre&nbsp;» et que vous achetez chez un marchand, celui-ci peut
          nous verser une <b>commission d&apos;affiliation</b>. C&apos;est notre source de revenus.
        </p>
        <p>
          Point essentiel&nbsp;: cette commission est payée par le <b>marchand</b>, prélevée sur sa marge. Elle
          <b> n&apos;augmente jamais le prix que vous payez</b>. Vous payez exactement le même montant qu&apos;en
          allant directement sur le site du marchand.
        </p>
        <p style={{ color: "var(--ink-3)", fontSize: 14 }}>
          En clair, comme l&apos;exige la réglementation (DGCCRF, ARPP) et nos partenaires&nbsp;: certains liens de
          ce site sont des liens affiliés. Cliquer dessus et acheter peut nous rapporter une commission, sans coût
          supplémentaire pour vous.
        </p>
      </ProseBlock>

      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-lead">
            <span className="idx">Nos règles</span>
            <h2>
              Ce que la rémunération ne change <span className="it">jamais</span>.
            </h2>
          </div>
          <InfoGrid
            items={[
              {
                n: "01",
                h: "Aucun classement acheté",
                p: "Un marchand qui nous rémunère mieux n'obtient pas une meilleure place, ni un meilleur Score. Le classement suit votre intérêt, point.",
              },
              {
                n: "02",
                h: "Le meilleur prix d'abord",
                p: "Si l'offre la moins chère ne nous rapporte rien, c'est quand même elle que nous vous montrons. Toujours.",
              },
              {
                n: "03",
                h: "Sans publicité",
                p: "Pas de bannières, pas de placements déguisés. Rien ne vient troubler le conseil que vous recevez.",
              },
              {
                n: "04",
                h: "Gratuit, pour de vrai",
                p: "Aucun abonnement, aucune carte bancaire, aucune option payante. Vous ne payez jamais FILON.",
              },
              {
                n: "05",
                h: "Vos données restent à vous",
                p: "Mesure d'audience sans cookie et anonyme (Plausible). Aucun profil publicitaire, aucune revente.",
              },
              {
                n: "06",
                h: "Le raisonnement est ouvert",
                p: "Le Score se décompose critère par critère. Vous voyez pourquoi une offre est recommandée.",
              },
            ]}
          />
        </div>
      </section>

      <ProseBlock heading={<>Quand l&apos;information manque, on le <span className="it">dit</span>.</>} alt>
        <p>
          Les offres et l&apos;historique ne sont pas disponibles avec la même profondeur pour chaque produit. Une
          garantie, une alternative comparable ou un historique suffisant peuvent manquer.
        </p>
        <p>
          Dans ce cas, FILON ne transforme pas une hypothèse en recommandation&nbsp;: l&apos;information est absente,
          ou le verdict indique que le suivi est trop récent.
        </p>
        <p>
          Notre seul actif, c&apos;est votre confiance&nbsp;: nous préférons afficher «&nbsp;on ne sait pas encore&nbsp;»
          plutôt qu&apos;un beau chiffre faux.
        </p>
      </ProseBlock>

      <ClosingCta
        title={<>Un conseil de votre côté, <span className="it">rien d&apos;autre.</span></>}
        sub="Demandez à FILON avant d'acheter. Gratuit, neutre, sans publicité."
      />
    </>
  );
}

function TransparenceNL() {
  return (
    <>
      <ContentHero
        eyebrow="Transparantie"
        title={
          <>
            Hoe FILON zijn brood verdient, <span className="it">zonder je ooit meer te kosten</span>.
          </>
        }
        intro={
          <>
            Een gratis dienst moet zich verantwoorden. Hier, zonder omwegen, ons model : waar het geld vandaan komt,
            wat het voor jou verandert (niets), en wat we onszelf verbieden.
          </>
        }
        breadcrumb={[{ name: "Transparantie", path: "/transparence" }]}
      />

      <ProseBlock heading={<>We worden vergoed via <span className="it">affiliatie</span>.</>}>
        <p>
          Wanneer je op «&nbsp;Bekijk het aanbod&nbsp;» klikt en bij een winkel koopt, kan die ons een{" "}
          <b>affiliatiecommissie</b> betalen. Dat is onze inkomstenbron.
        </p>
        <p>
          Essentieel punt&nbsp;: die commissie wordt betaald door de <b>winkel</b>, afgehouden van zijn marge. Ze
          <b> verhoogt nooit de prijs die jij betaalt</b>. Je betaalt exact hetzelfde bedrag als wanneer je
          rechtstreeks naar de website van de winkel gaat.
        </p>
        <p style={{ color: "var(--ink-3)", fontSize: 14 }}>
          In klare taal, zoals de regelgeving en onze partners het eisen&nbsp;: sommige links op deze site zijn
          affiliatielinks. Erop klikken en kopen kan ons een commissie opleveren, zonder extra kost voor jou.
        </p>
      </ProseBlock>

      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-lead">
            <span className="idx">Onze regels</span>
            <h2>
              Wat de vergoeding <span className="it">nooit</span> verandert.
            </h2>
          </div>
          <InfoGrid
            items={[
              {
                n: "01",
                h: "Geen gekochte rangschikking",
                p: "Een winkel die ons beter vergoedt, krijgt geen betere plaats, noch een betere Score. De rangschikking volgt jouw belang, punt.",
              },
              {
                n: "02",
                h: "De beste prijs eerst",
                p: "Als het goedkoopste aanbod ons niets opbrengt, is het toch dat wat we je tonen. Altijd.",
              },
              {
                n: "03",
                h: "Zonder reclame",
                p: "Geen banners, geen verkapte plaatsingen. Niets komt het advies dat je krijgt verstoren.",
              },
              {
                n: "04",
                h: "Gratis, echt waar",
                p: "Geen abonnement, geen bankkaart, geen betalende optie. Je betaalt FILON nooit.",
              },
              {
                n: "05",
                h: "Je gegevens blijven van jou",
                p: "Bezoekersmeting zonder cookie en anoniem (Plausible). Geen advertentieprofiel, geen doorverkoop.",
              },
              {
                n: "06",
                h: "De redenering ligt open",
                p: "De Score wordt criterium per criterium ontleed. Je ziet waarom een aanbod aanbevolen is.",
              },
            ]}
          />
        </div>
      </section>

      <ProseBlock heading={<>Wanneer informatie ontbreekt, <span className="it">zeggen we dat</span>.</>} alt>
        <p>
          Aanbiedingen en prijsgeschiedenis zijn niet voor elk product even volledig beschikbaar. Een garantie,
          vergelijkbaar alternatief of voldoende geschiedenis kan ontbreken.
        </p>
        <p>
          In dat geval maakt FILON van een aanname geen aanbeveling: de informatie ontbreekt, of het oordeel geeft
          aan dat de opvolging te recent is.
        </p>
        <p>
          Onze enige troef is je vertrouwen: we tonen liever «&nbsp;dat weten we nog niet&nbsp;» dan een mooi vals cijfer.
        </p>
      </ProseBlock>

      <ClosingCta
        title={<>Advies aan jouw kant, <span className="it">niets anders.</span></>}
        sub="Vraag het aan FILON vóór je koopt. Gratis, neutraal, zonder reclame."
      />
    </>
  );
}

function TransparenceEN() {
  return (
    <>
      <ContentHero
        eyebrow="Transparency"
        title={
          <>
            How FILON makes a living, <span className="it">without ever costing you more</span>.
          </>
        }
        intro={
          <>
            A free service owes an explanation. Here, plainly, is our model: where the money comes from, what it
            changes for you (nothing), and what we forbid ourselves.
          </>
        }
        breadcrumb={[{ name: "Transparency", path: "/transparence" }]}
      />

      <ProseBlock heading={<>We&apos;re paid through <span className="it">affiliation</span>.</>}>
        <p>
          When you click « See the offer » and buy from a merchant, that merchant may pay us an{" "}
          <b>affiliation commission</b>. That&apos;s our source of income.
        </p>
        <p>
          Key point&nbsp;: this commission is paid by the <b>merchant</b>, taken from its margin. It
          <b> never increases the price you pay</b>. You pay exactly the same amount as going directly to the
          merchant&apos;s site.
        </p>
        <p style={{ color: "var(--ink-3)", fontSize: 14 }}>
          In plain terms, as the regulations and our partners require&nbsp;: some links on this site are affiliate
          links. Clicking them and buying may earn us a commission, at no extra cost to you.
        </p>
      </ProseBlock>

      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-lead">
            <span className="idx">Our rules</span>
            <h2>
              What the income <span className="it">never</span> changes.
            </h2>
          </div>
          <InfoGrid
            items={[
              {
                n: "01",
                h: "No ranking is bought",
                p: "A merchant that pays us more doesn't get a better place, nor a better Score. The ranking follows your interest, full stop.",
              },
              {
                n: "02",
                h: "The best price first",
                p: "If the cheapest offer earns us nothing, it's still the one we show you. Always.",
              },
              {
                n: "03",
                h: "No advertising",
                p: "No banners, no disguised placements. Nothing disturbs the recommendation you receive.",
              },
              {
                n: "04",
                h: "Free, for real",
                p: "No subscription, no credit card, no paid option. You never pay FILON.",
              },
              {
                n: "05",
                h: "Your data stays yours",
                p: "Cookie-free, anonymous audience measurement (Plausible). No advertising profile, no reselling.",
              },
              {
                n: "06",
                h: "The reasoning is open",
                p: "The Score breaks down criterion by criterion. You see why an offer is recommended.",
              },
            ]}
          />
        </div>
      </section>

      <ProseBlock heading={<>When information is missing, we <span className="it">say so</span>.</>} alt>
        <p>
          Offers and price history are not available with the same depth for every product. A warranty, comparable
          alternative or sufficient history may be missing.
        </p>
        <p>
          In that case, FILON does not turn an assumption into a recommendation: the information is unavailable, or
          the verdict states that tracking is still too recent.
        </p>
        <p>
          Trust is our only asset: we&apos;d rather show « we don&apos;t know yet » than a nice but false figure.
        </p>
      </ProseBlock>

      <ClosingCta
        title={<>Advice on your side, <span className="it">nothing else.</span></>}
        sub="Ask FILON before you buy. Free, neutral, ad-free."
      />
    </>
  );
}

export default function TransparencePage() {
  return <Localized fr={<TransparenceFR />} nl={<TransparenceNL />} en={<TransparenceEN />} />;
}
