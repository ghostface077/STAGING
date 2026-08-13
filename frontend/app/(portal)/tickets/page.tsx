"use client";

import { useQuery } from "@tanstack/react-query";
import { ListFilter, PlusCircle, Search, X } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useState } from "react";

import { PageHeader } from "@/components/common/page-header";
import { Pagination } from "@/components/ui/pagination";
import { TicketTable } from "@/components/tickets/ticket-table";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useCategories, usePriorities, useStatuses } from "@/hooks/use-reference-data";
import { ticketsApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

const PAGE_SIZE = 15;

export default function TicketsPage() {
  const { user } = useAuth();
  const searchParams = useSearchParams();
  const [search, setSearch] = useState(searchParams.get("search") ?? "");
  const [statusId, setStatusId] = useState<string>("tous");
  const [priorityId, setPriorityId] = useState<string>("toutes");
  const [categoryId, setCategoryId] = useState<string>("toutes");
  const [page, setPage] = useState(1);

  const { data: statuses } = useStatuses();
  const { data: priorities } = usePriorities();
  const { data: categories } = useCategories();

  const { data, isLoading } = useQuery({
    queryKey: ["tickets", { search, statusId, priorityId, categoryId, page }],
    queryFn: () =>
      ticketsApi
        .list({
          search: search || undefined,
          status_id: statusId !== "tous" ? Number(statusId) : undefined,
          priority_id: priorityId !== "toutes" ? Number(priorityId) : undefined,
          category_id: categoryId !== "toutes" ? Number(categoryId) : undefined,
          page,
          page_size: PAGE_SIZE,
        })
        .then((res) => res.data),
    placeholderData: (previous) => previous, // évite un flash de tableau vide entre deux pages
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
          {hasActiveFilters && (
            <Button variant="ghost" size="sm" onClick={resetFilters}>
              <X className="h-3.5 w-3.5" /> Réinitialiser
            </Button>
          )}
        </div>

        <TicketTable tickets={tickets} isLoading={isLoading} />
        <Pagination page={page} pageCount={pageCount} onPageChange={setPage} totalItems={data?.total} pageSize={PAGE_SIZE} />
      </Card>
    </div>
  );
}
