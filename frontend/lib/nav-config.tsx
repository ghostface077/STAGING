import {
  BookOpen,
  Gauge,
  Laptop,
  LayoutDashboard,
  LineChart,
  ListChecks,
  Timer,
  Ticket,
  UserCog,
  Users,
} from "lucide-react";

import type { RoleName } from "@/lib/types";

export interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  roles?: RoleName[]; // si absent : visible par tous les rôles connectés
}

export interface NavGroup {
  label: string;
  items: NavItem[];
}

/** Navigation principale du portail (hors back-office /admin), groupée et adaptée au rôle connecté. */
export const PORTAL_NAV_GROUPS: NavGroup[] = [
  {
    label: "Principal",
    items: [
      { label: "Tableau de bord", href: "/dashboard", icon: LayoutDashboard },
      {
        label: "Tous les tickets",
        href: "/tickets",
        icon: Ticket,
        roles: ["Responsable IT", "Administrateur"],
      },
      { label: "Mes tickets", href: "/mes-tickets", icon: ListChecks },
      {
        label: "Non assignés",
        href: "/tickets/non-assignes",
        icon: Gauge,
        roles: ["Technicien", "Responsable IT", "Administrateur"],
      },
    ],
  },
  {
    label: "Support",
    items: [
      { label: "Équipements", href: "/equipment", icon: Laptop },
      { label: "Base de connaissances", href: "/knowledge-base", icon: BookOpen },
    ],
  },
  {
    label: "Analyse",
    items: [
      { label: "Équipes", href: "/teams", icon: Users, roles: ["Responsable IT", "Administrateur"] },
      { label: "Techniciens", href: "/technicians", icon: UserCog, roles: ["Responsable IT", "Administrateur"] },
      { label: "SLA", href: "/slas", icon: Timer, roles: ["Responsable IT", "Administrateur"] },
      { label: "Rapports", href: "/reports", icon: LineChart, roles: ["Responsable IT", "Administrateur"] },
    ],
  },
];

export function getPortalNavGroupsForRole(role: string | undefined): NavGroup[] {
  if (!role) return [];
  return PORTAL_NAV_GROUPS.map((group) => ({
    ...group,
    items: group.items.filter((item) => !item.roles || (item.roles as readonly string[]).includes(role)),
  })).filter((group) => group.items.length > 0);
}
