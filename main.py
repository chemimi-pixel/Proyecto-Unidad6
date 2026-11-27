"""Punto de entrada de la aplicacion grafica."""

from laboratorio.database import Database
from laboratorio.ui import Dashboard, LoginWindow


def main() -> None:
    database = Database()
    login = LoginWindow(database)
    login.mainloop()
    if login.user is not None:
        Dashboard(login.user, database).mainloop()


if __name__ == "__main__":
    main()
