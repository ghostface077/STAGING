/**
 * Client HTTP central pour communiquer avec l'API backend (FastAPI), ainsi que
 * l'ensemble des fonctions d'accès aux données, regroupées par domaine métier.
 */
import axios, { AxiosError } from "axios";

import type {
  AuditLog,
  Category,
  Comment,
  CountByLabel,
  DashboardStatistics,
  Department,
  Equipment,
  KnowledgeBaseArticle,
  Notification,
  Page,
  Priority,
  Role,
  SLA,
  SLAOverview,
  SatisfactionRating,
  Status,
  Team,
  TechnicianStats,
  Ticket,
  TicketHistoryEntry,
  TicketListItem,
  User,
} from "@/lib/types";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

// Correctif #12 : l'access token et le refresh token sont portés par des
// cookies httpOnly posés par le serveur — plus de lecture/écriture de
// localStorage ni d'en-tête Authorization manuel (le navigateur joint les
// cookies automatiquement). withCredentials est nécessaire pour que ces
// cookies soient envoyés/acceptés en cross-origin (front et API sur des ports
// différents en développement) ; le backend autorise déjà les credentials
// pour l'origine configurée (voir CORSMiddleware dans app/main.py).
export const apiClient = axios.create({ baseURL: API_BASE_URL, withCredentials: true });

/** Empêche plusieurs requêtes en échec simultané de déclencher chacune leur
 * propre appel /auth/refresh (le refresh token est remplacé à chaque usage —
 * rotation, correctif #12 — donc un appel concurrent redondant échouerait). */
let refreshPromise: Promise<boolean> | null = null;

function attemptRefresh(): Promise<boolean> {
  if (!refreshPromise) {
    refreshPromise = apiClient
      .post("/auth/refresh")
      .then(() => true)
      .catch(() => false)
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as (AxiosError["config"] & { _retry?: boolean }) | undefined;
    const url = originalRequest?.url ?? "";
    const isAuthEndpoint = url.includes("/auth/login") || url.includes("/auth/refresh") || url.includes("/auth/register");

    if (error.response?.status === 401 && originalRequest && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true;
      const refreshed = await attemptRefresh();
      if (refreshed) {
        return apiClient(originalRequest);
      }
    }

    if (error.response?.status === 401 && typeof window !== "undefined" && !window.location.pathname.includes("/login")) {
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);

/** Extrait un message d'erreur en français exploitable par l'interface depuis une erreur Axios. */
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as { message?: string; detail?: string } | undefined;
    return data?.message || data?.detail || "Une erreur inattendue est survenue. Merci de réessayer.";
  }
  return "Une erreur inattendue est survenue. Merci de réessayer.";
}

// --- Authentification ---
// Correctif #12 : la connexion/inscription ne renvoie plus de jeton dans le
// corps de la réponse (posé en cookie httpOnly), uniquement l'utilisateur.
export const authApi = {
  login: (email: string, password: string) => apiClient.post<{ user: User }>("/auth/login", { email, password }),
  register: (payload: { first_name: string; last_name: string; email: string; password: string; phone?: string }) =>
    apiClient.post<{ user: User }>("/auth/register", payload),
  me: () => apiClient.get<User>("/auth/me"),
  logout: () => apiClient.post("/auth/logout"),
};

// --- Utilisateurs ---
export const usersApi = {
  list: (params?: Record<string, string | number | undefined>) => apiClient.get<Page<User>>("/users", { params }),
  get: (id: number) => apiClient.get<User>(`/users/${id}`),
  create: (payload: Record<string, unknown>) => apiClient.post<User>("/users", payload),
  update: (id: number, payload: Record<string, unknown>) => apiClient.put<User>(`/users/${id}`, payload),
  remove: (id: number) => apiClient.delete(`/users/${id}`),
  updateMyProfile: (payload: { first_name?: string; last_name?: string; phone?: string }) =>
    apiClient.put<User>("/users/moi/profil", payload),
  changeMyPassword: (payload: { current_password: string; new_password: string }) =>
    apiClient.put("/users/moi/mot-de-passe", payload),
};

// --- Référentiels ---
export const rolesApi = {
  list: () => apiClient.get<Role[]>("/roles"),
  create: (payload: Record<string, unknown>) => apiClient.post<Role>("/roles", payload),
  update: (id: number, payload: Record<string, unknown>) => apiClient.put<Role>(`/roles/${id}`, payload),
  remove: (id: number) => apiClient.delete(`/roles/${id}`),
};

export const departmentsApi = {
  list: () => apiClient.get<Department[]>("/departments"),
  create: (payload: Record<string, unknown>) => apiClient.post<Department>("/departments", payload),
  update: (id: number, payload: Record<string, unknown>) => apiClient.put<Department>(`/departments/${id}`, payload),
  remove: (id: number) => apiClient.delete(`/departments/${id}`),
};

export const teamsApi = {
  list: () => apiClient.get<Team[]>("/teams"),
  get: (id: number) => apiClient.get<Team>(`/teams/${id}`),
  create: (payload: Record<string, unknown>) => apiClient.post<Team>("/teams", payload),
  update: (id: number, payload: Record<string, unknown>) => apiClient.put<Team>(`/teams/${id}`, payload),
  remove: (id: number) => apiClient.delete(`/teams/${id}`),
};

export const categoriesApi = {
  list: () => apiClient.get<Category[]>("/categories"),
  create: (payload: Record<string, unknown>) => apiClient.post<Category>("/categories", payload),
  update: (id: number, payload: Record<string, unknown>) => apiClient.put<Category>(`/categories/${id}`, payload),
  remove: (id: number) => apiClient.delete(`/categories/${id}`),
};

export const prioritiesApi = {
  list: () => apiClient.get<Priority[]>("/priorities"),
  create: (payload: Record<string, unknown>) => apiClient.post<Priority>("/priorities", payload),
  update: (id: number, payload: Record<string, unknown>) => apiClient.put<Priority>(`/priorities/${id}`, payload),
  remove: (id: number) => apiClient.delete(`/priorities/${id}`),
};

export const statusesApi = {
  list: () => apiClient.get<Status[]>("/statuses"),
  create: (payload: Record<string, unknown>) => apiClient.post<Status>("/statuses", payload),
  update: (id: number, payload: Record<string, unknown>) => apiClient.put<Status>(`/statuses/${id}`, payload),
  remove: (id: number) => apiClient.delete(`/statuses/${id}`),
};

export const slasApi = {
  list: () => apiClient.get<SLA[]>("/slas"),
  create: (payload: Record<string, unknown>) => apiClient.post<SLA>("/slas", payload),
  update: (id: number, payload: Record<string, unknown>) => apiClient.put<SLA>(`/slas/${id}`, payload),
  remove: (id: number) => apiClient.delete(`/slas/${id}`),
};

// --- Équipements ---
export const equipmentApi = {
  list: (params?: Record<string, string | number | undefined>) => apiClient.get<Page<Equipment>>("/equipment", { params }),
  get: (id: number) => apiClient.get<Equipment>(`/equipment/${id}`),
  tickets: (id: number) => apiClient.get<TicketListItem[]>(`/equipment/${id}/tickets`),
  create: (payload: Record<string, unknown>) => apiClient.post<Equipment>("/equipment", payload),
  update: (id: number, payload: Record<string, unknown>) => apiClient.put<Equipment>(`/equipment/${id}`, payload),
  remove: (id: number) => apiClient.delete(`/equipment/${id}`),
};

// --- Tickets ---
export const ticketsApi = {
  list: (params?: Record<string, string | number | boolean | undefined>) =>
    apiClient.get<Page<TicketListItem>>("/tickets", { params }),
  get: (id: number) => apiClient.get<Ticket>(`/tickets/${id}`),
  history: (id: number) => apiClient.get<TicketHistoryEntry[]>(`/tickets/${id}/history`),
  create: (payload: Record<string, unknown>) => apiClient.post<Ticket>("/tickets", payload),
  update: (id: number, payload: Record<string, unknown>) => apiClient.put<Ticket>(`/tickets/${id}`, payload),
  remove: (id: number) => apiClient.delete(`/tickets/${id}`),
  assign: (id: number, payload: { technician_id?: number | null; team_id?: number | null }) =>
    apiClient.post<Ticket>(`/tickets/${id}/assign`, payload),
  changeStatus: (id: number, status_id: number) => apiClient.post<Ticket>(`/tickets/${id}/status`, { status_id }),
  changePriority: (id: number, priority_id: number) => apiClient.post<Ticket>(`/tickets/${id}/priority`, { priority_id }),
  resolve: (id: number, solution: string) => apiClient.post<Ticket>(`/tickets/${id}/resolve`, { solution }),
  close: (id: number) => apiClient.post<Ticket>(`/tickets/${id}/close`),
  reopen: (id: number) => apiClient.post<Ticket>(`/tickets/${id}/reopen`),
  escalate: (id: number, payload: { team_id?: number | null; technician_id?: number | null; reason?: string }) =>
    apiClient.post<Ticket>(`/tickets/${id}/escalate`, payload),
};

// --- Commentaires & pièces jointes ---
export const commentsApi = {
  list: (ticketId: number) => apiClient.get<Comment[]>(`/tickets/${ticketId}/comments`),
  create: (ticketId: number, payload: { content: string; is_internal: boolean }) =>
    apiClient.post<Comment>(`/tickets/${ticketId}/comments`, payload),
  update: (commentId: number, content: string) => apiClient.put<Comment>(`/comments/${commentId}`, { content }),
  remove: (commentId: number) => apiClient.delete(`/comments/${commentId}`),
};

export const attachmentsApi = {
  upload: (ticketId: number, file: File, commentId?: number) => {
    const formData = new FormData();
    formData.append("file", file);
    const params = commentId ? { comment_id: commentId } : undefined;
    return apiClient.post(`/tickets/${ticketId}/attachments`, formData, {
      params,
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  downloadUrl: (attachmentId: number) => `${API_BASE_URL}/attachments/${attachmentId}/download`,
  remove: (attachmentId: number) => apiClient.delete(`/attachments/${attachmentId}`),
};

// --- Notifications ---
export const notificationsApi = {
  list: (unreadOnly = false) => apiClient.get<Notification[]>("/notifications", { params: { unread_only: unreadOnly } }),
  unreadCount: () => apiClient.get<{ unread: number }>("/notifications/nombre-non-lues"),
  markAsRead: (id: number) => apiClient.post<Notification>(`/notifications/${id}/lue`),
  markAllAsRead: () => apiClient.post("/notifications/tout-marquer-lu"),
};

// --- Base de connaissances ---
export const knowledgeBaseApi = {
  list: (params?: Record<string, string | number | undefined>) =>
    apiClient.get<Page<KnowledgeBaseArticle>>("/knowledge-base", { params }),
  get: (id: number) => apiClient.get<KnowledgeBaseArticle>(`/knowledge-base/${id}`),
  create: (payload: Record<string, unknown>) => apiClient.post<KnowledgeBaseArticle>("/knowledge-base", payload),
  update: (id: number, payload: Record<string, unknown>) =>
    apiClient.put<KnowledgeBaseArticle>(`/knowledge-base/${id}`, payload),
  remove: (id: number) => apiClient.delete(`/knowledge-base/${id}`),
};

// --- Satisfaction ---
export const satisfactionApi = {
  get: (ticketId: number) => apiClient.get<SatisfactionRating | null>(`/tickets/${ticketId}/satisfaction`),
  create: (ticketId: number, payload: { rating: number; comment?: string }) =>
    apiClient.post<SatisfactionRating>(`/tickets/${ticketId}/satisfaction`, payload),
};

// --- Tableau de bord ---
export const dashboardApi = {
  statistics: () => apiClient.get<DashboardStatistics>("/dashboard/statistics"),
  byStatus: () => apiClient.get<CountByLabel[]>("/dashboard/tickets-by-status"),
  byPriority: () => apiClient.get<CountByLabel[]>("/dashboard/tickets-by-priority"),
  byCategory: () => apiClient.get<CountByLabel[]>("/dashboard/tickets-by-category"),
  byTechnician: () => apiClient.get<TechnicianStats[]>("/dashboard/tickets-by-technician"),
  slaOverview: () => apiClient.get<SLAOverview>("/dashboard/sla"),
};

// --- Rapports ---
export const reportsApi = {
  summary: (params?: { date_from?: string; date_to?: string }) =>
    apiClient.get<DashboardStatistics>("/reports/summary", { params }),
  exportCsvUrl: (params?: { date_from?: string; date_to?: string }) => {
    const query = new URLSearchParams(params as Record<string, string>).toString();
    return `${API_BASE_URL}/reports/export.csv${query ? `?${query}` : ""}`;
  },
  exportPdfUrl: (params?: { date_from?: string; date_to?: string }) => {
    const query = new URLSearchParams(params as Record<string, string>).toString();
    return `${API_BASE_URL}/reports/export.pdf${query ? `?${query}` : ""}`;
  },
};

// --- Journal d'audit ---
export const auditLogsApi = {
  list: (params?: Record<string, string | number | undefined>) => apiClient.get<AuditLog[]>("/audit-logs", { params }),
};
