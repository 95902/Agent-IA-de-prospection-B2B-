/** Normalise pour comparer sans casse ni accents : « Hôtel Élysée » → « hotel elysee ». */
export function normalizeText(value: string): string {
  return value
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase()
    .replace(/\s+/g, " ")
    .trim();
}

/** Vrai si chaque mot de `query` apparaît dans au moins un des champs. */
export function matchesQuery(
  query: string,
  fields: ReadonlyArray<string | null | undefined>,
): boolean {
  const words = normalizeText(query).split(" ").filter(Boolean);
  if (words.length === 0) return true;
  const haystack = normalizeText(fields.filter(Boolean).join(" "));
  return words.every((w) => haystack.includes(w));
}
