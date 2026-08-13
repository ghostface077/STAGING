/**
 * Types TypeScript correspondant aux schémas de l'API backend (FastAPI / Pydantic).
 * Toute donnée provenant de l'API doit être typée ici pour garder le frontend cohérent.
 */

export interface Role {
  id: number;
  name: string;
  description: string | null;
}

export interface Department {
  id: number;
  name: string;
  description: string | null;
}

export interface UserSummary {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
}

export interface User extends UserSummary {
  phone: string | null;
  role_id: number;
  department_id: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  role: Role | null;
  department: Department | null;
}

export interface Team {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
  members: UserSummary[];
}

export interface Category {
  id: number;
  name: string;
  description: string | null;
  parent_id: number | null;
  created_at: string;
  updated_at: string;
  children: Category[];
}

export interface Priority {
  id: number;
  name: string;
  level: number;
  description: string | null;
}

export interface Status {
  id: number;
  name: string;
  description: string | null;
}

export interface SLA {
  id: number;
  name: string;
  priority_id: number;
  first_response_minutes: number;
  resolution_minutes: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  priority: Priority | null;
}

export type SLAState = "normal" | "attention" | "critique" | "depasse" | "aucun";

export interface SLAProgress {
  sla_id: number | null;
  sla_name: string | null;
  first_response_deadline: string | null;
  resolution_deadline: string | null;
  first_response_met: boolean | null;
  minutes_remaining: number | null;
  percent_elapsed: number | null;
  state: SLAState;
}

export interface Equipment {
  id: number;
  asset_number: string;
  type: string;
  brand: string;
  model: string;
  serial_number: string | null;
  user_id: number | null;
  department_id: number | null;
  operating_system: string | null;
  purchase_date: string | null;
  warranty_end_date: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  user: UserSummary | null;
  department: Department | null;
}

export interface TicketListItem {
  id: number;
  reference: string;
  title: string;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  requester: UserSummary;
  technician: UserSummary | null;
  team: Team | null;
  category: Category;
  priority: Priority;
  status: Status;
  sla_progress: SLAProgress | null;
}

export interface Ticket extends TicketListItem {
  description: string;
  solution: string | null;
  equipment_id: number | null;
  sla: SLA | null;
  closed_at: string | null;
  first_response_at: string | null;
}

export interface Attachment {
  id: number;
  file_name: string;
  file_type: string;
  file_size: number;
  created_at: string;
}

export interface Comment {
  id: number;
  ticket_id: number;
  content: string;
  is_internal: boolean;
  created_at: string;
  updated_at: string;
  user: UserSummary;
  attachments: Attachment[];
}

export interface TicketHistoryEntry {
  id: number;
  ticket_id: number;
  action: string;
  old_value: string | null;
  new_value: string | null;
  created_at: string;
  user: UserSummary | null;
}

export interface Notification {
  id: number;
  ticket_id: number | null;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  created_at: string;
}

export interface KnowledgeBaseArticle {
  id: number;
  title: string;
  content: string;
  status: string;
  views: number;
  created_at: string;
  updated_at: string;
  category: Category | null;
  author: UserSummary | null;
}

export interface SatisfactionRating {
  id: number;
  ticket_id: number;
  rating: number;
  comment: string | null;
  created_at: string;
}

export interface AuditLog {
  id: number;
  action: string;
  entity_type: string;
  entity_id: number | null;
  ip_address: string | null;
  created_at: string;
  user: UserSummary | null;
}

export interface DashboardStatistics {
  total_tickets: number;
  tickets_ouverts: number;
  tickets_en_cours: number;
  tickets_en_attente: number;
  tickets_resolus: number;
  tickets_fermes: number;
  tickets_critiques: number;
  tickets_sla_depasse: number;
  temps_moyen_resolution_heures: number | null;
  temps_moyen_premiere_reponse_minutes: number | null;
  satisfaction_moyenne: number | null;
}

export interface CountByLabel {
  label: string;
  count: number;
}

export interface TechnicianStats {
  technician_id: number;
  technician_name: string;
  tickets_assignes: number;
  tickets_resolus: number;
  temps_moyen_resolution_heures: number | null;
}

export interface SLAOverview {
  total_avec_sla: number;
  respectes: number;
  bientot_depasses: number;
  depasses: number;
  taux_respect_pourcent: number;
}

export type RoleName = "Utilisateur" | "Technicien" | "Responsable IT" | "Administrateur";
