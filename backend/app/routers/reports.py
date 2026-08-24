"""
API de rapports : synthèse chiffrée sur une période, export CSV et export PDF.
`_compute_summary` et `_ticket_rows` sont partagées entre `/summary`,
`/export.csv` et `/export.pdf` pour ne jamais faire diverger les chiffres
d'un format à l'autre.
"""
import csv
import io
from datetime import date, datetime, time, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import require_manager
from app.models.satisfaction_rating import SatisfactionRating
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.dashboard import DashboardStatistics
from app.services.sla_service import compute_sla_progress

router = APIRouter(prefix="/api/reports", tags=["Rapports"])


def _sanitize_csv_field(value: str | None) -> str:
    """Neutralise une valeur avant écriture dans le CSV, pour empêcher toute
    interprétation comme formule par un tableur (Excel/LibreOffice/Google
    Sheets) — correctif #11, injection CSV / Formula Injection (CWE-1236).
    Une valeur commençant par =, +, -, @, tabulation ou retour chariot est
    préfixée d'une apostrophe, qui neutralise la formule sans altérer le
    contenu visible ; toute autre valeur est retournée strictement inchangée.
    Spécifique au risque CSV/tableur — un PDF n'y est pas exposé, cette
    fonction n'est donc utilisée que par export_csv."""
    if value is None:
        return ""
    text = str(value)
    if text.startswith(("=", "+", "-", "@", "\t", "\r")):
        return f"'{text}"
    return text


def _period_query(db: Session, date_from: date | None, date_to: date | None):
    query = db.query(Ticket).options(
        joinedload(Ticket.requester), joinedload(Ticket.technician), joinedload(Ticket.category),
        joinedload(Ticket.priority), joinedload(Ticket.status),
    ).filter(Ticket.deleted_at.is_(None))  # correctif #09 : exclure les tickets supprimés des rapports
    if date_from:
        query = query.filter(Ticket.created_at >= datetime.combine(date_from, time.min, tzinfo=timezone.utc))
    if date_to:
        query = query.filter(Ticket.created_at <= datetime.combine(date_to, time.max, tzinfo=timezone.utc))
    return query


def _compute_summary(db: Session, tickets: list[Ticket]) -> DashboardStatistics:
    """Calcule la synthèse chiffrée d'une liste de tickets. Partagée par
    `/summary` et `/export.pdf` pour que les deux affichent toujours les
    mêmes chiffres pour une même période."""
    total = len(tickets)
    resolved_tickets = [t for t in tickets if t.resolved_at is not None]
    responded_tickets = [t for t in tickets if t.first_response_at is not None]

    temps_resolution = (
        sum((t.resolved_at - t.created_at).total_seconds() for t in resolved_tickets) / len(resolved_tickets) / 3600
        if resolved_tickets else None
    )
    temps_reponse = (
        sum((t.first_response_at - t.created_at).total_seconds() for t in responded_tickets) / len(responded_tickets) / 60
        if responded_tickets else None
    )
    sla_depasse = sum(1 for t in tickets if compute_sla_progress(t).state == "depasse")

    ticket_ids = [t.id for t in tickets]
    ratings = (
        db.query(SatisfactionRating).filter(SatisfactionRating.ticket_id.in_(ticket_ids)).all() if ticket_ids else []
    )
    satisfaction_moyenne = round(sum(r.rating for r in ratings) / len(ratings), 2) if ratings else None

    return DashboardStatistics(
        total_tickets=total,
        tickets_ouverts=sum(1 for t in tickets if t.status.name == "Ouvert"),
        tickets_en_cours=sum(1 for t in tickets if t.status.name == "En cours"),
        tickets_en_attente=sum(1 for t in tickets if t.status.name == "En attente"),
        tickets_resolus=sum(1 for t in tickets if t.status.name == "Résolu"),
        tickets_fermes=sum(1 for t in tickets if t.status.name == "Fermé"),
        tickets_critiques=sum(1 for t in tickets if t.priority.name == "Critique"),
        tickets_sla_depasse=sla_depasse,
        temps_moyen_resolution_heures=round(temps_resolution, 1) if temps_resolution is not None else None,
        temps_moyen_premiere_reponse_minutes=round(temps_reponse, 1) if temps_reponse is not None else None,
        satisfaction_moyenne=satisfaction_moyenne,
    )


def _ticket_rows(tickets: list[Ticket]) -> list[tuple[str, str, str, str, str, str, str, str, str]]:
    """Lignes brutes (non échappées) de la table tickets, partagées par le
    CSV (qui les neutralise ensuite via _sanitize_csv_field) et le PDF (qui
    n'a pas besoin de cette neutralisation, un PDF n'étant pas un tableur)."""
    return [
        (
            t.reference,
            t.title,
            t.status.name,
            t.priority.name,
            t.category.name,
            t.requester.full_name,
            t.technician.full_name if t.technician else "",
            t.created_at.strftime("%Y-%m-%d %H:%M"),
            t.resolved_at.strftime("%Y-%m-%d %H:%M") if t.resolved_at else "",
        )
        for t in tickets
    ]


_TICKET_COLUMNS = [
    "Référence", "Titre", "Statut", "Priorité", "Catégorie", "Demandeur", "Technicien",
    "Date de création", "Date de résolution",
]

_SUMMARY_ROWS = [
    ("Total des tickets", "total_tickets", "{}"),
    ("Tickets résolus", "tickets_resolus", "{}"),
    ("Tickets ouverts", "tickets_ouverts", "{}"),
    ("Tickets critiques", "tickets_critiques", "{}"),
    ("SLA dépassés", "tickets_sla_depasse", "{}"),
    ("Temps moyen de résolution", "temps_moyen_resolution_heures", "{} h"),
    ("Temps moyen de 1ère réponse", "temps_moyen_premiere_reponse_minutes", "{} min"),
    ("Satisfaction moyenne", "satisfaction_moyenne", "{} / 5"),
]


@router.get("/summary", response_model=DashboardStatistics)
def report_summary(
    date_from: date | None = None,
    date_to: date | None = None,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db),
):
    """Synthèse chiffrée des tickets sur une période donnée (réservé Responsable IT / Administrateur)."""
    tickets = _period_query(db, date_from, date_to).all()
    return _compute_summary(db, tickets)


@router.get("/export.csv")
def export_csv(
    date_from: date | None = None,
    date_to: date | None = None,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db),
):
    """Exporte la liste des tickets de la période au format CSV (compatible Excel)."""
    tickets = _period_query(db, date_from, date_to).order_by(Ticket.created_at).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(_TICKET_COLUMNS)
    for row in _ticket_rows(tickets):
        writer.writerow([_sanitize_csv_field(value) for value in row])

    buffer.seek(0)
    filename = f"rapport_tickets_{date.today().isoformat()}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export.pdf")
def export_pdf(
    date_from: date | None = None,
    date_to: date | None = None,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db),
):
    """Exporte un rapport PDF (synthèse chiffrée + liste des tickets) de la période."""
    tickets = _period_query(db, date_from, date_to).order_by(Ticket.created_at).all()
    summary = _compute_summary(db, tickets)

    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    normal_style = styles["Normal"]
    cell_style = ParagraphStyle("cell", parent=normal_style, fontSize=8, leading=10)
    header_cell_style = ParagraphStyle("header_cell", parent=cell_style, textColor=colors.white, fontName="Helvetica-Bold")

    period_label = f"{date_from.isoformat() if date_from else '…'} → {date_to.isoformat() if date_to else '…'}"
    generated_label = datetime.now(timezone.utc).strftime("%d/%m/%Y à %H:%M UTC")

    elements = [
        Paragraph("Rapport de tickets — IT Support", title_style),
        Paragraph(f"Période : {period_label} · Généré le {generated_label}", normal_style),
        Spacer(1, 0.6 * cm),
    ]

    # --- Synthèse chiffrée ---
    summary_data = [
        [label, template.format(getattr(summary, field)) if getattr(summary, field) is not None else "—"]
        for label, field, template in _SUMMARY_ROWS
    ]
    summary_table = Table(summary_data, colWidths=[7 * cm, 5 * cm])
    summary_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E4EE")),
    ]))
    elements += [summary_table, Spacer(1, 1 * cm)]

    # --- Liste des tickets ---
    if tickets:
        header_row = [Paragraph(col, header_cell_style) for col in _TICKET_COLUMNS]
        data_rows = [
            [Paragraph(str(value), cell_style) for value in row]
            for row in _ticket_rows(tickets)
        ]
        ticket_table = Table(
            [header_row, *data_rows],
            colWidths=[2.9 * cm, 5 * cm, 2.2 * cm, 2.2 * cm, 2.8 * cm, 3.2 * cm, 3.2 * cm, 3 * cm, 3 * cm],
            repeatRows=1,
        )
        ticket_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4338CA")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F6FA")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E4EE")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(ticket_table)
    else:
        elements.append(Paragraph("Aucun ticket sur cette période.", normal_style))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        leftMargin=1.5 * cm, rightMargin=1.5 * cm, topMargin=1.5 * cm, bottomMargin=1.5 * cm,
    )
    doc.build(elements)
    buffer.seek(0)

    filename = f"rapport_tickets_{date.today().isoformat()}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
