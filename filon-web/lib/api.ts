// Base URL du backend FILON (Railway). Surchargeable au build via
// NEXT_PUBLIC_FILON_API. Sert aux surfaces qui lisent des données en direct
// (assistant, catalogue) sans quitter l'export statique.
export const API = (
  process.env.NEXT_PUBLIC_FILON_API || "https://web-production-c6842.up.railway.app"
).replace(/\/$/, "");
