from pydantic import BaseModel


class DashboardStatistics(BaseModel):
    total_tickets: int
    tickets_ouverts: int
    tickets_en_cours: int
    tickets_en_attente: int
    tickets_resolus: int
    tickets_fermes: int
    tickets_critiques: int
    tickets_sla_depasse: int
    temps_moyen_resolution_heures: float | None
    temps_moyen_premiere_reponse_minutes: float | None
    satisfaction_moyenne: float | None


class CountByLabel(BaseModel):
    label: str
    count: int


class TechnicianStats(BaseModel):
    technician_id: int
    technician_name: str
    tickets_assignes: int
    tickets_resolus: int
    temps_moyen_resolution_heures: float | None


class SLAOverview(BaseModel):
    total_avec_sla: int
    respectes: int
    bientot_depasses: int
    depasses: int
    taux_respect_pourcent: float
