"""Fournisseur LLM factice, déterministe, sans réseau ni clé.

Il permet de faire tourner tout le pipeline d'agents de bout en bout en
local et dans les tests. Il reconnaît quelques intentions clés (ex. une
demande d'ordinateur portable) pour renvoyer des critères crédibles.
"""

from __future__ import annotations

import json

from app.llm.base import LLMProvider, Message


class MockProvider(LLMProvider):
    name = "mock"

    async def complete(
        self, messages: list[Message], *, temperature: float = 0.2
    ) -> str:
        user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        return f"[mock] {user[:180]}"

    async def complete_json(
        self, messages: list[Message], *, temperature: float = 0.0
    ) -> str:
        # L'intention se lit sur tout le contexte, mais les mots-clés ne
        # doivent venir que du besoin exprimé par l'utilisateur.
        text = " ".join(m.content for m in messages).lower()
        user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        return json.dumps(self._infer_criteria(text, user.lower()), ensure_ascii=False)

    @staticmethod
    def _infer_criteria(text: str, user_text: str | None = None) -> dict:
        user_text = user_text if user_text is not None else text
        category = None
        usage: list[str] = []
        must_have: list[str] = []
        priorities: list[str] = []

        if any(w in text for w in ("portable", "laptop", "ordinateur")):
            category = "ordinateur_portable"
        elif any(w in text for w in ("téléphone", "smartphone", "iphone")):
            category = "smartphone"

        if "étudiant" in text or "etudiant" in text or "fac" in text:
            usage += ["bureautique", "cours", "web"]
            priorities += ["autonomie", "portabilité", "prix"]
            must_have += ["ssd", "léger"]
        if "gaming" in text or "jeu" in text:
            usage += ["jeux"]
            priorities += ["gpu", "performance"]

        budget_max = None
        import re

        m = re.search(r"(\d[\d\s.]{1,6})\s*(?:€|eur|euros)", text)
        if m:
            budget_max = float(m.group(1).replace(" ", "").replace(".", ""))
        else:
            m2 = re.search(r"moins de\s*(\d[\d\s]{1,6})", text)
            if m2:
                budget_max = float(m2.group(1).replace(" ", ""))

        return {
            "category": category,
            "budget_max": budget_max,
            "usage": usage or ["polyvalent"],
            "must_have": must_have,
            "priorities": priorities or ["prix"],
            "keywords": [w.strip(".,;:!?") for w in user_text.split() if len(w) > 3][:8],
        }
