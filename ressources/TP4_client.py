"""\
GLO-2000 Travail pratique 4 - Client
Noms et numéros étudiants:
- Alec Lévesque 111 269 901
- Joey Fournier 111 267 602
- Zyed El Hidri 111 159 762
"""

import argparse
import getpass
import json
import socket
import sys

import glosocket
import gloutils


class Client:
    """Client pour le serveur mail @glo2000.ca."""

    def _get_username_password(self) -> "(str, str)":
        username = input("Veuillez entrer votre nom d'utilisateur...")
        password = getpass.getpass("Veuillez entrer votre mot de passe...")

        return username, password

    def _send_server_message(self, payload: gloutils.GloMessage):
        raw = json.dumps(payload)
        glosocket.send_msg(self._socket, raw)

    def _receive_server_message(self) -> gloutils.GloMessage:
        raw = glosocket.recv_msg(self._socket)
        return json.loads(raw)
    
    def _exchange_to_server(self, message: gloutils.GloMessage):
        self._send_server_message(payload=message)
        return self._receive_server_message()


    def __init__(self, destination: str) -> None:
        """
        Prépare et connecte le socket du client `_socket`.

        Prépare un attribut `_username` pour stocker le nom d'utilisateur
        courant. Laissé vide quand l'utilisateur n'est pas connecté.
        """
        try:
            self._username = None

            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((destination, gloutils.APP_PORT))
        except:
            sys.exit(-1)

    def _message_contains_error(self, message: gloutils.GloMessage) -> bool:
        if message["header"] == gloutils.Headers.ERROR:
            print(message["payload"]["error_message"])
            return True
        else:
            return False
    
    def _message_is_ok(self, message: gloutils.GloMessage) -> bool:
        return message["header"] == gloutils.Headers.OK

    def _register(self) -> None:
        """
        Demande un nom d'utilisateur et un mot de passe et les transmet au
        serveur avec l'entête `AUTH_REGISTER`.

        Si la création du compte s'est effectuée avec succès, l'attribut
        `_username` est mis à jour, sinon l'erreur est affichée.
        """
        username, password = self._get_username_password()

        payload = gloutils.AuthPayload(username=username, password=password)
        message = gloutils.GloMessage(header=gloutils.Headers.AUTH_REGISTER, payload=payload)

        message_rec = self._exchange_to_server(message=message)

        if self._message_contains_error(message_rec):
            return
        elif self._message_is_ok(message_rec):
            self._username = username
            print("Connexion réussie !")

    def _login(self) -> None:
        """
        Demande un nom d'utilisateur et un mot de passe et les transmet au
        serveur avec l'entête `AUTH_LOGIN`.

        Si la connexion est effectuée avec succès, l'attribut `_username`
        est mis à jour, sinon l'erreur est affichée.
        """
        username, password = self._get_username_password()

        payload = gloutils.AuthPayload(username=username, password=password)
        header = gloutils.Headers.AUTH_LOGIN
        message = gloutils.GloMessage(payload=payload, header=header)

        message_rec = self._exchange_to_server(message)

        if self._message_contains_error(message_rec):
            return
        elif self._message_is_ok(message_rec):
            self._username = username
        else:
            print("Erreur dans le traitement du message reçu.")



    def _quit(self) -> None:
        """
        Préviens le serveur de la déconnexion avec l'entête `BYE` et ferme le
        socket du client.
        """

        message = gloutils.GloMessage(payload=None, header=gloutils.Headers.BYE)
        self._send_server_message(message)
        print("Déconnexion. Au revoir !")

    def _read_email(self) -> None:
        """
        Demande au serveur la liste de ses courriels avec l'entête
        `INBOX_READING_REQUEST`.

        Affiche la liste des courriels puis transmet le choix de l'utilisateur
        avec l'entête `INBOX_READING_CHOICE`.

        Affiche le courriel à l'aide du gabarit `EMAIL_DISPLAY`.

        S'il n'y a pas de courriel à lire, l'utilisateur est averti avant de
        retourner au menu principal.
        """
        message = gloutils.GloMessage(header=gloutils.Headers.INBOX_READING_REQUEST, payload=None)
        message_rec = self._exchange_to_server(message)

        if self._message_contains_error(message_rec):
            return

        email_subjects_string = message_rec["payload"]["email_list"]

        email_subjects = json.loads(email_subjects_string)

        if len(email_subjects) == 0:
            print("Aucun email dans la boîte. Retour au menu principal.")
            return

        else:
            for subject in email_subjects:
                print(subject)
        
        choice = self._get_input_number_between(1, len(email_subjects))

        payload = gloutils.EmailChoicePayload(choice=choice)
        message = gloutils.GloMessage(header=gloutils.Headers.INBOX_READING_CHOICE, payload=payload)

        message_rec = self._exchange_to_server(message=message)

        if self._message_contains_error(message_rec):
            return

        payload = message_rec["payload"]
        sender = payload["sender"]
        to = payload["destination"]
        subject = payload["subject"] 
        date = payload["date"]
        body = payload["content"]

        print(gloutils.EMAIL_DISPLAY.format(sender=sender, to=to, subject=subject, date=date, body=body))


    def _send_email(self) -> None:
        """
        Demande à l'utilisateur respectivement:
        - l'adresse email du destinataire,
        - le sujet du message,
        - le corps du message.

        La saisie du corps se termine par un point seul sur une ligne.

        Transmet ces informations avec l'entête `EMAIL_SENDING`.
        """

        email = input("Veuillez entrer l'adresse courriel du destintaire:")
        subject = input("Veuillez entrer le sujet du message:")
        
        print("Veuillez tapper le corps du message. Pour arrêter, simplement insérer un point solitaire (.) dans la console:")
        body = ""

        while True:
            line = input()
            if line == ".":
                break
            else:
                body += line + "\n"
        
        payload = gloutils.EmailContentPayload(
            sender=self._username+"@glo2000.ca",
            destination=email,
            subject=subject,
            date=gloutils.get_current_utc_time(),
            content=body)

        message = gloutils.GloMessage(header=gloutils.Headers.EMAIL_SENDING, payload=payload)
        message_rec = self._exchange_to_server(message=message)

        header = message_rec["header"]

        if header == gloutils.Headers.OK:
            print("Envoi du message réussit!")
        elif header == gloutils.Headers.ERROR:
            print(message_rec["payload"]["error_message"])
        else:
            print("Erreur dans le traitement du message reçu.")
        

    def _check_stats(self) -> None:
        """
        Demande les statistiques au serveur avec l'entête `STATS_REQUEST`.

        Affiche les statistiques à l'aide du gabarit `STATS_DISPLAY`.
        """

        message = gloutils.GloMessage(header=gloutils.Headers.STATS_REQUEST, payload=None)
        message_rec = self._exchange_to_server(message=message)

        payload = message_rec["payload"]
        count = payload["count"]
        size = payload["size"]

        print(gloutils.STATS_DISPLAY.format(count=count, size=size))

    def _logout(self) -> None:
        """
        Préviens le serveur avec l'entête `AUTH_LOGOUT`.

        Met à jour l'attribut `_username`.
        """

        message = gloutils.GloMessage(header=gloutils.Headers.AUTH_LOGOUT, payload=None)

        self._send_server_message(message)

        self._username = None

    def _get_input_number_between(self, min: int, max: int) -> int:
        while True:
            try:
                choice = int(input("Entrer votre choix."))
                if choice not in range(min, max+1):
                    raise ValueError()
                break
            except:
                print(f"Le choix doît être un nombre de {min} à {max}.")
        return choice

    def _authentication_menu(self) -> bool:
        """Returns true if the program should quit."""
        print(20*"-")
        print(gloutils.CLIENT_AUTH_CHOICE)
        print(20*"-")

        choice = self._get_input_number_between(min=1, max=3)
        
        if (choice == 1):
            self._register()
        if (choice == 2):
            self._login()
        if (choice == 3):
            return True
        
        return False

    def _main_menu(self):
        
        print()
        print()
        print(f"Connecté à {self._username}")
        print()
        print(gloutils.CLIENT_USE_CHOICE)
        print()

        choice = self._get_input_number_between(1, 4)
        
        if (choice == 1):
            self._read_email()
        if (choice == 2):
            self._send_email()
        if (choice == 3):
            self._check_stats()
        if (choice == 4):
            self._logout()


    def run(self) -> None:
        """Point d'entrée du client."""
        should_quit = False

        while not should_quit:
            if not self._username:
                # Authentication menu
                should_quit = self._authentication_menu()
            else:
                # Main menu
                self._main_menu()
        
        self._quit()


def _main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--destination", action="store",
                        dest="dest", required=True,
                        help="Adresse IP/URL du serveur.")
    args = parser.parse_args(sys.argv[1:])
    client = Client(args.dest)
    client.run()
    return 0


if __name__ == '__main__':
    sys.exit(_main())
