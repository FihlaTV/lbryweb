class DaemonException(Exception):

    def __str__(self):
        return '{}: {}'.format(self.__class__.__name__, super().__str__())


class AccountNotFound(DaemonException):
    pass


class AccountMissing(DaemonException):
    pass
