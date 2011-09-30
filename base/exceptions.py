class ElementParseError(Exception):
    """Raises when attribute is required and value is None."""
    pass

class WrongElement(Exception):
    """
    Raises when there is invalid element.
    """
    pass
