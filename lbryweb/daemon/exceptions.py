class DaemonException(Exception):
    pass


class AccountNotFound(DaemonException):
    pass


class AccountMissing(DaemonException):
    pass
