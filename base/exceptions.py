class ElementParseError(Exception):
    """Raises when some error was aquired while stanza pasring, e.g. attribute
    or node is required but not given. An error stanza with the bad-request
    condition will be returned if such exception will be raised."""
    pass

class WrongElement(Exception):
    """
    Raises when an element declaration can't be compared with the given one.
    """
    pass
