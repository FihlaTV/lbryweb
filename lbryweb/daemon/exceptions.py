class DaemonException(Exception):

    def __str__(self):
        return self.__class__.__name__


class AccountNotFound(DaemonException):
    pass


class AccountMissing(DaemonException):
    pass
