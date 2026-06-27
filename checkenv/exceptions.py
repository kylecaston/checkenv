class CheckEnvException(Exception):
    def __init__(self, missing, optional):
        self._missing = missing
        self._optional = optional
        super().__init__(
            "Missing required environment variables: {}".format(
                ", ".join(missing)
            )
        )

    @property
    def missing(self):
        return self._missing

    @property
    def optional(self):
        return self._optional
