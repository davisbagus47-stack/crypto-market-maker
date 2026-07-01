from src.siga.auth import SigaSession


class SigaApiClient:
    def __init__(self, session: SigaSession, api_base_url: str):
        self.session = session
        self.api_base_url = api_base_url.rstrip("/")

    def submit(self, endpoint: str, payload: dict) -> dict:
        """Submit payload ke endpoint SIGA.

        Method ini sengaja belum aktif agar skeleton aman. Implementasi final
        harus menambahkan idempotency, retry, dan audit log.
        """
        raise NotImplementedError("Submit API belum diaktifkan.")
