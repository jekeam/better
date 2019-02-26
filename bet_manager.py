from exceptions import BetIsLost
from math import floor
from utils import prnt
from time import time


class BetManager:

    def __init__(self, bk: str, obj: dict, vector: str, sc1: int, sc2: int, cur_total: float):
        if bk in ('fonbet', 'olimp'):
            self.bk = bk
        else:
            raise ValueError('bk not defined, bk=' + bk)
        self.vector = vector
        self.sc1 = int(sc1)
        self.sc2 = int(sc2)
        self.new_sc1 = None
        self.new_sc2 = None
        self.cur_total = cur_total
        self.time_start = time()

        if self.cur_total:
            self.diff_total = max(0, floor(self.cur_total - (self.sc1 + self.sc2)))

        return self.start(obj)

    def start(self, obj):
        if self.diff_total:
            prnt('cur diff_total: ' + str(self.diff_total))

        # update param
        new_obj = {}

        timeout_up = 60 * 10
        timeout_down = 60 * 2.5

        try:
            new_sc1 = int(new_obj['sc1'])
        except Exception as e:
            err_str = 'sc1 not not defined, {} - {}'.format(str(new_obj), str(e))
            prnt(err_str)
            raise ValueError(err_str)
        try:
            new_sc2 = int(new_obj['sc2'])
        except Exception as e:
            err_str = 'sc2 not not defined, {} - {}'.format(str(new_obj), str(e))
            prnt(err_str)
            raise ValueError(err_str)

        # check: score changed?
        if self.sc1 == new_sc1 and self.sc2 == new_sc2 and self.diff_total == 0:
            if self.vector == 'UP':
                if self.cur_total < new_sc1 + new_sc2:
                    err_str = " cur_total:{}, new_sc1:{}, new_sc2: {}. Current bet lost... I'm sorry..." \
                        .format(str(self.cur_total), str(new_sc1), str(new_sc2))
                    prnt(err_str)
                    BetIsLost(err_str)
                else:
                    # recalc sum
                    # go bets
                    pass
            elif self.vector == 'DOWN':
                if self.cur_total <= new_sc1 + new_sc2:
                    err_str = " cur_total:{}, new_sc1:{}, new_sc2: {}. Current bet lost... I'm sorry..." \
                        .format(str(self.cur_total), str(new_sc1), str(new_sc2))
                    prnt(err_str)
                    BetIsLost(err_str)
                else:
                    pass
                    # recalc sum
                    # go bets
        else:
            if self.vector == 'UP':
                pass
                # recalc sum
                # go bets
            elif self.vector == 'DOWN':
                pass
                # recalc sum
                # go bets
