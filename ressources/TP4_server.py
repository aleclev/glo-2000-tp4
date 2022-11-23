"""\
GLO-2000 Travail pratique 4 - Serveur
Noms et numéros étudiants:
- Alec Lévesque 111 269 901
- Joey Fournier 111 267 602
- Zyed El Hidri 111 159 762
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
import re
import pathlib

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
        try:
            self._server_socket = self._make_socket()
            self._client_socs = []
            self._logged_users = {}

            path = pathlib.Path.cwd() / gloutils.SERVER_DATA_DIR / gloutils.SERVER_LOST_DIR
            path.mkdir(parents=True, exist_ok=True)
        except:
            sys.exit(-1)

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

        self._client_socs.remove(client_soc)
        
        if id(client_soc) in self._logged_users:
            self._logged_users.pop(id(client_soc))
        
        client_soc.close()

    def _create_account(self, client_soc: socket.socket,
                        payload: gloutils.AuthPayload
                        ) -> gloutils.GloMessage:
        """
        Crée un compte à partir des données du payload.

        Si les identifiants sont valides, créee le dossier de l'utilisateur,
        associe le socket au nouvel l'utilisateur et retourne un succès,
        sinon retourne un message d'erreur.
        """
        username = payload["username"]
        password = payload["password"]

        username_pattern = re.compile(r"^[\w_\.-]+")
        password_pattern = re.compile(r"^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9]).{10,}$")

        if (not username_pattern.fullmatch(username)) or username.lower() == "lost":
            return self._get_error_message("Le nom d'utilisateur doit être composé de caractères alpha numériques et ., - ou _.")

        if not password_pattern.fullmatch(password):
            return self._get_error_message("Le mot de passe doit contenir une lettre majuscule et une lettre minuscule. Doit aussi contenir au moins 10 caractères.")
        
        #create folder if not exists
        path = pathlib.Path.cwd() / gloutils.SERVER_DATA_DIR

        for x in path.iterdir(): 
            if x.is_dir() and x.name == username.lower():
                return self._get_error_message("Le nom d'utilisateur est déjà pris.")
        
        path = path / username.lower()

        path.mkdir(parents=True, exist_ok=True)

        path = path / gloutils.PASSWORD_FILENAME

        path.touch(exist_ok=True)

        hasher = hashlib.sha3_512()

        hasher.update(password.encode("utf-8"))
        encoded_pass = hasher.hexdigest()

        path.write_text(encoded_pass)
        self._logged_users[id(client_soc)] = username.lower()

        header = gloutils.Headers.OK
        return gloutils.GloMessage(header=header, payload=None)
    
    def _get_error_message(self, message: str):
        payload = gloutils.ErrorPayload(error_message=message)
        header = gloutils.Headers.ERROR
        message = gloutils.GloMessage(payload=payload, header=header)
        return message

    def _login(self, client_soc: socket.socket, payload: gloutils.AuthPayload
               ) -> gloutils.GloMessage:
        """
        Vérifie que les données fournies correspondent à un compte existant.

        Si les identifiants sont valides, associe le socket à l'utilisateur et
        retourne un succès, sinon retourne un message d'erreur.
        """

        path = pathlib.Path.cwd() / gloutils.SERVER_DATA_DIR
        
        username = payload["username"]
        password = payload["password"]

        stored_password = None

        for x in path.iterdir(): 
            if x.is_dir() and x.name == username.lower():
                with open(path / username.lower() / gloutils.PASSWORD_FILENAME, 'r') as password_file:
                    stored_password = password_file.read()
        
        if stored_password == None:
            return self._get_error_message("L'utilisateur n'existe pas.")
        
        hasher = hashlib.sha3_512()
        hasher.update(password.encode("utf-8"))
        digest = hasher.hexdigest()

        if hmac.compare_digest(digest, stored_password):
            self._logged_users[id(client_soc)] = username.lower()
            header = gloutils.Headers.OK
            return gloutils.GloMessage(payload=None, header=header)
        else:
            return self._get_error_message("Mot de passe incorrecte.")
        

    def _logout(self, client_soc: socket.socket) -> None:
        """Déconnecte un utilisateur."""

        if id(client_soc) not in self._logged_users:
            return self._get_error_message("Aucun utilisateur connecté")
        else:
            self._logged_users.pop(id(client_soc))
            return gloutils.GloMessage(header=gloutils.Headers.OK, payload=None)

    def _get_email_list(self, client_soc: socket.socket
                        ) -> gloutils.GloMessage:
        """
        Récupère la liste des courriels de l'utilisateur associé au socket.
        Les éléments de la liste sont construits à l'aide du gabarit
        SUBJECT_DISPLAY et sont ordonnés du plus récent au plus ancien.

        Une absence de courriel n'est pas une erreur, mais une liste vide.
        """

        try:
            username = self._logged_users[id(client_soc)]
        except:
            return self._get_error_message("Utilisateur invalide")
        
        email_list = self._get_client_emails_as_json_list(username=username)

        subject_display_list = []

        for i in range(0, len(email_list)):
            subject = email_list[i]["subject"]
            sender = email_list[i]["sender"]
            date = email_list[i]["date"]
            subject_display_list.append(gloutils.SUBJECT_DISPLAY.format(number=i+1, subject=subject, sender=sender, date=date))

        header = gloutils.Headers.OK
        payload = gloutils.EmailListPayload(email_list=json.dumps(subject_display_list))
        message = gloutils.GloMessage(header=header, payload=payload)

        return message

    def _get_client_emails_as_json_list(self, username: str) -> list:
        path = pathlib.Path.cwd() / gloutils.SERVER_DATA_DIR / username.lower()
        email_file_list = [f for f in path.iterdir() if f.name != gloutils.PASSWORD_FILENAME]
        email_list = []

        for file in email_file_list:
            with open(file, 'r') as email_file:
                email_list.append(json.loads(email_file.read()))
        
        email_list.reverse()
        return email_list

    def _get_email(self, client_soc: socket.socket,
                   payload: gloutils.EmailChoicePayload
                   ) -> gloutils.GloMessage:
        """
        Récupère le contenu de l'email dans le dossier de l'utilisateur associé
        au socket.
        """

        try:
            username = self._logged_users[id(client_soc)]
        except:
            return self._get_error_message("Invalid socket.")

        email_list = self._get_client_emails_as_json_list(username=username)

        index = int(payload["choice"]) - 1

        email_to_send = email_list[index]

        payload = gloutils.EmailContentPayload(
            sender=email_to_send["sender"],
            destination=email_to_send["destination"],
            subject=email_to_send["subject"],
            date=email_to_send["date"],
            content=email_to_send["content"]
        )

        header = gloutils.Headers.OK

        return gloutils.GloMessage(payload=payload, header=header)

    def _get_stats(self, client_soc: socket.socket) -> gloutils.GloMessage:
        """
        Récupère le nombre de courriels et la taille du dossier et des fichiers
        de l'utilisateur associé au socket.
        """

        try:
            username = self._logged_users[id(client_soc)]
        except:
            return self._get_error_message("Socket has no associated user.")

        path = pathlib.Path.cwd() / gloutils.SERVER_DATA_DIR / username.lower()

        number_of_mail = self._get_number_of_mail_for_user(username)
        size = sum(file.stat().st_size for file in path.rglob('*'))

        header = gloutils.Headers.OK
        payload = gloutils.StatsPayload(count=number_of_mail, size=size)

        return gloutils.GloMessage(header=header, payload=payload)

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
        sender = payload["sender"]
        destination = payload["destination"]
        subject = payload["subject"]
        date = payload["date"]
        content = payload["content"]

        if destination.endswith("@glo2000.ca"):
            #interne
            found_user = None
            path = pathlib.Path.cwd() / gloutils.SERVER_DATA_DIR
            for x in path.iterdir(): 
                if x.is_dir() and x.name + '@glo2000.ca' == destination.lower():
                    found_user = x.name
                    break

            if not found_user:
                found_user = gloutils.SERVER_LOST_DIR
            

            if found_user:
                new_file_number = self._get_number_of_mail_for_user(found_user) + 1
                path = path / found_user.lower() / str(new_file_number)
                path.touch()
                path.write_text(json.dumps(payload))
                if found_user == gloutils.SERVER_LOST_DIR:
                    return self._get_error_message("Le destinataire n'existe pas.")
                return gloutils.GloMessage(header=gloutils.Headers.OK, payload=None)

        else:
            #extrerne
            message = EmailMessage()
            message["From"] = sender
            message["To"] = destination
            message["Subject"] = subject
            message.set_content(content)

            try:
                with smtplib.SMTP(host="smtp.ulaval.ca", timeout=10) as connection:
                    connection.send_message(message)
                    return gloutils.GloMessage(header=gloutils.Headers.OK, payload=None)
            except:
                return self._get_error_message("Échec de l'envoie du courriel.")
    
    def _get_number_of_mail_for_user(self, username: str) -> int:
        path = pathlib.Path.cwd() / gloutils.SERVER_DATA_DIR / username.lower()
        return len([f for f in path.iterdir() if f.name != gloutils.PASSWORD_FILENAME])

    def _dispatch(self, message: gloutils.GloMessage, socket: glosocket.socket):
        
        response = None

        if message["header"] == gloutils.Headers.AUTH_LOGIN:
            response = self._login(socket, message["payload"])
        elif message["header"] == gloutils.Headers.AUTH_LOGOUT:
            return self._logout(socket)
        elif message["header"] == gloutils.Headers.AUTH_REGISTER:
            response = self._create_account(socket, message["payload"])
        elif message["header"] == gloutils.Headers.EMAIL_SENDING:
            response = self._send_email(message["payload"])
        elif message["header"] == gloutils.Headers.BYE:
            return self._remove_client(socket)
        elif message["header"] == gloutils.Headers.STATS_REQUEST:
            response = self._get_stats(client_soc=socket)
        elif message["header"] == gloutils.Headers.INBOX_READING_REQUEST:
            response = self._get_email_list(socket)      
        elif message["header"] == gloutils.Headers.INBOX_READING_CHOICE:
            response = self._get_email(socket, message["payload"])

        raw = json.dumps(response)
        glosocket.send_msg(socket, message=raw)

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
