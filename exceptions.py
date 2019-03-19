# coding:utf-8
class FonbetMatchСompleted(Exception):
    pass


class OlimpMatchСompleted(Exception):
    pass


class TimeOut(Exception):
    pass


class Shutdown(Exception):
    pass


class TimeOutFonbet(Exception):
    pass


class FonbetBetError(Exception):
    pass


class OlimpBetError(Exception):
    pass



# new except new concept
class BetIsLost(Exception):
    pass

class MaxFail(Exception):
    pass

class MaxFork(Exception):
    pass

class SessionNotDefined(Exception):
    pass

class BkOppBetError(Exception):
    pass

class NoMoney(Exception):
    pass

class BetError(Exception):
    pass

class SaleError(Exception):
    pass

class CouponBlocked(Exception):
    pass

class SessionExpired(Exception):
    pass