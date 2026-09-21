import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  Outlet,
  RouterProvider,
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
} from "@tanstack/react-router";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import * as api from "@/lib/api";
import { loadProfile, resetProfileCache } from "@/lib/profile";
import { readPrefill } from "../prefill";
import { Launcher } from "./Launcher";

const PHRASE =
  "Hôtels indépendants de 10 à 50 salariés à Paris et dans les Hauts-de-Seine, avec site web, sauf les chaînes";

function renderLauncher() {
  const root = createRootRoute({ component: () => <Outlet /> });
  const routes = [
    createRoute({ getParentRoute: () => root, path: "/campagnes/nouvelle", component: Launcher }),
    createRoute({ getParentRoute: () => root, path: "/campagnes", component: () => <h1>Liste des campagnes</h1> }),
  ];
  const router = createRouter({
    routeTree: root.addChildren(routes),
    history: createMemoryHistory({ initialEntries: ["/campagnes/nouvelle"] }),
  });
  const queryClient = new QueryClient({ defaultOptions: { mutations: { retry: false } } });
  render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
  return router;
}

async function analyse(phrase: string) {
  fireEvent.change(await screen.findByLabelText("Description de la cible"), { target: { value: phrase } });
  fireEvent.click(screen.getByRole("button", { name: /Analyser/ }));
}

beforeEach(() => {
  resetProfileCache();
  sessionStorage.clear();
  vi.restoreAllMocks();
  // Jamais de réseau en test : par défaut le service IA est absent (API sans #134).
  vi.spyOn(api, "getIcpParseStatus").mockRejectedValue(new Error("API 404"));
});

describe("Launcher", () => {
  it("phrase → critères éditables → brouillon créé avec le bon payload", async () => {
    const post = vi
      .spyOn(api, "postCampagne")
      .mockResolvedValue({ campagne_id: "c-1", client_id: "k-1", nom: "Hôtels — Paris" });
    renderLauncher();
    await analyse(PHRASE);

    // Critères reconnus
    expect(screen.getByText("Hôtels")).toBeInTheDocument();
    expect(screen.getByText("75 · Paris")).toBeInTheDocument();
    expect(screen.getByText("92 · Hauts-de-Seine")).toBeInTheDocument();
    expect(screen.getByText("« indépendants »")).toBeInTheDocument();

    // Édition : retirer une zone, promouvoir un mot non traduit en mot-clé
    fireEvent.click(screen.getByRole("button", { name: "Retirer la zone 92 · Hauts-de-Seine" }));
    fireEvent.click(screen.getByRole("button", { name: "Utiliser indépendants comme mot-clé positif" }));
    expect(screen.queryByText("92 · Hauts-de-Seine")).not.toBeInTheDocument();

    // Création bloquée tant que le client et le produit manquent
    const create = screen.getByRole("button", { name: /Créer le brouillon/ });
    expect(create).toBeDisabled();
    fireEvent.change(screen.getByLabelText(/Client/), { target: { value: "Client Test" } });
    fireEvent.change(screen.getByLabelText(/Ce que vous vendez/), { target: { value: "Logiciel de réservation" } });
    expect(create).toBeEnabled();
    fireEvent.click(create);

    expect(await screen.findByRole("heading", { name: "Brouillon créé" })).toBeInTheDocument();
    expect(post).toHaveBeenCalledTimes(1);
    expect(post.mock.calls[0][0]).toMatchObject({
      nom_entreprise: "Client Test",
      produit_vendu: "Logiciel de réservation",
      nom: "Hôtels — Paris",
      description_icp: PHRASE,
      codes_naf: ["5510Z"],
      departements: ["75"],
      effectif_min: 10,
      effectif_max: 50,
      exiger_site_web: true,
      mots_cles_positifs: ["indépendants"],
      mots_cles_negatifs: ["chaînes"],
    });
    // Client et produit mémorisés pour la prochaine fois
    expect(loadProfile()).toMatchObject({ dernierClient: "Client Test", dernierProduit: "Logiciel de réservation" });
  });

  it("affiche l'erreur de l'API sans perdre la saisie", async () => {
    vi.spyOn(api, "postCampagne").mockRejectedValue(new Error("API 500 Internal Server Error"));
    renderLauncher();
    await analyse("hôtels à Paris");
    fireEvent.change(screen.getByLabelText(/Client/), { target: { value: "C" } });
    fireEvent.change(screen.getByLabelText(/Ce que vous vendez/), { target: { value: "P" } });
    fireEvent.click(screen.getByRole("button", { name: /Créer le brouillon/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent("API 500");
    expect(screen.getByText("75 · Paris")).toBeInTheDocument();
  });

  it("« Mode avancé » transmet les critères au formulaire complet", async () => {
    const router = renderLauncher();
    await analyse("dentistes en petite couronne");
    fireEvent.click(screen.getByRole("button", { name: "Mode avancé (formulaire complet)" }));
    await waitFor(() => expect(router.state.location.pathname).toBe("/campagnes"));
    expect(readPrefill()).toMatchObject({ codes_naf: "8623Z", departements: "92, 93, 94" });
  });

  it("un exemple s'analyse en un clic", async () => {
    renderLauncher();
    fireEvent.click(await screen.findByRole("button", { name: /Restaurants et bars à Lyon/ }));
    expect(screen.getByText("Restaurants")).toBeInTheDocument();
    expect(screen.getByText("69 · Rhône")).toBeInTheDocument();
    expect(screen.getByText(/ciblage sur tout le département 69/)).toBeInTheDocument();
  });
});

describe("Launcher — « Affiner avec l'IA »", () => {
  const PHRASE_IA = "Hôtels indépendants à Paris";

  it("reste caché tant que le serveur ne l'active pas", async () => {
    renderLauncher();
    await analyse(PHRASE_IA);
    expect(screen.getByText("« indépendants »")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Affiner avec l'IA/ })).not.toBeInTheDocument();
  });

  it("envoie les mots non traduits et fusionne la proposition", async () => {
    vi.spyOn(api, "getIcpParseStatus").mockResolvedValue({ enabled: true, modele: "claude-haiku-4-5" });
    const post = vi.spyOn(api, "postIcpParse").mockResolvedValue({
      codes_naf: [],
      departements: [],
      effectif_min: null,
      effectif_max: null,
      anciennete_min_ans: null,
      exiger_site_web: false,
      exiger_email: false,
      mots_cles_positifs: [],
      mots_cles_negatifs: ["groupe", "franchise"],
      non_traduits: [],
      hypotheses: ["indépendants : exclusion des réseaux et franchises"],
      modele: "claude-haiku-4-5",
      depuis_cache: false,
    });
    renderLauncher();
    await analyse(PHRASE_IA);
    fireEvent.click(await screen.findByRole("button", { name: /Affiner avec l'IA/ }));

    expect(await screen.findByText("« groupe »")).toBeInTheDocument();
    expect(screen.getByText("« franchise »")).toBeInTheDocument();
    expect(screen.queryByText("« indépendants »")).not.toBeInTheDocument();
    expect(screen.getByText("IA : indépendants : exclusion des réseaux et franchises")).toBeInTheDocument();
    expect(post).toHaveBeenCalledWith({ phrase: PHRASE_IA, non_traduits: ["indépendants"] });
  });

  it("garde les critères si l'IA échoue", async () => {
    vi.spyOn(api, "getIcpParseStatus").mockResolvedValue({ enabled: true, modele: "claude-haiku-4-5" });
    vi.spyOn(api, "postIcpParse").mockRejectedValue(new Error("API 503 Service Unavailable"));
    renderLauncher();
    await analyse(PHRASE_IA);
    fireEvent.click(await screen.findByRole("button", { name: /Affiner avec l'IA/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent("API 503");
    expect(screen.getByText("75 · Paris")).toBeInTheDocument();
    expect(screen.getByText("« indépendants »")).toBeInTheDocument();
  });
});
