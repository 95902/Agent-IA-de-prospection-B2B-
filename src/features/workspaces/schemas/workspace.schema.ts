import { z } from "zod";
import { DEPARTEMENTS_VALUES } from "../seed";

export const WorkspaceFormSchema1 = z.object({
  customerName: z
    .string()
    .min(2, "Le nom de la campagne doit faire au moins 2 caractères"),
  industry: z.enum(DEPARTEMENTS_VALUES, {
    error: "Veuillez choisir une industrie valide",
  }),
  contact: z
    .string()
    .min(2, "Le nom du contact doit faire au moins 2 caractères"),
  email: z.string().min(2, "L'email doit faire au moins 2 caractères"),
});

export type WorkspaceForm1Values = z.infer<typeof WorkspaceFormSchema1>;

export const WorkspaceFormSchema2 = z.object({
  customerName: z
    .string()
    .min(2, "Le nom du client doit faire au moins 2 caractères"),
  code: z
    .string()
    .length(
      5,
      "Le code SIG / NAF doit faire exactement 5 caractères (ex: 7022Z)",
    ),
  numberEmploye: z.string().min(1, "Le nombre de clients doit être inscript"),
});

export type WorkspaceForm2Values = z.infer<typeof WorkspaceFormSchema2>;
