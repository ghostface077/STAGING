"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "@/components/ui/button";

interface PaginationProps {
  page: number;
  pageCount: number;
  onPageChange: (page: number) => void;
  totalItems?: number;
  pageSize?: number;
}

/** Pagination simple avec indicateur de page et navigation précédent/suivant. */
export function Pagination({ page, pageCount, onPageChange, totalItems, pageSize }: PaginationProps) {
  if (pageCount <= 1) return null;

  const rangeStart = totalItems && pageSize ? (page - 1) * pageSize + 1 : undefined;
  const rangeEnd = totalItems && pageSize ? Math.min(page * pageSize, totalItems) : undefined;

  return (
    <div className="flex flex-col items-center justify-between gap-3 border-t border-border px-2 py-3 sm:flex-row">
      <p className="text-sm text-muted-foreground">
        {totalItems !== undefined && rangeStart && rangeEnd
          ? `Affichage de ${rangeStart} à ${rangeEnd} sur ${totalItems} résultats`
          : `Page ${page} sur ${pageCount}`}
      </p>
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" onClick={() => onPageChange(page - 1)} disabled={page <= 1}>
          <ChevronLeft />
          Précédent
        </Button>
        <span className="text-sm text-muted-foreground">
          {page} / {pageCount}
        </span>
        <Button variant="outline" size="sm" onClick={() => onPageChange(page + 1)} disabled={page >= pageCount}>
          Suivant
          <ChevronRight />
        </Button>
      </div>
    </div>
  );
}
