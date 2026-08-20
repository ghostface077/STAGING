"use client";

import { useEffect, useState } from "react";

/**
 * Renvoie `value` avec un délai : l'utilisateur voit sa saisie s'afficher
 * instantanément (le champ contrôlé reste, lui, à jour immédiatement),
 * pendant que la valeur qui déclenche la requête réseau attend une courte
 * pause dans la frappe — pour ne pas partir en requête à chaque caractère.
 */
export function useDebouncedValue<T>(value: T, delayMs = 250): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(timer);
  }, [value, delayMs]);

  return debounced;
}
