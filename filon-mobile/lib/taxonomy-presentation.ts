import type MaterialIcons from "@expo/vector-icons/MaterialIcons";
import type { ComponentProps } from "react";

export type TaxonomyLocale = "fr" | "nl" | "en";

type IconName = ComponentProps<typeof MaterialIcons>["name"];
type TaxonomyLabels = Readonly<Record<TaxonomyLocale, string>>;

const labels = (fr: string, nl: string, en: string): TaxonomyLabels => ({ fr, nl, en });

export const FILON_DEPARTMENT_LABELS = {
  "mode-accessoires": labels("Mode & Accessoires", "Mode & accessoires", "Fashion & Accessories"),
  "high-tech": labels("High-Tech", "Elektronica", "Tech"),
  maison: labels("Maison", "Wonen", "Home"),
  "beaute-sante": labels("Beauté & Santé", "Schoonheid & Gezondheid", "Beauty & Health"),
  "sport-loisirs": labels("Sport & Loisirs", "Sport & Vrije tijd", "Sports & Leisure"),
  "famille-quotidien": labels("Famille & Quotidien", "Gezin & Dagelijks leven", "Family & Everyday"),
  voyages: labels("Voyages", "Reizen", "Travel"),
} as const satisfies Record<string, TaxonomyLabels>;

export const FILON_CATEGORY_LABELS = {
  informatique: labels("Informatique", "Computers", "Computing"),
  telephonie: labels("Téléphonie", "Telefonie", "Phones"),
  photo: labels("Photo", "Fotografie", "Photography"),
  gaming: labels("Gaming", "Gaming", "Gaming"),
  "tv-son": labels("TV & Son", "TV & Audio", "TV & Audio"),
  electromenager: labels("Électroménager", "Huishoudtoestellen", "Home Appliances"),
  "maison-deco": labels("Maison & Déco", "Wonen & Decoratie", "Home & Decor"),
  "jardin-bricolage": labels("Jardin & Bricolage", "Tuin & Klussen", "Garden & DIY"),
  "mode-femme": labels("Mode femme", "Damesmode", "Women's Fashion"),
  "mode-homme": labels("Mode homme", "Herenmode", "Men's Fashion"),
  "mode-enfant": labels("Mode enfant", "Kindermode", "Kids' Fashion"),
  chaussures: labels("Chaussures", "Schoenen", "Shoes"),
  "bijoux-montres": labels("Bijoux & Montres", "Sieraden & Horloges", "Jewellery & Watches"),
  "beaute-parfum": labels("Beauté & Parfum", "Schoonheid & Parfum", "Beauty & Fragrance"),
  sante: labels("Santé", "Gezondheid", "Health"),
  "sport-plein-air": labels("Sport & Plein air", "Sport & Outdoor", "Sports & Outdoors"),
  "auto-moto": labels("Auto & Moto", "Auto & Motor", "Automotive & Motorcycles"),
  "bebe-puericulture": labels("Bébé & Puériculture", "Baby & Verzorging", "Baby & Nursery"),
  animalerie: labels("Animalerie", "Huisdieren", "Pet Supplies"),
  bagagerie: labels("Bagagerie", "Bagage", "Luggage"),
  "livres-culture": labels("Livres & Culture", "Boeken & Cultuur", "Books & Culture"),
  "alimentation-boissons": labels("Alimentation & Boissons", "Eten & Drinken", "Food & Drinks"),
  "jeux-jouets": labels("Jeux & Jouets", "Spellen & Speelgoed", "Games & Toys"),
  accessoires: labels("Accessoires", "Accessoires", "Accessories"),
  "loisirs-creatifs": labels("Loisirs créatifs", "Creatieve hobby's", "Arts & Crafts"),
  mode: labels("Mode", "Mode", "Fashion"),
  "voyages-sejours": labels("Voyages & Séjours", "Reizen & Verblijven", "Travel & Stays"),
} as const satisfies Record<string, TaxonomyLabels>;

export const FILON_SUBCATEGORY_LABELS = {
  "accessoires-auto": labels("Accessoires auto", "Auto-accessoires", "Car Accessories"),
  "accessoires-gaming": labels("Accessoires gaming", "Gamingaccessoires", "Gaming Accessories"),
  "arrimage-hydraulique": labels("Arrimage & Hydraulique", "Ladingzekering & Hydrauliek", "Load Securing & Hydraulics"),
  aspirateurs: labels("Aspirateurs", "Stofzuigers", "Vacuum Cleaners"),
  "auvents-rampes": labels("Auvents & Rampes", "Luifels & Leuningen", "Awnings & Railings"),
  bagues: labels("Bagues", "Ringen", "Rings"),
  "bain-corps": labels("Bain & Corps", "Bad & Lichaam", "Bath & Body"),
  "barres-de-son": labels("Barres de son", "Soundbars", "Soundbars"),
  "baskets-sneakers": labels("Baskets & Sneakers", "Sneakers", "Trainers & Sneakers"),
  "bottes-bottines": labels("Bottes & Bottines", "Laarzen & Enkellaarzen", "Boots & Ankle Boots"),
  "boucles-d-oreilles": labels("Boucles d'oreilles", "Oorbellen", "Earrings"),
  bracelets: labels("Bracelets", "Armbanden", "Bracelets"),
  "bebe-0-2-ans": labels("Bébé (0-2 ans)", "Baby (0-2 jaar)", "Baby (0-2 Years)"),
  "camping-randonnee": labels("Camping & Randonnée", "Kamperen & Wandelen", "Camping & Hiking"),
  "campings-parcs": labels("Campings & Parcs", "Campings & Parken", "Campsites & Parks"),
  "casques-audio": labels("Casques audio", "Hoofdtelefoons", "Headphones"),
  ceintures: labels("Ceintures", "Riemen", "Belts"),
  "chambre-bebe": labels("Chambre bébé", "Babykamer", "Nursery"),
  "chapeaux-casquettes": labels("Chapeaux & Casquettes", "Hoeden & Petten", "Hats & Caps"),
  "chargeurs-batteries": labels("Chargeurs & Batteries", "Opladers & Batterijen", "Chargers & Batteries"),
  chat: labels("Chat", "Kat", "Cat"),
  "chauffage-vehicule": labels("Chauffage véhicule", "Voertuigverwarming", "Vehicle Heating"),
  chaussettes: labels("Chaussettes", "Sokken", "Socks"),
  chaussons: labels("Chaussons", "Pantoffels", "Slippers"),
  chemises: labels("Chemises", "Overhemden", "Shirts"),
  cheveux: labels("Cheveux", "Haar", "Hair"),
  chien: labels("Chien", "Hond", "Dog"),
  "claviers-souris": labels("Claviers & Souris", "Toetsenborden & Muizen", "Keyboards & Mice"),
  "climatisation-chauffage": labels("Climatisation & Chauffage", "Airconditioning & Verwarming", "Air Conditioning & Heating"),
  "coffrets-calendriers": labels("Coffrets & Calendriers", "Geschenksets & Kalenders", "Gift Sets & Calendars"),
  "colliers-pendentifs": labels("Colliers & Pendentifs", "Kettingen & Hangers", "Necklaces & Pendants"),
  "composants-pc": labels("Composants PC", "Pc-componenten", "PC Components"),
  consoles: labels("Consoles", "Consoles", "Consoles"),
  "coques-protections": labels("Coques & Protections", "Hoesjes & Bescherming", "Cases & Protection"),
  costumes: labels("Costumes", "Pakken", "Suits"),
  "couches-toilette": labels("Couches & Toilette", "Luiers & Verzorging", "Nappies & Changing"),
  cravates: labels("Cravates", "Stropdassen", "Ties"),
  "creation-de-badges": labels("Création de badges", "Buttons Maken", "Badge Making"),
  cyclisme: labels("Cyclisme", "Fietsen", "Cycling"),
  "cables-adaptateurs": labels("Câbles & Adaptateurs", "Kabels & Adapters", "Cables & Adapters"),
  "cables-audio-video": labels("Câbles audio & vidéo", "Audio- & Videokabels", "Audio & Video Cables"),
  "dessin-peinture": labels("Dessin & Peinture", "Tekenen & Schilderen", "Drawing & Painting"),
  decoration: labels("Décoration", "Decoratie", "Decor"),
  "deguisements-costumes": labels("Déguisements & Costumes", "Verkleedkleding & Kostuums", "Fancy Dress & Costumes"),
  enceintes: labels("Enceintes", "Luidsprekers", "Speakers"),
  entretien: labels("Entretien", "Onderhoud", "Care & Maintenance"),
  "escarpins-talons": labels("Escarpins & Talons", "Pumps & Hakken", "Pumps & Heels"),
  fille: labels("Fille", "Meisjes", "Girls"),
  "fitness-musculation": labels("Fitness & Musculation", "Fitness & Krachttraining", "Fitness & Strength Training"),
  gants: labels("Gants", "Handschoenen", "Gloves"),
  garcon: labels("Garçon", "Jongens", "Boys"),
  "gravure-sublimation": labels("Gravure & Sublimation", "Graveren & Sublimatie", "Engraving & Sublimation"),
  "gros-electromenager": labels("Gros électroménager", "Groot Witgoed", "Major Appliances"),
  "hauts-t-shirts": labels("Hauts & T-shirts", "Tops & T-shirts", "Tops & T-Shirts"),
  "hygiene-bucco-dentaire": labels("Hygiène bucco-dentaire", "Mondverzorging", "Oral Care"),
  hotels: labels("Hôtels", "Hotels", "Hotels"),
  "impression-3d-scan": labels("Impression 3D & Scan", "3D-printen & Scannen", "3D Printing & Scanning"),
  "imprimantes-consommables": labels("Imprimantes & Consommables", "Printers & Verbruiksartikelen", "Printers & Supplies"),
  "jantes-roues": labels("Jantes & Roues", "Velgen & Wielen", "Rims & Wheels"),
  "jardinage-apiculture": labels("Jardinage & Apiculture", "Tuinieren & Bijenteelt", "Gardening & Beekeeping"),
  "jeux-de-bain": labels("Jeux de bain", "Badspeelgoed", "Bath Toys"),
  "jeux-video": labels("Jeux vidéo", "Videogames", "Video Games"),
  jupes: labels("Jupes", "Rokken", "Skirts"),
  "lentilles-regard": labels("Lentilles & Regard", "Lenzen & Oogverzorging", "Contact Lenses & Eye Care"),
  "linge-de-maison": labels("Linge de maison", "Huishoudtextiel", "Home Linens"),
  "lingerie-nuit": labels("Lingerie & Nuit", "Lingerie & Nachtkleding", "Lingerie & Nightwear"),
  "locations-de-vacances": labels("Locations de vacances", "Vakantiehuizen", "Holiday Rentals"),
  luminaires: labels("Luminaires", "Verlichting", "Lighting"),
  "lunettes-de-soleil": labels("Lunettes de soleil", "Zonnebrillen", "Sunglasses"),
  "maillots-de-bain": labels("Maillots de bain", "Badmode", "Swimwear"),
  "manteaux-vestes": labels("Manteaux & Vestes", "Jassen & Mantels", "Coats & Jackets"),
  maquillage: labels("Maquillage", "Make-up", "Makeup"),
  "massage-bien-etre": labels("Massage & Bien-être", "Massage & Welzijn", "Massage & Wellness"),
  meubles: labels("Meubles", "Meubels", "Furniture"),
  "mobilier-de-jardin": labels("Mobilier de jardin", "Tuinmeubelen", "Garden Furniture"),
  "mocassins-ville": labels("Mocassins & Ville", "Loafers & Nette Schoenen", "Loafers & Dress Shoes"),
  montres: labels("Montres", "Horloges", "Watches"),
  "montres-connectees": labels("Montres connectées", "Smartwatches", "Smartwatches"),
  ongles: labels("Ongles", "Nagels", "Nails"),
  "ordinateurs-portables": labels("Ordinateurs portables", "Laptops", "Laptops"),
  outillage: labels("Outillage", "Gereedschap", "Tools"),
  "outils-levage": labels("Outils & Levage", "Gereedschap & Hijsmateriaal", "Tools & Lifting"),
  "pantalons-jeans": labels("Pantalons & Jeans", "Broeken & Jeans", "Trousers & Jeans"),
  "papeterie-bureau": labels("Papeterie & Bureau", "Kantoor & Schrijfwaren", "Stationery & Office"),
  parfums: labels("Parfums", "Parfums", "Fragrances"),
  "patrons-kits-de-couture": labels("Patrons & Kits de couture", "Patronen & Naaikits", "Patterns & Sewing Kits"),
  "petit-electromenager": labels("Petit électroménager", "Kleine Huishoudtoestellen", "Small Appliances"),
  "petits-animaux": labels("Petits animaux", "Kleine Huisdieren", "Small Pets"),
  "pieces-detachees": labels("Pièces détachées", "Reserveonderdelen", "Spare Parts"),
  "platines-hi-fi": labels("Platines & Hi-Fi", "Platenspelers & Hi-fi", "Turntables & Hi-Fi"),
  pneus: labels("Pneus", "Banden", "Tyres"),
  "pompes-arrosage": labels("Pompes & Arrosage", "Pompen & Besproeiing", "Pumps & Irrigation"),
  portefeuilles: labels("Portefeuilles", "Portemonnees", "Wallets"),
  "poterie-ceramique": labels("Poterie & Céramique", "Pottenbakken & Keramiek", "Pottery & Ceramics"),
  "poussettes-sieges-auto": labels("Poussettes & Sièges auto", "Kinderwagens & Autostoelen", "Pushchairs & Car Seats"),
  "pulls-sweats": labels("Pulls & Sweats", "Truien & Sweaters", "Jumpers & Sweatshirts"),
  "pyrogravure-travail-du-bois": labels("Pyrogravure & Travail du bois", "Pyrografie & Houtbewerking", "Pyrography & Woodworking"),
  "rangement-boites-aux-lettres": labels("Rangement & Boîtes aux lettres", "Opbergen & Brievenbussen", "Storage & Mailboxes"),
  "rasage-epilation": labels("Rasage & Épilation", "Scheren & Ontharen", "Shaving & Hair Removal"),
  "remorquage-carrosserie": labels("Remorquage & Carrosserie", "Slepen & Carrosserie", "Towing & Bodywork"),
  "repas-biberons": labels("Repas & Biberons", "Voeding & Flessen", "Feeding & Bottles"),
  revetements: labels("Revêtements", "Vloer- & Wandbekleding", "Flooring & Wall Coverings"),
  robes: labels("Robes", "Jurken", "Dresses"),
  running: labels("Running", "Hardlopen", "Running"),
  reseau: labels("Réseau", "Netwerk", "Networking"),
  "sacs-banane-pochettes": labels("Sacs banane & Pochettes", "Heuptassen & Clutches", "Bum Bags & Pouches"),
  "sacs-a-dos": labels("Sacs à dos", "Rugzakken", "Backpacks"),
  "sacs-a-main": labels("Sacs à main", "Handtassen", "Handbags"),
  sandales: labels("Sandales", "Sandalen", "Sandals"),
  "semelles-entretien": labels("Semelles & Entretien", "Inlegzolen & Onderhoud", "Insoles & Shoe Care"),
  smartphones: labels("Smartphones", "Smartphones", "Smartphones"),
  "soins-visage": labels("Soins visage", "Gezichtsverzorging", "Facial Care"),
  "sous-vetements": labels("Sous-vêtements", "Ondergoed", "Underwear"),
  "sports-collectifs": labels("Sports collectifs", "Teamsporten", "Team Sports"),
  "sports-d-hiver": labels("Sports d'hiver", "Wintersport", "Winter Sports"),
  stockage: labels("Stockage", "Opslag", "Storage"),
  "securite-quincaillerie": labels("Sécurité & Quincaillerie", "Beveiliging & IJzerwaren", "Security & Hardware"),
  "t-shirts-polos": labels("T-shirts & Polos", "T-shirts & Polo's", "T-Shirts & Polos"),
  tablettes: labels("Tablettes", "Tablets", "Tablets"),
  "tissus-mercerie": labels("Tissus & Mercerie", "Stoffen & Fournituren", "Fabrics & Haberdashery"),
  telecommandes: labels("Télécommandes", "Afstandsbedieningen", "Remote Controls"),
  televiseurs: labels("Téléviseurs", "Televisies", "Televisions"),
  "vaisselle-cuisine": labels("Vaisselle & Cuisine", "Servies & Keuken", "Tableware & Kitchen"),
  "valises-bagages": labels("Valises & Bagages", "Koffers & Bagage", "Suitcases & Luggage"),
  videoprojecteurs: labels("Vidéoprojecteurs", "Projectoren", "Projectors"),
  "villas-appartements": labels("Villas & Appartements", "Villa's & Appartementen", "Villas & Apartments"),
  "echarpes-foulards": labels("Écharpes & Foulards", "Sjaals & Omslagdoeken", "Scarves & Shawls"),
  eclairage: labels("Éclairage", "Voertuigverlichting", "Vehicle Lighting"),
  ecouteurs: labels("Écouteurs", "Oordopjes", "Earbuds"),
  ecrans: labels("Écrans", "Beeldschermen", "Monitors"),
} as const satisfies Record<string, TaxonomyLabels>;

export const FILON_TAXONOMY_LABELS: Readonly<Record<string, TaxonomyLabels>> = {
  ...FILON_DEPARTMENT_LABELS,
  ...FILON_CATEGORY_LABELS,
  ...FILON_SUBCATEGORY_LABELS,
};

/** Produces the same stable URL key as the backend for canonical French labels. */
export function taxonomySlug(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/&/g, " ")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

export function localizedTaxonomyLabel(
  item: { name: string; slug?: string | null },
  locale: TaxonomyLocale,
) {
  const providedSlug = item.slug?.trim().toLowerCase();
  const canonicalSlug = taxonomySlug(item.name);
  return (providedSlug ? FILON_TAXONOMY_LABELS[providedSlug]?.[locale] : undefined)
    ?? FILON_TAXONOMY_LABELS[canonicalSlug]?.[locale]
    ?? item.name;
}

export function localizedTaxonomyOption(
  item: { name: string; slug?: string | null },
  locale: TaxonomyLocale,
) {
  return { label: localizedTaxonomyLabel(item, locale), canonicalName: item.name } as const;
}

const RULES: { terms: string[]; icon: IconName }[] = [
  { terms: ["tech", "informat", "telephon", "gaming"], icon: "memory" },
  { terms: ["maison", "deco", "jardin", "bricol"], icon: "home" },
  { terms: ["mode", "chauss", "bijoux"], icon: "checkroom" },
  { terms: ["beaute", "parfum", "sante"], icon: "spa" },
  { terms: ["sport", "plein air"], icon: "directions-run" },
  { terms: ["auto", "moto"], icon: "directions-car" },
  { terms: ["bebe", "puericulture"], icon: "child-care" },
  { terms: ["animal"], icon: "pets" },
  { terms: ["voyage", "sejour"], icon: "flight" },
];

const FALLBACKS: IconName[] = ["category", "explore", "auto-awesome", "widgets", "hub"];

function normalized(value: string) {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}

function stableIndex(value: string) {
  return Array.from(value).reduce((hash, char) => ((hash * 31) + char.charCodeAt(0)) >>> 0, 17) % FALLBACKS.length;
}

export function taxonomyPresentation(name: string) {
  const key = normalized(name);
  const rule = RULES.find(({ terms }) => terms.some((term) => key.includes(term)));
  return { icon: rule?.icon ?? FALLBACKS[stableIndex(key)], variation: stableIndex(key) };
}
