from ape.exceptions import ApeException

class QuickNodeProviderError(ApeException):
    """
    Raised when there's an error with the QuickNode provider.
    """

class QuickNodeFeatureNotAvailable(QuickNodeProviderError):
    """
    Raised when a requested feature is not available in the current QuickNode plan.
    """

class MissingAuthTokenError(QuickNodeProviderError):
    def __init__(self, missing_vars):
        super().__init__(f"Missing environment variables: {', '.join(missing_vars)}")