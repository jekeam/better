import os

import sys, traceback

def lumberjack():
    bright_side_of_death()

def bright_side_of_death():
    return tuple()[0]

try:
    lumberjack()
except IndexError:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    print("*** print_tb:")
    traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
    print("*** print_exception:")
    # exc_type below is ignored on 3.5 and later
    traceback.print_exception(exc_type, exc_value, exc_traceback,
                              limit=2, file=sys.stdout)
    print("*** print_exc:")
    traceback.print_exc(limit=2, file=sys.stdout)
    print("*** format_exc, first and last line:")
    formatted_lines = traceback.format_exc().splitlines()
    print(formatted_lines[0])
    print(formatted_lines[-1])
    print("*** format_exception:")
    # exc_type below is ignored on 3.5 and later
    print(repr(traceback.format_exception(exc_type, exc_value,
                                          exc_traceback)))
    print("*** extract_tb:")
    print(repr(traceback.extract_tb(exc_traceback)))
    print("*** format_tb:")
    print(repr(traceback.format_tb(exc_traceback)))
    print("*** tb_lineno:", exc_traceback.tb_lineno)

def sold(vector, cur_total, sc1, sc2):
    cur_sc1 = int(sc1)
    cur_sc2 = int(sc2)
    new_sc1 = None
    new_sc2 = None
    
    # update param
    new_obj = {}
    
    try:
        new_sc1 = int(new_obj['sc1'])
    except Exception as e:
        err_str = 'sc1 not not defined, {} - {}'.format(str(new_obj), str(e))
        print(err_str)
        raise ValueError(err_str)
    try:
        new_sc2 = int(new_obj['sc2'])
    except Exception as e:
        err_str = 'sc2 not not defined, {} - {}'.format(str(new_obj), str(e))
        print(err_str)
        raise ValueError(err_str)
        
    # check change score?
    if cur_sc1 == new_sc1 and cur_sc2 == new_sc2:
        pass
    else:
        pass
        