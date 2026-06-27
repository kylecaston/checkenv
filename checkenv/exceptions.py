class CheckEnvException(Exception):
    def __init__(self, missing: list[str], optional: list[str]) -> None:
        self._missing = missing
        self._optional = optional
        super().__init__(f"Missing required environment variables: {', '.join(missing)}")

    @property
    def missing(self) -> list[str]:
        return self._missing

    @property
    def optional(self) -> list[str]:
        return self._optional
