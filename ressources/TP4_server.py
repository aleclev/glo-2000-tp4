"""\
GLO-2000 Travail pratique 4 - Serveur
Noms et numéros étudiants:
-
-
-
"""

from email.message import EmailMessage
import hashlib
import hmac
import json
import os
import select
import smtplib
import socket
import sys

import glosocket
import gloutils


class Server:
    """Serveur mail @glo2000.ca."""

    def __init__(self) -> None:
        """
        Prépare le socket du serveur `_server_socket`
        et le met en mode écoute.

        Prépare les attributs suivants:
        - `_client_socs` une liste des sockets clients.
        - `_logged_users` un dictionnaire associant chaque
            socket client à un nom d'utilisateur.

        S'assure que les dossiers de données du serveur existent.
        """
        self._server_socket = self._make_socket()
        self._client_socs = []
        self._logged_users = []

    def _make_socket(self):
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        soc.bind(("127.0.0.1", gloutils.APP_PORT))
        soc.listen(10)
        return soc

    def cleanup(self) -> None:
        """Ferme toutes les connexions résiduelles."""
        for client_soc in self._client_socs:
            client_soc.close()
        self._server_socket.close()

    def _accept_client(self) -> None:
        """Accepte un nouveau client."""
        newsocket, _ = self._server_socket.accept()
        
        self._client_socs.append(newsocket)

    def _remove_client(self, client_soc: socket.socket) -> None:
        """Retire le client des structures de données et ferme sa connexion."""

    def _create_account(self, client_soc: socket.socket,
                        payload: gloutils.AuthPayload
                        ) -> gloutils.GloMessage:
        """
        Crée un compte à partir des données du payload.

        Si les identifiants sont valides, créee le dossier de l'utilisateur,
        associe le socket au nouvel l'utilisateur et retourne un succès,
        sinon retourne un message d'erreur.
        """
        return gloutils.GloMessage()

    def _login(self, client_soc: socket.socket, payload: gloutils.AuthPayload
               ) -> gloutils.GloMessage:
        """
        Vérifie que les données fournies correspondent à un compte existant.

        Si les identifiants sont valides, associe le socket à l'utilisateur et
        retourne un succès, sinon retourne un message d'erreur.
        """
        return gloutils.GloMessage()

    def _logout(self, client_soc: socket.socket) -> None:
        """Déconnecte un utilisateur."""

    def _get_email_list(self, client_soc: socket.socket
                        ) -> gloutils.GloMessage:
        """
        Récupère la liste des courriels de l'utilisateur associé au socket.
        Les éléments de la liste sont construits à l'aide du gabarit
        SUBJECT_DISPLAY et sont ordonnés du plus récent au plus ancien.

        Une absence de courriel n'est pas une erreur, mais une liste vide.
        """
        return gloutils.GloMessage()

    def _get_email(self, client_soc: socket.socket,
                   payload: gloutils.EmailChoicePayload
                   ) -> gloutils.GloMessage:
        """
        Récupère le contenu de l'email dans le dossier de l'utilisateur associé
        au socket.
        """
        return gloutils.GloMessage()

    def _get_stats(self, client_soc: socket.socket) -> gloutils.GloMessage:
        """
        Récupère le nombre de courriels et la taille du dossier et des fichiers
        de l'utilisateur associé au socket.
        """
        return gloutils.GloMessage()

    def _send_email(self, payload: gloutils.EmailContentPayload
                    ) -> gloutils.GloMessage:
        """
        Détermine si l'envoi est interne ou externe et:
        - Si l'envoi est interne, écris le message tel quel dans le dossier
        du destinataire.
        - Si le destinataire n'existe pas, place le message dans le dossier
        SERVER_LOST_DIR et considère l'envoi comme un échec.
        - Si le destinataire est externe, transforme le message en
        EmailMessage et utilise le serveur SMTP pour le relayer.

        Retourne un messange indiquant le succès ou l'échec de l'opération.
        """
        return gloutils.GloMessage()

    def _dispatch(self, message: gloutils.GloMessage, socket: glosocket.socket):
        if message.header == gloutils.Headers.AUTH_LOGIN:
            pass
        if message.header == gloutils.Headers.AUTH_LOGOUT:
            pass
        if message.header == gloutils.Headers.AUTH_REGISTER:
            pass
        if message.header == gloutils.Headers.EMAIL_SENDING:
            pass
        if message.header == gloutils.Headers.ERROR:
            pass
        if message.header == gloutils.Headers.INBOX_READING_CHOICE:
            pass

    def run(self):
        """Point d'entrée du serveur."""
        while True:
            # Select readable sockets
            result = select.select([self._server_socket] + self._client_socs, [], [])
            readable_sockets = result[0]
            for waiter in readable_sockets:
                if waiter == self._server_socket:
                    self._accept_client()
                else:
                    raw = glosocket.recv_msg(waiter)
                    message = json.loads(raw)
                    self._dispatch(message, waiter)


def _main() -> int:
    server = Server()
    try:
        server.run()
    except KeyboardInterrupt:
        server.cleanup()
    return 0


if __name__ == '__main__':
    sys.exit(_main())
