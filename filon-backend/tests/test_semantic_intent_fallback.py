import pytest

from app.intelligence import intent_resolution
from app.services import taxonomy


class FakeProvider:
    name = "semantic-test"

    def __init__(self, content: str):
        self.content = content

    async def complete_json(self, _messages, *, temperature: float = 0.0):
        assert temperature == 0.0
        return self.content


class FakeRouter:
    def __init__(self, content: str):
        self.provider = FakeProvider(content)

    def for_task(self, _task: str):
        return self.provider


@pytest.mark.asyncio
async def test_fallback_semantique_accepte_un_scope_taxonomique_valide(monkeypatch):
    monkeypatch.setattr(
        intent_resolution,
        "get_router",
        lambda: FakeRouter('{"scopes":[{"category":"Sport & Plein air","subcategory":"Camping & Randonnée"}]}'),
    )

    intent = await intent_resolution.resolve_intent_with_fallback("kampeeruitrusting onder 300 €", "nl")

    assert [(scope.category, scope.subcategory) for scope in intent.scopes] == [
        (taxonomy.SPORT, "Camping & Randonnée")
    ]
    assert intent.budget_eur == 300.0


@pytest.mark.asyncio
async def test_fallback_semantique_utilise_des_termes_de_besoin_concrets(monkeypatch):
    monkeypatch.setattr(
        intent_resolution,
        "get_router",
        lambda: FakeRouter('{"scopes":[{"category":"Sport & Plein air","subcategory":"Camping & Randonnée","keywords":["tente","sac de couchage","rechaud"]}]}'),
    )

    intent = await intent_resolution.resolve_intent_with_fallback("kampeeruitrusting onder 300 €", "nl")

    assert intent.scopes[0].query_terms == ("tente", "sac de couchage", "rechaud")


@pytest.mark.asyncio
async def test_fallback_semantique_peut_preciser_un_scope_lexical_large(monkeypatch):
    monkeypatch.setattr(
        intent_resolution,
        "get_router",
        lambda: FakeRouter('{"scopes":[{"category":"Électroménager","subcategory":"Petit électroménager"}]}'),
    )

    intent = await intent_resolution.resolve_intent_with_fallback("machine à café automatique sous 500 €", "fr")

    assert [(scope.category, scope.subcategory) for scope in intent.scopes] == [
        (taxonomy.ELECTROMENAGER, "Petit électroménager")
    ]


@pytest.mark.asyncio
async def test_fallback_semantique_accepte_un_json_encadre(monkeypatch):
    monkeypatch.setattr(
        intent_resolution,
        "get_router",
        lambda: FakeRouter('```json\n{"scopes":[{"category":"Électroménager","subcategory":"Aspirateurs"}]}\n```'),
    )

    intent = await intent_resolution.resolve_intent_with_fallback("robot vacuum under €300", "en")

    assert [(scope.category, scope.subcategory) for scope in intent.scopes] == [(taxonomy.ELECTROMENAGER, "Aspirateurs")]


@pytest.mark.asyncio
async def test_fallback_semantique_refuse_un_scope_invente(monkeypatch):
    monkeypatch.setattr(
        intent_resolution,
        "get_router",
        lambda: FakeRouter('{"scopes":[{"category":"Univers imaginaire","subcategory":"Inconnue"}]}'),
    )

    intent = await intent_resolution.resolve_intent_with_fallback("objet imaginaire inexistant", "fr")

    assert intent.resolved is False


@pytest.mark.asyncio
async def test_fallback_semantique_ne_remplace_pas_un_scope_prouve_par_des_scopes_divergents(monkeypatch):
    monkeypatch.setattr(
        intent_resolution,
        "get_router",
        lambda: FakeRouter(
            '{"scopes":[{'
            '"category":"Mode homme","subcategory":"T-shirts & Polos",'
            '"keywords":["tennis shirt","polo"]},{'
            '"category":"Mode femme","subcategory":"Hauts & T-shirts",'
            '"keywords":["tennis top","skort"]},{'
            '"category":"Chaussures","subcategory":"Baskets & Sneakers",'
            '"keywords":["tennis shoes"]}]}'
        ),
    )

    intent = await intent_resolution.resolve_intent_with_fallback("tennis clothing under €200", "en")

    assert [(scope.category, scope.subcategory) for scope in intent.scopes] == [(taxonomy.SPORT, None)]
    assert intent.scopes[0].query_terms == ("tennis",)


@pytest.mark.asyncio
async def test_fallback_semantique_ne_specialise_pas_un_sous_rayon_sans_preuve_dans_la_demande(monkeypatch):
    monkeypatch.setattr(
        intent_resolution,
        "get_router",
        lambda: FakeRouter(
            '{"scopes":[{"category":"Sport & Plein air","subcategory":"Running",'
            '"keywords":["tennis apparel","sportswear","breathable"]}]}'
        ),
    )

    intent = await intent_resolution.resolve_intent_with_fallback("tennis clothing under €200", "en")

    assert [(scope.category, scope.subcategory) for scope in intent.scopes] == [(taxonomy.SPORT, None)]
    assert intent.scopes[0].query_terms == ("tennis",)
