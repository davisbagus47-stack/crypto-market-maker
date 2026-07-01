from dataclasses import dataclass


@dataclass
class SigaSession:
    username: str
    access_token: str
    refresh_token: str | None = None


def login(username: str, password: str, app_id: int = 2) -> SigaSession:
    """Login SIGA.

    Implementasi final perlu memanggil endpoint resmi:
    /sigaauthorizationservice/auth/signin

    Password tidak boleh ditulis ke log.
    """
    raise NotImplementedError("Implementasi login aktif belum dipasang di skeleton.")
