import {
  AlertTriangle,
  Bell,
  CheckCircle2,
  Clock,
  MessageSquare,
  PlusCircle,
  RotateCcw,
  ShieldAlert,
  UserPlus,
  Workflow,
  XCircle,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

/** Une icône par type de notification (miroir de NOTIFICATION_TYPE_LABELS dans lib/constants.ts). */
export const NOTIFICATION_TYPE_ICONS: Record<string, LucideIcon> = {
  creation_ticket: PlusCircle,
  attribution: UserPlus,
  nouveau_commentaire: MessageSquare,
  changement_statut: Workflow,
  changement_priorite: AlertTriangle,
  resolution: CheckCircle2,
  fermeture: XCircle,
  reouverture: RotateCcw,
  sla_bientot_depasse: Clock,
  sla_depasse: ShieldAlert,
};

export function notificationIcon(type: string): LucideIcon {
  return NOTIFICATION_TYPE_ICONS[type] ?? Bell;
}
