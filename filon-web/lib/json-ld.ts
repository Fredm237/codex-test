/** Sérialise une valeur JSON-LD sans permettre à un champ issu d'un flux de
 * fermer la balise `<script>`. */
export function serializeJsonLd(data: unknown): string {
  return (JSON.stringify(data) ?? "null")
    .replace(/</g, "\\u003c")
    .replace(/\u2028/g, "\\u2028")
    .replace(/\u2029/g, "\\u2029");
}
