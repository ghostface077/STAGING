"use client";

import { useQuery } from "@tanstack/react-query";
import { Kanban, LayoutGrid, ListFilter, PlusCircle, Rows3, Search, SlidersHorizontal, X } from "lucide-react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { PageHeader } from "@/components/common/page-header";
import { Pagination } from "@/components/ui/pagination";
import { TicketCardGrid } from "@/components/tickets/ticket-card";
import { TicketTable } from "@/components/tickets/ticket-table";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useDebouncedValue } from "@/hooks/use-debounced-value";
import { useCategories, usePriorities, useStatuses } from "@/hooks/use-reference-data";
import { ticketsApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

// Chargé à la demande : la logique de glisser-déposer ne sert que si l'utilisateur
// choisit la vue Kanban (pas la vue par défaut) - inutile de l'envoyer au chargement
// initial de la page.
const TicketKanban = dynamic(() => import("@/components/tickets/ticket-kanban").then((mod) => mod.TicketKanban), {
  ssr: false,
  loading: () => (
    <div className="flex gap-3 overflow-x-auto p-4">
      {Array.from({ length: 5 }).map((_, index) => <Skeleton key={index} className="h-96 w-72 shrink-0" />)}
    </div>
  ),
});

const PAGE_SIZE = 15;
const WIDE_PAGE_SIZE = 100; // vues Cartes/Kanban : pas de pagination dédiée (même convention que Mes tickets / Non assignés)
type View = "tableau" | "cartes" | "kanban";
const VIEW_STORAGE_KEY = "tickets-view";

export default function TicketsPage() {
  const { user } = useAuth();
  const searchParams = useSearchParams();
  const [search, setSearch] = useState(searchParams.get("search") ?? "");
  const debouncedSearch = useDebouncedValue(search, 250);
  const [statusId, setStatusId] = useState<string>("tous");
  const [priorityId, setPriorityId] = useState<string>("toutes");
  const [categoryId, setCategoryId] = useState<string>("toutes");
  const [sortBy, setSortBy] = useState<string>("recent");
  const [page, setPage] = useState(1);
  const [view, setView] = useState<View>("tableau");

  useEffect(() => {
    const stored = window.localStorage.getItem(VIEW_STORAGE_KEY);
    if (stored === "tableau" || stored === "cartes" || stored === "kanban") setView(stored);
  }, []);
  const changeView = (next: View) => {
    setView(next);
    window.localStorage.setItem(VIEW_STORAGE_KEY, next);
  };

  const { data: statuses } = useStatuses();
  const { data: priorities } = usePriorities();
  const { data: categories } = useCategories();

  const isWideView = view !== "tableau";

  const { data, isLoading } = useQuery({
    queryKey: ["tickets", { search: debouncedSearch, statusId, priorityId, categoryId, sortBy, page, wide: isWideView }],
    queryFn: () =>
      ticketsApi
        .list({
          search: debouncedSearch || undefined,
          status_id: statusId !== "tous" ? Number(statusId) : undefined,
          priority_id: priorityId !== "toutes" ? Number(priorityId) : undefined,
          category_id: categoryId !== "toutes" ? Number(categoryId) : undefined,
          sort_by: sortBy !== "recent" ? sortBy : undefined,
          page: isWideView ? 1 : page,
          page_size: isWideView ? WIDE_PAGE_SIZE : PAGE_SIZE,
        })
        .then((res) => res.data),
    placeholderData: (previous) => previous, // évite un flash de contenu vide entre deux pages/vues
  });

  const tickets = data?.items ?? [];
  const pageCount = data?.pages ?? 1;

  const resetFilters = () => {
    setSearch("");
    setStatusId("tous");
    setPriorityId("toutes");
    setCategoryId("toutes");
    setPage(1);
  };

  const hasActiveFilters = search || statusId !== "tous" || priorityId !== "toutes" || categoryId !== "toutes";

  return (
    <div>
      <PageHeader
        title="Tous les tickets"
        description="Recherchez, filtrez et consultez l'ensemble des tickets."
        actions={
          user?.role?.name === "Utilisateur" ? (
            <Button asChild>
              <Link href="/tickets/nouveau">
                <PlusCircle /> Nouveau ticket
              </Link>
            </Button>
          ) : undefined
        }
      />

      <Card>
        <div className="flex flex-col gap-3 border-b border-border p-4 md:flex-row md:items-center">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                setPage(1);
              }}
              placeholder="Rechercher par référence ou titre…"
              className="pl-8"
            />
          </div>
          <Select value={statusId} onValueChange={(value) => { setStatusId(value); setPage(1); }}>
            <SelectTrigger className="w-full md:w-44"><ListFilter className="h-4 w-4 opacity-60" /><SelectValue placeholder="Statut" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="tous">Tous les statuts</SelectItem>
              {statuses?.map((status) => (
                <SelectItem key={status.id} value={String(status.id)}>{status.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={priorityId} onValueChange={(value) => { setPriorityId(value); setPage(1); }}>
            <SelectTrigger className="w-full md:w-44"><SelectValue placeholder="Priorité" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="toutes">Toutes les priorités</SelectItem>
              {priorities?.map((priority) => (
                <SelectItem key={priority.id} value={String(priority.id)}>{priority.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={categoryId} onValueChange={(value) => { setCategoryId(value); setPage(1); }}>
            <SelectTrigger className="w-full md:w-48"><SelectValue placeholder="Catégorie" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="toutes">Toutes les catégories</SelectItem>
              {categories?.map((category) => (
                <SelectItem key={category.id} value={String(category.id)}>{category.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={sortBy} onValueChange={setSortBy}>
            <SelectTrigger className="w-full md:w-40"><SlidersHorizontal className="h-4 w-4 opacity-60" /><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="recent">Plus récents</SelectItem>
              <SelectItem value="priority">Plus urgents</SelectItem>
            </SelectContent>
          </Select>
          {hasActiveFilters && (
            <Button variant="ghost" size="sm" onClick={resetFilters}>
              <X className="h-3.5 w-3.5" /> Réinitialiser
            </Button>
          )}
        </div>

        <div className="flex items-center justify-between gap-3 border-b border-border px-4 py-2.5">
          <Tabs value={view} onValueChange={(value) => changeView(value as View)}>
            <TabsList>
              <TabsTrigger value="tableau" className="gap-1.5"><Rows3 className="h-3.5 w-3.5" /> Tableau</TabsTrigger>
              <TabsTrigger value="cartes" className="gap-1.5"><LayoutGrid className="h-3.5 w-3.5" /> Cartes</TabsTrigger>
              <TabsTrigger value="kanban" className="gap-1.5"><Kanban className="h-3.5 w-3.5" /> Kanban</TabsTrigger>
            </TabsList>
          </Tabs>
          {data && (
            <span className="text-xs text-muted-foreground">
              {data.total} ticket{data.total > 1 ? "s" : ""}
            </span>
          )}
        </div>

        {view === "tableau" && <TicketTable tickets={tickets} isLoading={isLoading} />}
        {view === "cartes" && <TicketCardGrid tickets={tickets} isLoading={isLoading} />}
        {view === "kanban" && <TicketKanban tickets={tickets} isLoading={isLoading} />}

        {view === "tableau" && (
          <Pagination page={page} pageCount={pageCount} onPageChange={setPage} totalItems={data?.total} pageSize={PAGE_SIZE} />
        )}
      </Card>
    </div>
  );
}
