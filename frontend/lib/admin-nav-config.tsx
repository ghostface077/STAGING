import {
  BookOpen,
  Building2,
  FileClock,
  Laptop,
  LayoutDashboard,
  LineChart,
  ListTree,
  Settings,
  ShieldCheck,
  Tags,
  Ticket,
  Timer,
  Users,
  Bell,
  UserSquare2,
} from "lucide-react";

export interface AdminNavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

export interface AdminNavGroup {
  label: string;
  items: AdminNavItem[];
}

/** Navigation du back-office administrateur (/admin/*), groupée par domaine. */
export const ADMIN_NAV_GROUPS: AdminNavGroup[] = [
  {
    label: "Vue d'ensemble",
    items: [
      { label: "Tableau de bord", href: "/admin/dashboard", icon: LayoutDashboard },
      { label: "Tickets", href: "/admin/tickets", icon: Ticket },
      { label: "Rapports", href: "/admin/reports", icon: LineChart },
    ],
  },
  {
    label: "Organisation",
    items: [
      { label: "Utilisateurs", href: "/admin/users", icon: Users },
      { label: "Rôles", href: "/admin/roles", icon: ShieldCheck },
      { label: "Services", href: "/admin/departments", icon: Building2 },
      { label: "Équipes", href: "/admin/teams", icon: UserSquare2 },
    ],
  },
  {
    label: "Référentiels",
    items: [
      { label: "Catégories", href: "/admin/categories", icon: ListTree },
      { label: "Priorités", href: "/admin/priorities", icon: Tags },
      { label: "Statuts", href: "/admin/statuses", icon: Tags },
      { label: "SLA", href: "/admin/slas", icon: Timer },
      { label: "Équipements", href: "/admin/equipment", icon: Laptop },
      { label: "Base de connaissances", href: "/admin/knowledge-base", icon: BookOpen },
    ],
  },
  {
    label: "Système",
    items: [
      { label: "Notifications", href: "/admin/notifications", icon: Bell },
      { label: "Journal d'audit", href: "/admin/audit-logs", icon: FileClock },
      { label: "Paramètres", href: "/admin/settings", icon: Settings },
    ],
  },
];

/** Version à plat (utilisée là où le regroupement n'est pas nécessaire). */
export const ADMIN_NAV: AdminNavItem[] = ADMIN_NAV_GROUPS.flatMap((group) => group.items);
