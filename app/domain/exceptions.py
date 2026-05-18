class FileTooLargeError(Exception):
    def __init__(self, size_mb: float, max_mb: int) -> None:
        self.size_mb = size_mb
        self.max_mb = max_mb
        super().__init__(f"File size {size_mb:.1f}MB exceeds maximum {max_mb}MB")


class InvalidFileTypeError(Exception):
    def __init__(self, type_value: str) -> None:
        self.type_value = type_value
        super().__init__(f"File type '{type_value}' is not allowed")


class AnalysisNotFoundError(Exception):
    def __init__(self, analysis_id: str) -> None:
        self.analysis_id = analysis_id
        super().__init__(f"Analysis {analysis_id} not found")


class StorageError(Exception):
    pass


class MessagingError(Exception):
    pass
