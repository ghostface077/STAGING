/**
 * Politique de mot de passe (correctif #14) — miroir de app/schemas/password.py.
 * Le contrôle réel reste côté serveur (celui-ci n'améliore que le message
 * d'erreur affiché avant même l'envoi du formulaire).
 */
import { z } from "zod";

export const PASSWORD_MIN_LENGTH = 8;
export const PASSWORD_MAX_LENGTH = 72;

export const strongPasswordSchema = z
  .string()
  .min(PASSWORD_MIN_LENGTH, `${PASSWORD_MIN_LENGTH} caractères minimum.`)
  .max(PASSWORD_MAX_LENGTH, `${PASSWORD_MAX_LENGTH} caractères maximum.`)
  .refine((value) => /[A-ZÀ-Ý]/.test(value), "Doit contenir au moins une majuscule.")
  .refine((value) => /[a-zà-ÿ]/.test(value), "Doit contenir au moins une minuscule.")
  .refine((value) => /\d/.test(value), "Doit contenir au moins un chiffre.")
  .refine((value) => /[^\w\s]/.test(value), "Doit contenir au moins un caractère spécial.");
