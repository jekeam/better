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
        