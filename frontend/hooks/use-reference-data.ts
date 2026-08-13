"use client";

/** Hooks TanStack Query pour les données de référence (peu volatiles, mises en cache plus longtemps). */
import { useQuery } from "@tanstack/react-query";

import {
  categoriesApi,
  departmentsApi,
  equipmentApi,
  prioritiesApi,
  rolesApi,
  slasApi,
  statusesApi,
  teamsApi,
  usersApi,
} from "@/lib/api";

const REFERENCE_STALE_TIME = 5 * 60 * 1000;

export function useCategories() {
  return useQuery({
    queryKey: ["categories"],
    queryFn: () => categoriesApi.list().then((res) => res.data),
    staleTime: REFERENCE_STALE_TIME,
  });
}

export function usePriorities() {
  return useQuery({
    queryKey: ["priorities"],
    queryFn: () => prioritiesApi.list().then((res) => res.data),
    staleTime: REFERENCE_STALE_TIME,
  });
}

export function useStatuses() {
  return useQuery({
    queryKey: ["statuses"],
    queryFn: () => statusesApi.list().then((res) => res.data),
    staleTime: REFERENCE_STALE_TIME,
  });
}

export function useTeams() {
  return useQuery({
    queryKey: ["teams"],
    queryFn: () => teamsApi.list().then((res) => res.data),
    staleTime: REFERENCE_STALE_TIME,
  });
}

export function useDepartments() {
  return useQuery({
    queryKey: ["departments"],
    queryFn: () => departmentsApi.list().then((res) => res.data),
    staleTime: REFERENCE_STALE_TIME,
  });
}

export function useRoles() {
  return useQuery({
    queryKey: ["roles"],
    queryFn: () => rolesApi.list().then((res) => res.data),
    staleTime: REFERENCE_STALE_TIME,
  });
}

// Utilisées comme listes déroulantes (pas des pages consultées) : on demande le
// page_size maximum autorisé par l'API (100) plutôt que d'ajouter une interface
// de pagination ici. Au-delà de 100 techniciens/équipements, cette liste serait
// tronquée — limite connue et acceptée pour ce correctif (#07).
export function useTechnicians() {
  return useQuery({
    queryKey: ["users", { role: "Technicien", page_size: 100 }],
    queryFn: () => usersApi.list({ role: "Technicien", page_size: 100 }).then((res) => res.data.items),
    staleTime: REFERENCE_STALE_TIME,
  });
}

export function useEquipmentList() {
  return useQuery({
    queryKey: ["equipment", { page_size: 100 }],
    queryFn: () => equipmentApi.list({ page_size: 100 }).then((res) => res.data.items),
    staleTime: REFERENCE_STALE_TIME,
  });
}

export function useSlas() {
  return useQuery({
    queryKey: ["slas"],
    queryFn: () => slasApi.list().then((res) => res.data),
    staleTime: REFERENCE_STALE_TIME,
  });
}
