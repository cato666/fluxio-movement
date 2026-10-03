"""Channel-independent errors; HTTP adapters decide status codes."""


class TrainingError(Exception):
    pass


class TrainingInvalid(TrainingError):
    pass


class TrainingTooLarge(TrainingError):
    pass


class TrainingNotFound(TrainingError):
    pass


class TrainingUnavailable(TrainingError):
    pass


class TrainingProcessingFailed(TrainingError):
    pass
