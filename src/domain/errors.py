"""Errors that distinguish rejected input from operational failures."""


class BusinessError(ValueError):
    """Safe, local feedback; does not generate a Super incident."""


class ModelError(RuntimeError):
    def __init__(self, message: str, *, diagnostic: str = ""):
        super().__init__(message)
        self.diagnostic = f"{message}\n{diagnostic}" if diagnostic else message
