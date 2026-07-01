class SigaBrowserAutomation:
    """Adapter browser automation untuk form SIGA.

    Gunakan adapter ini jika endpoint API target belum diketahui. Implementasi
    final perlu membuka route menu, mengisi field, lalu submit setelah approval.
    """

    def __init__(self, web_base_url: str):
        self.web_base_url = web_base_url.rstrip("/")

    def open_target(self, route: str) -> None:
        raise NotImplementedError("Browser automation belum diaktifkan.")

    def fill_form(self, mapped_data: dict) -> None:
        raise NotImplementedError("Form filler belum diaktifkan.")

    def submit_form(self) -> dict:
        raise NotImplementedError("Submit form belum diaktifkan.")
