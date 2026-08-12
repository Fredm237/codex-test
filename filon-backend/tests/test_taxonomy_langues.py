"""Collisions lexicales entre langues, relevées en production.

Le catalogue mélange français, anglais et néerlandais. Un même mot y désigne
souvent deux choses selon la langue, et un motif écrit pour l'une capte les
produits de l'autre. Tous les libellés ci-dessous sont réels, et tous étaient
mal rangés.

Le principe appliqué est celui déjà retenu pour « souris » : un mot ambigu ne
classe pas seul, il exige un contexte.
"""

from __future__ import annotations

import pytest

from app.services import taxonomy as t


def _rayon(nom: str, cat: str = "") -> str | None:
    return t.classify(cat, nom)


class TestCremeEstUneCouleurEnNeerlandais:
    """« crème » range en Beauté ; en néerlandais c'est une teinte.

    Le rayon Beauté & Parfum affichait un salon de jardin, un paravent et une
    applique murale, tous déclinés « Crème ».
    """

    @pytest.mark.parametrize(
        "nom,attendu",
        [
            ("Casaria Polyrattan Loungeset -Incl. Kussens Tafel - Bruin Crème", t.JARDIN),
            ("Casaria Wind Tuinscherm Nosara - 160x300cm Uitschuifbaar – Crème", t.JARDIN),
            ("Muro 3365CR wandlamp – crème, modern ontwerp, 13x7,5x9 cm", t.MAISON),
        ],
    )
    def test_la_teinte_creme_ne_range_plus_en_beaute(self, nom, attendu):
        assert _rayon(nom) == attendu, nom

    @pytest.mark.parametrize(
        "nom",
        [
            "Nivea Crème Soft Bad - 750 ML",
            "Crème hydratante visage 50ml",
            "Crème de jour anti-âge",
            "Handcrème amandel 75ml",
            "Zonnecrème SPF 50 kinderen",
        ],
    )
    def test_les_vraies_cremes_restent_en_beaute(self, nom):
        assert _rayon(nom) == t.BEAUTE, nom


class TestKettingEstUneChaineEnNeerlandais:
    """« ketting » range en Bijoux ; « kettingzaag » est une tronçonneuse."""

    def test_une_chaine_de_tronconneuse_nest_pas_un_collier(self):
        nom = 'yaoqijie Hoge kwaliteit 16-inch bladgrootte .325"-1.3mm-67DL kettingzaag ketting'
        assert _rayon(nom) == t.JARDIN

    def test_une_chaine_de_velo_non_plus(self):
        assert _rayon("Shimano fietsketting 11-speed") != t.BIJOUX

    def test_un_vrai_collier_reste_en_bijoux(self):
        assert _rayon("Zilveren halsketting met hanger 45cm") == t.BIJOUX
        assert _rayon("Collier argent massif chaîne maille") == t.BIJOUX


class TestPendantEstAmbigu:
    """« pendant lamp » est une suspension, pas un pendentif."""

    def test_une_lampe_suspendue_est_un_luminaire(self):
        assert _rayon("Tube pendant lamp iron 60x6x120 gold") == t.MAISON

    def test_une_pendule_murale_est_de_la_decoration(self):
        assert _rayon("Horloge murale silencieuse 30cm blanche") == t.MAISON
        assert _rayon("Wandklok zwart metaal 40cm") == t.MAISON

    def test_une_montre_reste_en_bijoux(self):
        assert _rayon("Montre automatique acier bracelet cuir") == t.BIJOUX
        assert _rayon("Casio G-Shock watch resin strap") == t.BIJOUX

    def test_un_pendentif_reste_en_bijoux(self):
        assert _rayon("Pendentif or blanc 18 carats") == t.BIJOUX
        assert _rayon("Hip Hop Diamond Necklace Pendant") == t.BIJOUX


class TestSportSeulNeRangePlus:
    """« Potenza Sport » est un pneu Bridgestone, pas un article de sport."""

    @pytest.mark.parametrize(
        "nom,cat",
        [
            ("Potenza Sport", "tyres"),
            ("Cross Sport SP-9", "tyres"),
            ("Road Venture MT KL71", "tyres"),
        ],
    )
    def test_les_pneus_vont_en_auto(self, nom, cat):
        assert t.classify(cat, nom) == t.AUTO, nom

    def test_le_mot_sport_dans_un_nom_commercial_ne_suffit_pas(self):
        """Sans contexte sportif, mieux vaut ne rien conclure qu'aller en Sport."""
        assert _rayon("Selle femme SMC Sport Gel") != t.BEAUTE

    def test_les_vrais_articles_de_sport_restent_classes(self):
        for nom in (
            "Sac de sport 40L noir",
            "Vêtements de sport homme respirants",
            "Equipamiento deportivo profesional",
            "Sportartikelen fitness set",
        ):
            assert _rayon(nom) == t.SPORT, nom


class TestObjetsFinisEnNeerlandais:
    """« Zomerslaapzak Jersey » est une gigoteuse, pas du tissu jersey."""

    def test_une_gigoteuse_neerlandaise_va_en_bebe(self):
        assert _rayon("Jollein Zomerslaapzak Jersey - Lovely Birds - TOG 0.5") == t.BEBE

    def test_une_housse_de_couette_neerlandaise_va_en_maison(self):
        assert _rayon("Dekbedovertrek katoen 240x220 grijs") == t.MAISON


class TestLeSportPrimeSurLeGenreQuandIlEstExplicite:
    """« Maillot arbitre Macron », catégorisé « Football > Maillot > Homme ».

    Le public était tranché avant de regarder si l'article relève d'un rayon
    plus spécifique. Un maillot de football est un article de sport.
    """

    def test_un_maillot_de_football_va_en_sport(self):
        assert t.classify("Football > Maillot > Adulte > Homme", "Maillot arbitre Macron") == t.SPORT

    def test_un_maillot_de_bain_de_natation_aussi(self):
        assert _rayon("Maillot de bain Natation Arena Dynamo One Piece Femme") == t.SPORT

    def test_mais_une_chemise_dhomme_reste_en_mode_homme(self):
        assert t.classify("Men's Clothing", "OLYMP Luxor Modern Fit Overhemd") == t.MODE_HOMME

    def test_et_des_baskets_restent_en_chaussures(self):
        """Le rayon Chaussures est plus précis que Sport pour une paire."""
        assert _rayon("Baskets running homme taille 43") == t.CHAUSSURES
        assert _rayon("Chaussures Running adidas Homme Réponse Super White") == t.CHAUSSURES


class TestAnglesMorts:
    """Aucune règle ne les reconnaissait : 216 466 offres non rangées."""

    @pytest.mark.parametrize(
        "nom,attendu",
        [
            ("iScooter iK3Max Trottinette électrique pour enfants moteur 200W", t.SPORT),
            ("Segway Ninebot step elektrisch", t.SPORT),
            ("NEWSMY 100W Panneau solaire portable cellules BC", t.JARDIN),
            ("Zonnepaneel 400W monokristallijn", t.JARDIN),
            ("Flashfish A101 120W 98Wh Station d'alimentation portable", t.INFORMATIQUE),
            ("EcoFlow Powerstation 1000W", t.INFORMATIQUE),
            ("Coast 2-in-1 kinderstoel - hoge kinderstoel - hout", t.BEBE),
            ("Kinderwagen 3-in-1 grijs", t.BEBE),
            ("Parc à chiots pliable 129 x 65 x 81 cm - blanc", t.ANIMALERIE),
            ("Puppy training pads 60x60cm", t.ANIMALERIE),
        ],
    )
    def test_les_libelles_orphelins_sont_desormais_ranges(self, nom, attendu):
        assert _rayon(nom) == attendu, nom


class TestAucuneRegressionSurLesRayonsEtablis:
    """Filet de sécurité : les cas déjà corrects doivent le rester."""

    @pytest.mark.parametrize(
        "nom,attendu",
        [
            ("Souris sans fil Logitech MX Master 3S", t.INFORMATIQUE),
            ("Coque téléphone iPhone 15 motif chat", t.TELEPHONIE),
            ("Croquettes pour chien 12 kg", t.ANIMALERIE),
            ("Pneu hiver Michelin 205/55 R16", t.AUTO),
            ("Casque audio Bluetooth réduction de bruit", t.TV_SON),
            ("Parfum femme eau de toilette 50ml", t.BEAUTE),
            ("Housse de couette percale de coton 240x220", t.MAISON),
            ("Tissu chemise 100% coton - Carreaux bleu & vert", t.LOISIRS),
            ("Piqué 100% coton milleraies - Souris écolière", t.LOISIRS),
            ("Robe de soirée longue", t.MODE_FEMME),
            ("FastGo Running Steam CD Key", t.GAMING),
        ],
    )
    def test_les_rayons_deja_justes_ne_bougent_pas(self, nom, attendu):
        assert _rayon(nom) == attendu, nom


class TestHorlogeDesigneUneMontreEnBelgique:
    """« Horloge » est le mot des flux marchands belges pour une montre-bracelet.

    Ces cas viennent d'une mesure sur 1560 offres réelles de production :
    retirer « horloge » du rayon Bijoux déplaçait 57 vraies montres vers
    Maison & Déco. Le mot est donc conservé en Bijoux, et seules les pendules
    explicitement murales ou d'intérieur vont en Maison.
    """

    @pytest.mark.parametrize(
        "cat,nom",
        [
            ("Watch", "MIDO Ocean Star M0266293729100 Ocean Star GMT Horloge"),
            ("Watch", "Certina DS-2 C0492101112601 Horloge"),
            ("Watch", "Daniel Wellington Classic DW00100882 Juliette Evergold Horloge"),
            ("Watch", "Tissot T-Classic T1518221103100 PRC 100 Solar Horloge"),
            ("Watch", "Citizen Sky AT8304-57W Promaster Sky Horloge"),
            ("Watch", "Hamilton Navy H77855330 Khaki Navy Frogman Horloge"),
        ],
    )
    def test_les_montres_bracelets_restent_en_bijoux(self, cat, nom):
        assert t.classify(cat, nom) == t.BIJOUX, nom

    @pytest.mark.parametrize(
        "nom",
        [
            "Horloge murale silencieuse 30cm blanche",
            "Horloge de cuisine rétro",
            "Wandklok modern zwart 40 cm",
            "Koekoeksklok hout traditioneel",
        ],
    )
    def test_mais_les_pendules_dinterieur_vont_en_maison(self, nom):
        assert _rayon(nom) == t.MAISON, nom


class TestRegressionsMesureesSurDonneesReelles:
    """Cas où un premier correctif s'est révélé trop large, une fois mesuré."""

    def test_une_station_pour_oiseaux_nest_pas_de_linformatique(self):
        """« Station d'alimentation pour oiseaux » est un distributeur de graines."""
        assert _rayon("Station d'alimentation pour oiseaux en bois") != t.INFORMATIQUE

    def test_mais_une_station_electrique_en_est(self):
        assert _rayon("Station d'alimentation portable 1000Wh solaire") == t.INFORMATIQUE

    def test_un_piege_photo_avec_kit_solaire_reste_en_photo(self):
        """La caméra est le produit, le panneau solaire n'est qu'un accessoire."""
        nom = "Piège Photographique Wifi Photo 64MP Video 1296P W600 + kit panneaux solaires"
        assert _rayon(nom) == t.PHOTO

    def test_mais_un_vrai_kit_solaire_va_en_jardin(self):
        assert _rayon("Kit de panneaux solaires 300W pour toiture") == t.JARDIN

    def test_la_piscine_et_le_spa_relevent_du_plein_air(self):
        assert _rayon("Brosse pour piscine 46cm avec tête de raccordement en alu") == t.SPORT
        assert _rayon("Spa gonflable noir rond pour 4 personnes 20-42°C") == t.SPORT


class TestSurfEstAussiUneMarqueDeLessive:
    """« Surf Wasmiddel Berry Bliss » est une lessive Unilever, pas du surf.

    Relevé sur la seconde mesure : trois références de lessive Surf passaient
    d'Électroménager à Sport & Plein air.
    """

    @pytest.mark.parametrize(
        "nom",
        [
            "Surf Wasmiddel Berry Bliss - 500 ml",
            "Surf Tropical Lelie Wasmiddel - 648 ml",
            "Surf Watermeloen Breeze Wasmiddel - 648 ml",
        ],
    )
    def test_la_lessive_surf_ne_va_pas_en_sport(self, nom):
        assert t.classify("Wassen, strijken & drogen", nom) != t.SPORT, nom

    def test_mais_le_vrai_surf_reste_en_sport(self):
        assert _rayon("Planche de surf 6'2 epoxy shortboard") == t.SPORT
        assert _rayon("Kitesurf harnais taille M") == t.SPORT
        assert _rayon("Surfboard leash 8ft") == t.SPORT


class TestSoutienGorgeDeSport:
    """« Soutien-gorge sport Training Bra Classic » devenait non rangé."""

    def test_un_soutien_gorge_de_sport_va_en_sport(self):
        assert _rayon("Soutien-gorge sport Training Bra Classic") == t.SPORT
        assert _rayon("Soutien gorge de sport maintien fort") == t.SPORT


class TestDerniersSignauxManquants:
    """Libellés réels qui n'étaient rangés dans aucun rayon."""

    def test_une_huile_de_massage_va_en_beaute(self):
        assert t.classify("Creme, gel & olie", "Shiatsu Ylang Ylang Massageolie - 100ml") == t.BEAUTE

    def test_la_parapharmacie_va_en_beaute(self):
        assert t.classify("Parapharmacie > Corporel > Hydratation", "Crème propre") == t.BEAUTE

    def test_un_service_de_table_va_en_maison(self):
        nom = "Liewood Eetset - Vivi Printed Tableware Set - Elephant / Creme"
        assert _rayon(nom) == t.MAISON

    @pytest.mark.parametrize(
        "nom",
        [
            "Fossil Straps ABQ2341 BQ2341 Flynn Sport Horlogeband",
            "Fossil Straps AFTW6026 FTW6026 Sport Horlogeband",
            "Bracelet de montre cuir 20mm brun",
        ],
    )
    def test_un_bracelet_de_montre_va_en_bijoux(self, nom):
        assert t.classify("Strap", nom) == t.BIJOUX, nom


class TestBraceletsSousLibelleBand:
    """Sous la catégorie « Strap », « band » et « bandje » désignent un bracelet."""

    @pytest.mark.parametrize(
        "nom",
        [
            "Rado straps 07.02976.10 The Original band",
            "Calvin Klein 459300030 Gauge Sport band",
            "Luminox Straps FMX.2405.ST 0900 Sport Timer band",
            "Danish Design Straps DD-BA-1274-02 On The Dot band",
        ],
    )
    def test_un_band_de_categorie_strap_va_en_bijoux(self, nom):
        assert t.classify("Strap", nom) == t.BIJOUX, nom

    def test_un_bandje_de_smartwatch_va_en_bijoux(self):
        nom = "imoshion Siliconen sport bandje met gesp voor de Fitbit Charge"
        assert t.classify("Smartwatch Strap", nom) == t.BIJOUX

    def test_une_bande_de_resistance_reste_en_sport(self):
        assert t.classify("Fitness", "Bande de résistance élastique musculation") == t.SPORT


class TestBaignadeGonflable:
    """Les fauteuils flottants de piscine n'étaient rangés dans aucun rayon."""

    @pytest.mark.parametrize(
        "nom",
        [
            "Pvc Inflatable Lounge Chair Water Floating Chair Adult Floating",
            "Inflatable Floating Chair Upright Lounge Swimming Pool Lounge",
            "Bouée gonflable licorne 90 cm",
        ],
    )
    def test_un_flotteur_va_en_sport(self, nom):
        assert t.classify("Sports & Outdoor", nom) == t.SPORT, nom


class TestPneusSousLibelleNeerlandais:
    """Les pneus arrivent sous « Zomerbanden » ou sans autre indice que leur
    dimension. « Sport » dans le nom les envoyait en Sport & Plein air, et
    « Debica Frigo » en Électroménager.
    """

    @pytest.mark.parametrize(
        "cat,nom",
        [
            ("Zomerbanden", "Continental CrossContact LX Sport ( 225/60 R17 99H )"),
            ("Zomerbanden", "Michelin Pilot Sport 4S ( 285/40 ZR18 (105Y) XL )"),
            ("Winterbanden", "Dunlop Winter Sport 5 ( 205/55 R16 91H )"),
            ("All-season banden", "Dunlop Sport All Season ( 195/55 R16 91V XL BLK )"),
            ("Pneus d'hiver", "Debica Frigo 2 ( 155/70 R13 75T )"),
        ],
    )
    def test_un_pneu_va_en_auto(self, cat, nom):
        assert t.classify(cat, nom) == t.AUTO, nom


class TestPlongeeEtSnorkeling:
    """Masques de plongée et tubas : familles absentes de toute règle."""

    @pytest.mark.parametrize(
        "nom",
        [
            "Large Field Of View Foldable Full Face Anti-fog Snorkeling Mask",
            "New diving mask Full dry breathing tube anti-fog snorkel",
            "Masque de plongée en silicone avec tuba",
            "Palmes de natation réglables adulte",
        ],
    )
    def test_un_masque_de_plongee_va_en_sport(self, nom):
        assert t.classify("Sports & Outdoor", nom) == t.SPORT, nom


class TestVetementsMultisports:
    """Le vêtement doit d'abord être reconnu comme tel pour que l'usage sportif
    puisse s'exprimer : « Débardeur » et « Sweatshirt » manquaient à la liste,
    si bien que ces articles n'étaient rangés nulle part.
    """

    @pytest.mark.parametrize(
        "cat,nom",
        [
            ("Multisports > Débardeur > Adulte > Homme", "Débardeur Proact Sport"),
            ("Multisports > Sweatshirt > Adulte", "Sweatshirt à capuche Proact 1/4 Zip Sport"),
            ("Multisports > Chaussettes > Adulte", "Chaussettes de sport rayés Proact"),
        ],
    )
    def test_un_vetement_multisports_va_en_sport(self, cat, nom):
        assert t.classify(cat, nom) == t.SPORT, nom


class TestLuminaireAMotifSportif:
    """Le support l'emporte sur le motif : une lampe décorée d'un ballon reste
    un luminaire, pas un article de sport.
    """

    def test_une_lampe_a_motif_football_reste_en_maison(self):
        assert _rayon("Lampe LED 3D avec impression ballon de football") == t.MAISON


class TestAnglesMortsMesuresEnBase:
    """Angles morts relevés sur les offres réellement sans rayon en base.

    Les cas précédents venaient d'échantillons de l'API filtrés PAR rayon, donc
    ne contenaient par construction que des offres déjà classées. Ceux-ci
    proviennent de `GET /api/catalog/admin/unclassified`, qui interroge
    directement `filon_category IS NULL`. Les volumes cités sont les comptes
    réels observés sur les 245 293 offres sans rayon.
    """

    @pytest.mark.parametrize(
        "cat,nom",
        [
            # 13 640 offres. « Lamper » est du danois : le catalogue contient une
            # quatrième langue, non anticipée au diagnostic initial.
            ("Lamper", "Fritz Hansen Orient P2 Hanglamp Koper"),
            ("Lamper", "Lampe Gras N317 Tafellamp Mat Zwart & Mat Rood"),
            ("Wonen & Koken > Wonen > Binnenverlichting", "Hanglamp zwart metaal"),
            ("Wonen & Koken > Wonen > Woondecoratie", "Vaas keramiek beige"),
            ("Wonen & Koken > Wonen > Tafels & stoelen", "Eettafel eiken 180cm"),
        ],
    )
    def test_les_luminaires_scandinaves_et_neerlandais_vont_en_maison(self, cat, nom):
        assert t.classify(cat, nom) == t.MAISON, nom

    @pytest.mark.parametrize(
        "cat,nom",
        [
            # ~12 000 offres cumulées sur Phone/Tablet/Ereader Cover.
            ("Phone Cover", "imoshion Color Backcover voor de Samsung Galaxy S21"),
            ("Tablet Cover", "Selencia Echt Leren Bookcase voor de iPad"),
            ("Phone Screenprotector", "Screenprotector Galaxy A51"),
            ("Ereader Cover", "Kobo Clara hoes zwart"),
        ],
    )
    def test_les_accessoires_de_protection_vont_en_telephonie(self, cat, nom):
        assert t.classify(cat, nom) == t.TELEPHONIE, nom

    @pytest.mark.parametrize(
        "cat,nom",
        [
            # ~10 000 offres cumulées sur les familles de maquillage et de soins,
            # en français, néerlandais et anglais.
            ("Foundation", "MAC Studio Fix Fluid SPF15"),
            ("Fond de teint", "Bourjois Healthy Mix"),
            ("Concealer", "MAC Waterweight Concealer - NW50"),
            ("Anti-cerne", "Correcteur teint clair"),
            ("Mascara", "Bourjois Volume Glamour"),
            ("Lipgloss", "L'Oréal Infallible Matte Lipgloss - 207"),
            ("Lippenstift", "Rimmel Lasting Finish"),
            ("Rouge à lèvres", "Rouge Dior 999"),
            ("Oogschaduw", "Palette 12 kleuren"),
            ("Fard à paupières", "Palette nude essentielle"),
            ("Nagels", "Royal Kunstnagels Midnight Minx Stiletto"),
            ("Wimpers & wenkbrauwen", "Wenkbrauwpotlood bruin"),
            ("Gezichtsverzorging", "Nivea gezichtscrème"),
            ("Lichaamsverzorging", "Bodylotion amandel 400ml"),
            ("Bodywash & douchegel", "Dove douchegel"),
        ],
    )
    def test_les_familles_de_maquillage_vont_en_beaute(self, cat, nom):
        assert t.classify(cat, nom) == t.BEAUTE, nom


class TestBlushNestPasQuUnFard:
    """« blush » désigne autant un fard qu'une teinte rosée.

    Ajouté comme mot nu, il faisait basculer en Beauté une robe, des sneakers et
    une bague. Il n'est donc retenu que qualifié, ou seul comme libellé marchand.
    Même principe que « crème » et « souris ».
    """

    @pytest.mark.parametrize(
        "cat,nom,attendu",
        [
            ("Mode femme", "Robe blush rose", t.MODE_FEMME),
            ("Chaussures", "Sneakers blush", t.CHAUSSURES),
            ("Bijoux & Montres", "Bague blush gold", t.BIJOUX),
        ],
    )
    def test_la_teinte_blush_ne_bascule_pas_en_beaute(self, cat, nom, attendu):
        assert t.classify(cat, nom) == attendu, nom

    @pytest.mark.parametrize(
        "cat,nom",
        [
            ("Blush", "Benefit Dandelion"),
            ("Blush", "Blush poudre Chanel"),
            ("Makeup", "Blush palette nude"),
        ],
    )
    def test_le_fard_blush_va_bien_en_beaute(self, cat, nom):
        assert t.classify(cat, nom) == t.BEAUTE, nom
