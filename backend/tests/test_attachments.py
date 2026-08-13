"""Tests des pièces jointes : validation du contenu réel (magic bytes), stockage
sécurisé et autorisation du téléchargement (correctif #05)."""
import os
import uuid as uuid_module

import pytest

from app.config import settings
from app.models.attachment import Attachment
from app.models.category import Category
from app.models.priority import Priority
from tests.conftest import auth_headers, create_user


@pytest.fixture(autouse=True)
def _cleanup_uploaded_files():
    """Supprime les fichiers physiques créés par chaque test dans le répertoire
    d'upload (répertoire déjà exclu de Git — voir .gitignore — mais autant ne
    pas laisser de fichiers de test s'accumuler sur le disque local)."""
    upload_dir = os.path.abspath(settings.upload_dir)
    before = set(os.listdir(upload_dir)) if os.path.isdir(upload_dir) else set()
    yield
    if os.path.isdir(upload_dir):
        for name in set(os.listdir(upload_dir)) - before:
            try:
                os.remove(os.path.join(upload_dir, name))
            except OSError:
                pass


# --- Contenus minimaux, réels et volontairement inoffensifs, pour chaque cas testé ---
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64             # signature PNG valide
PDF_BYTES = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n" + b"\x00" * 64   # signature PDF valide
HTML_BYTES = b"<html><body>Ceci n'est pas un PDF.</body></html>" * 5
# Contenu texte quelconque, sans rapport avec une image : suffit à faire échouer
# la détection de signature binaire (filetype.guess), sans utiliser de motif
# évocateur d'un script malveillant.
NOT_AN_IMAGE_BYTES = b"Ceci est un simple fichier texte, pas une image. " * 10
GARBAGE_BYTES = bytes(range(1, 256)) * 2  # octets quelconques, aucune signature de format connu


def _ticket_payload(db_session):
    category = db_session.query(Category).first()
    priority = db_session.query(Priority).filter_by(name="Normale").first()
    return {
        "title": "Impossible d'ouvrir le fichier joint",
        "description": "Voir la pièce jointe.",
        "category_id": category.id,
        "priority_id": priority.id,
    }


def _create_ticket(client, db_session, requester_email):
    return client.post(
        "/api/tickets", json=_ticket_payload(db_session), headers=auth_headers(client, requester_email)
    ).json()


def _upload(client, ticket_id, headers, filename, content, content_type):
    return client.post(
        f"/api/tickets/{ticket_id}/attachments",
        files={"file": (filename, content, content_type)},
        headers=headers,
    )


# --- Test 1 : fichier valide, extension correcte -> accepté ---

def test_valid_file_upload_accepted(client, db_session):
    create_user(db_session, "up1@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "up1@test.example")

    response = _upload(
        client, ticket["id"], auth_headers(client, "up1@test.example"), "photo.png", PNG_BYTES, "image/png"
    )
    assert response.status_code == 201
    assert response.json()["file_name"] == "photo.png"


def test_valid_pdf_upload_accepted(client, db_session):
    create_user(db_session, "up1b@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "up1b@test.example")

    response = _upload(
        client, ticket["id"], auth_headers(client, "up1b@test.example"), "rapport.pdf", PDF_BYTES, "application/pdf"
    )
    assert response.status_code == 201


# --- Test 2 : extension autorisée mais contenu falsifié -> refusé ---

def test_pdf_extension_with_html_content_rejected(client, db_session):
    """document.pdf contenant réellement du HTML -> REFUS."""
    create_user(db_session, "up2@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "up2@test.example")

    response = _upload(
        client, ticket["id"], auth_headers(client, "up2@test.example"), "document.pdf", HTML_BYTES, "application/pdf"
    )
    assert response.status_code == 400


def test_jpg_extension_with_non_image_content_rejected(client, db_session):
    """image.jpg dont le contenu réel n'est pas une image -> REFUS (signature non reconnue)."""
    create_user(db_session, "up3@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "up3@test.example")

    response = _upload(
        client, ticket["id"], auth_headers(client, "up3@test.example"), "image.jpg", NOT_AN_IMAGE_BYTES, "image/jpeg"
    )
    assert response.status_code == 400


# --- Test 3 : Content-Type falsifié -> refusé ---

def test_falsified_content_type_rejected(client, db_session):
    """Fichier .png réel mais Content-Type déclaré comme application/pdf : incohérence extension/MIME déclaré."""
    create_user(db_session, "up5@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "up5@test.example")

    response = _upload(
        client, ticket["id"], auth_headers(client, "up5@test.example"), "photo.png", PNG_BYTES, "application/pdf"
    )
    assert response.status_code == 400


# --- Test 4 : fichier trop volumineux -> refusé ---

def test_oversized_file_rejected(client, db_session, monkeypatch):
    create_user(db_session, "up6@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "up6@test.example")

    monkeypatch.setattr("app.utils.files.settings.max_upload_size_mb", 1)  # limite abaissée à 1 Mo pour le test
    oversized_content = PNG_BYTES + b"\x00" * (2 * 1024 * 1024)  # ~2 Mo > 1 Mo

    response = _upload(
        client, ticket["id"], auth_headers(client, "up6@test.example"), "gros_fichier.png", oversized_content, "image/png"
    )
    assert response.status_code == 400
    assert "taille maximale" in response.json()["detail"]


# --- Test 5 : extension interdite -> refusée ---

def test_forbidden_extension_rejected(client, db_session):
    create_user(db_session, "up7@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "up7@test.example")

    response = _upload(
        client, ticket["id"], auth_headers(client, "up7@test.example"),
        "notes.bat", b"contenu quelconque", "application/octet-stream",
    )
    assert response.status_code == 400


# --- Test 6 : fichier vide -> refusé ---

def test_empty_file_rejected(client, db_session):
    create_user(db_session, "up8@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "up8@test.example")

    response = _upload(client, ticket["id"], auth_headers(client, "up8@test.example"), "vide.txt", b"", "text/plain")
    assert response.status_code == 400


# --- Test 7 : fichier corrompu -> refusé ---

def test_corrupted_file_rejected(client, db_session):
    """Contenu totalement incohérent, sans signature reconnaissable, déclaré comme PDF."""
    create_user(db_session, "up9@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "up9@test.example")

    response = _upload(
        client, ticket["id"], auth_headers(client, "up9@test.example"), "rapport.pdf", GARBAGE_BYTES, "application/pdf"
    )
    assert response.status_code == 400


# --- Test 8 : nom de fichier avec tentative de path traversal ---

def test_path_traversal_filename_does_not_escape_upload_dir(client, db_session):
    create_user(db_session, "up10@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "up10@test.example")

    response = _upload(
        client, ticket["id"], auth_headers(client, "up10@test.example"),
        "../../malicious.txt", b"contenu texte inoffensif", "text/plain",
    )
    assert response.status_code == 201

    attachment = db_session.query(Attachment).order_by(Attachment.id.desc()).first()
    upload_dir = os.path.abspath(settings.upload_dir)
    stored_path = os.path.abspath(attachment.file_path)

    # Le fichier physique est strictement à l'intérieur du répertoire d'upload.
    assert os.path.commonpath([upload_dir, stored_path]) == upload_dir
    # Le nom affiché ne conserve aucune séquence de traversée de répertoire.
    assert ".." not in attachment.file_name
    assert "/" not in attachment.file_name and "\\" not in attachment.file_name
    # Aucun fichier n'a été écrit en dehors du répertoire prévu.
    escaped_path = os.path.abspath(os.path.join(upload_dir, "..", "..", "malicious.txt"))
    assert not os.path.exists(escaped_path)


# --- Test 9 : utilisateur sans accès au ticket -> téléchargement refusé ---

def test_download_forbidden_without_ticket_access(client, db_session):
    create_user(db_session, "proprio11@test.example", "Utilisateur")
    create_user(db_session, "intrus11@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "proprio11@test.example")
    upload_resp = _upload(
        client, ticket["id"], auth_headers(client, "proprio11@test.example"), "photo.png", PNG_BYTES, "image/png"
    )
    attachment_id = upload_resp.json()["id"]

    response = client.get(
        f"/api/attachments/{attachment_id}/download", headers=auth_headers(client, "intrus11@test.example")
    )
    assert response.status_code == 403


# --- Test 10 : utilisateur autorisé -> téléchargement fonctionnel ---

def test_download_allowed_for_authorized_user(client, db_session):
    create_user(db_session, "proprio12@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "proprio12@test.example")
    upload_resp = _upload(
        client, ticket["id"], auth_headers(client, "proprio12@test.example"), "photo.png", PNG_BYTES, "image/png"
    )
    attachment_id = upload_resp.json()["id"]

    response = client.get(
        f"/api/attachments/{attachment_id}/download", headers=auth_headers(client, "proprio12@test.example")
    )
    assert response.status_code == 200
    assert response.content == PNG_BYTES


# --- Amélioration A : en-tête X-Content-Type-Options: nosniff ---

def test_download_response_has_nosniff_header(client, db_session):
    """GET /api/attachments/{id}/download doit renvoyer X-Content-Type-Options: nosniff,
    en complément de Content-Disposition: attachment déjà en place."""
    create_user(db_session, "nosniff1@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "nosniff1@test.example")
    upload_resp = _upload(
        client, ticket["id"], auth_headers(client, "nosniff1@test.example"), "photo.png", PNG_BYTES, "image/png"
    )
    attachment_id = upload_resp.json()["id"]

    response = client.get(
        f"/api/attachments/{attachment_id}/download", headers=auth_headers(client, "nosniff1@test.example")
    )
    assert response.status_code == 200
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("content-disposition", "").startswith("attachment")


def test_normal_responses_still_work_with_nosniff_header(client, db_session):
    """Le nouvel en-tête global ne doit casser aucune réponse normale de
    l'application : santé, connexion et création de ticket restent
    fonctionnelles et portent elles aussi le nouvel en-tête."""
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.headers.get("x-content-type-options") == "nosniff"

    create_user(db_session, "nosniff2@test.example", "Utilisateur")
    login = client.post("/api/auth/login", json={"email": "nosniff2@test.example", "password": "MotDePasse123!"})
    assert login.status_code == 200
    assert "access_token" in login.json()
    assert login.headers.get("x-content-type-options") == "nosniff"

    ticket = _create_ticket(client, db_session, "nosniff2@test.example")
    assert ticket["reference"].startswith("TCK-")


def test_download_manipulated_id_does_not_leak_other_ticket_attachment(client, db_session):
    """Un utilisateur ne peut pas récupérer la pièce jointe d'un autre ticket en devinant son ID."""
    create_user(db_session, "proprio-a@test.example", "Utilisateur")
    create_user(db_session, "proprio-b@test.example", "Utilisateur")
    ticket_a = _create_ticket(client, db_session, "proprio-a@test.example")
    upload_resp = _upload(
        client, ticket_a["id"], auth_headers(client, "proprio-a@test.example"), "photo.png", PNG_BYTES, "image/png"
    )
    attachment_id = upload_resp.json()["id"]

    response = client.get(
        f"/api/attachments/{attachment_id}/download", headers=auth_headers(client, "proprio-b@test.example")
    )
    assert response.status_code == 403
    assert PNG_BYTES not in response.content


# --- Test 11 : pas d'écrasement d'un fichier existant en cas de collision de nom ---

def test_no_overwrite_on_uuid_collision(client, db_session, monkeypatch):
    create_user(db_session, "up13@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "up13@test.example")

    upload_dir = os.path.abspath(settings.upload_dir)
    os.makedirs(upload_dir, exist_ok=True)
    colliding_uuid = uuid_module.uuid4()
    existing_path = os.path.join(upload_dir, f"{colliding_uuid.hex}.txt")
    original_content = b"CONTENU ORIGINAL A NE JAMAIS ECRASER"
    with open(existing_path, "wb") as f:
        f.write(original_content)

    # Le premier appel à uuid4() rejoue volontairement une collision ; le second
    # renvoie un UUID différent, comme le ferait uuid4() en conditions réelles.
    sequence = iter([colliding_uuid, uuid_module.uuid4()])
    monkeypatch.setattr("app.utils.files.uuid.uuid4", lambda: next(sequence))

    try:
        response = _upload(
            client, ticket["id"], auth_headers(client, "up13@test.example"), "nouveau.txt", b"nouveau contenu", "text/plain"
        )
        assert response.status_code == 201

        with open(existing_path, "rb") as f:
            assert f.read() == original_content  # le fichier préexistant n'a pas été touché

        attachment = db_session.query(Attachment).order_by(Attachment.id.desc()).first()
        assert os.path.abspath(attachment.file_path) != os.path.abspath(existing_path)
    finally:
        os.remove(existing_path)
