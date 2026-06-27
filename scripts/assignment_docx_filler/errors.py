class AssignmentFillerError(RuntimeError):
    """Base error for a user-actionable assignment filler failure."""


class UnsupportedTemplateError(AssignmentFillerError):
    """Raised when an input format cannot be handled without data loss."""


class UnsafeTemplateError(AssignmentFillerError):
    """Raised when a requested edit could remove teacher-provided content."""


class MappingError(AssignmentFillerError):
    """Raised when a slot map is missing or inconsistent with its template."""

