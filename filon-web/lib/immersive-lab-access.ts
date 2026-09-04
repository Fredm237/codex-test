type RuntimeEnvironment = Record<string, string | undefined>;

const ENABLED = new Set(["1", "true", "yes", "on"]);

/**
 * Le laboratoire est une surface de construction, jamais une route publique de
 * production. Un override explicite peut l'ouvrir pour une qualification
 * interne ; les Preview Vercel et le serveur de développement restent ouverts.
 */
export function isImmersiveLabEnabled(environment: RuntimeEnvironment = process.env) {
  const explicit = environment.FILON_IMMERSIVE_LAB_ENABLED?.trim().toLowerCase();
  if (explicit !== undefined) return ENABLED.has(explicit);

  return environment.VERCEL_ENV === "preview"
    || environment.VERCEL_ENV === "development"
    || environment.NODE_ENV === "development"
    || environment.NODE_ENV === "test";
}
