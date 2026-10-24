class MapperError(Exception):
    """Public errors contain only a fixed code, never library exceptions."""

    def __init__(self, code):
        if not isinstance(code, str) or not code.replace("_", "").isalnum() or not code.isupper():
            code = "INTERNAL_ERROR"
        self.code = code
        super().__init__(code)
