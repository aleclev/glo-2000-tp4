"""\
Module fournissant les constantes, énumérations,
protocoles et gabarits à utiliser pour le TP4.
"""
import enum
from typing import TypedDict, Union
import datetime

APP_PORT = 5321
SERVER_DATA_DIR = "glo_server_data"
SERVER_LOST_DIR = "LOST"
SERVER_DOMAIN = "glo2000.ca"
SMTP_SERVER = "smtp.ulaval.ca"
PASSWORD_FILENAME = "pass"  # nosec:B105

CLIENT_AUTH_CHOICE = """Menu de connexion
1. Créer un compte
2. Se connecter
3. Quitter"""
CLIENT_USE_CHOICE = """Menu principal
1. Consultation de courriels
2. Envoi de courriels
3. Statistiques
4. Se déconnecter"""

SUBJECT_DISPLAY = "#{number} {sender} - {subject} {date}"

EMAIL_DISPLAY = """De : {sender}
À : {to}
Sujet : {subject}
Date : {date}
----------------------------------------
{body}
"""

STATS_DISPLAY = """Nombre de messages : {count}
Taille du dossier : {size} octets"""


class Headers(enum.IntEnum):
    """
    Entête à utiliser
    """
    OK = enum.auto()
    ERROR = enum.auto()
    BYE = enum.auto()

    AUTH_REGISTER = enum.auto()
    AUTH_LOGIN = enum.auto()
    AUTH_LOGOUT = enum.auto()

    INBOX_READING_REQUEST = enum.auto()
    INBOX_READING_CHOICE = enum.auto()

    EMAIL_SENDING = enum.auto()

    STATS_REQUEST = enum.auto()


class ErrorPayload(TypedDict, total=True):
    """Payload pour les messages d'erreurs."""
    error_message: str


class AuthPayload(TypedDict, total=True):
    """Payload pour les requêtes LOGIN/REGISTER."""
    username: str
    password: str


class EmailContentPayload(TypedDict, total=True):
    """Payload pour les transferts de courriels."""
    sender: str
    destination: str
    subject: str
    date: str
    content: str


class EmailListPayload(TypedDict, total=True):
    """Payload pour les consulation de courriel."""
    email_list: "list[str]"


class EmailChoicePayload(TypedDict, total=True):
    """Payload pour le choix du courriel à consulter."""
    choice: int


class StatsPayload(TypedDict, total=True):
    """Payload pour les statistiques."""
    count: int
    size: int


class GloMessage(TypedDict, total=False):
    """
    Classe à utiliser pour générer des messages.

    Les classes *Payload correspondent à des entêtes spécifiques
    certaines entêtes n'ont pas besoin de payload.
    """
    header: Headers
    payload: Union[ErrorPayload, AuthPayload, EmailContentPayload,
                   EmailListPayload, EmailChoicePayload, StatsPayload]


def get_current_utc_time() -> str:
    """Récupère l'heure courante au fuseau UTC et la formatte en string."""
    current_time = datetime.datetime.now(datetime.timezone.utc)
    return current_time.strftime("%a, %d %b %Y %H:%M:%S %z")
