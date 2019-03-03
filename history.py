# -*- coding: utf-8 -*-
from bet_olimp import *
from bet_fonbet import *
from better import OLIMP_USER, FONBET_USER
from utils import prnt
from math import ceil
from datetime import datetime
import time, random
import json

file_name = 'id_forks.txt'
olimp_bet_min = 1000000
fonbet_bet_min = 999999999999999999999

f = open(file_name, encoding='utf-8')
for line in f.readlines():
    fork = json.loads(line)
    for id, info in fork.items():
        if info['fonbet'].get('reg_id', fonbet_bet_min):
            if int(info['fonbet'].get('reg_id', fonbet_bet_min)) < fonbet_bet_min:
                fonbet_bet_min = info['fonbet'].get('reg_id', '')
        if info['olimp'].get('reg_id', olimp_bet_min):
            if int(info['olimp'].get('reg_id', olimp_bet_min)) < olimp_bet_min:
                olimp_bet_min = info['olimp'].get('reg_id', '')


def olimp_get_hist(OLIMP_USER):
    global olimp_bet_min
    prnt('Олимп: делаю выгрузку')
    """
    # 0111 не расчитанные, выигранные и проигранные
    # 0011 выигранные и проигранные
    # 0001 проигранные
    # 0010 выигранные и выкупденые
    # 0100 не расчитанные
    # 0000 Галки сняты: выиграл и продал
    """

    def get_chank(offset=0):
        coupot_list_chank = dict()
        bet_list = olimp.get_history_bet(filter="0011", offset=offset).get('bet_list')
        for bets in bet_list:
            if bets.get('bet_id') >= olimp_bet_min:
                ts = int(bets.get('dttm'))
                # if you encounter a "year is out of range" error the timestamp
                # may be in milliseconds, try `ts /= 1000` in that case
                val = datetime.fromtimestamp(ts)
                date_str = val.strftime('%Y-%m-%d %H:%M:%S')
                reg_id = bets.get('bet_id')
                coupot_list_chank[reg_id] = {
                    'time': str(date_str),
                    'kof': str(bets.get('final_odd')),
                    'sum_bet': str(bets.get('total_bet')),
                    'profit': str(bets.get('pay_sum')),
                    'result': str(bets.get('result_text')),
                    'name': str(bets.get('events')[0].get('matchname')),
                    'status': str(bets.get('calc_cashout_sum'))
                }
        return coupot_list_chank

    coupot_list = dict()
    olimp = OlimpBot(OLIMP_USER)
    data = olimp.get_history_bet(filter="0011", offset=0)
    count = data.get('count')
    offset = ceil(count / 10)
    # prnt('HISTORY.PY: Olimp get cnt wareg:' + str(count) + ', offset(count/10)=' + str(offset))

    for n in range(0, ceil(offset / 3)):
        coupot_list.update(get_chank(n))
        time.sleep(random.randint(2, 3))
    return coupot_list


def fonbet_get_hist(FONBET_USER):
    global fonbet_bet_min
    prnt('Фонбет: делаю выгрузку')
    is_get_list = list()
    coupon_list = dict()
    fonbet = FonbetBot(FONBET_USER)
    fonbet.sign_in()
    data = fonbet.get_operations(500)
    for operation in data.get('operations'):
        reg_id = operation.get('marker')
        if reg_id not in is_get_list and reg_id >= fonbet_bet_min:
            is_get_list.append(reg_id)
            bet_info = fonbet.get_coupon_info(reg_id)
            try:
                val = datetime.fromtimestamp(bet_info.get('regTime'))
                date_str = val.strftime('%Y-%m-%d %H:%M:%S')
                oper_time = date_str

                coupon_list[reg_id] = {
                    'time': str(oper_time),
                    'kof': str(bet_info.get('coupons')[0]['bets'][0]['factor']),
                    'sum_bet': str(bet_info.get('sum')),
                    'profit': str(bet_info.get('win')),
                    'result': str(bet_info.get('coupons')[0]['bets'][0]['result']),
                    'name': str(bet_info.get('coupons')[0]['bets'][0]['eventName']),
                    'status': str(bet_info.get('state'))
                }
            except Exception as e:
                print(e)
            finally:
                time.sleep(random.randint(2, 3))
    return coupon_list


def export_hist(OLIMP_USER, FONBET_USER):
    global file_name
    out = ""
    ol_list = olimp_get_hist(OLIMP_USER)
    fb_list = fonbet_get_hist(FONBET_USER)

    # fb_list = {12859167801: {'time': '2018-12-11 05:44:33', 'kof': '2.40', 'sum_bet': '110.0', 'profit': 'None', 'result': 'none', 'name': 'Арсенал Саранди - Нуэва Чикаго: Нуэва Чикаго забьет', 'status': 'register'}, 12858195847: {'time': '2018-12-11 03:15:40', 'kof': '1.72', 'sum_bet': '160.0', 'profit': '0.0', 'result': 'lose', 'name': 'Патронато Парана - Велес Сарсфилд', 'status': 'calculated'}, 12858182027: {'time': '2018-12-11 03:13:59', 'kof': '1.80', 'sum_bet': '160.0', 'profit': '0.0', 'result': 'lose', 'name': 'Патронато Парана - Велес Сарсфилд', 'status': 'calculated'}, 12858046688: {'time': '2018-12-11 03:02:16', 'kof': '2.60', 'sum_bet': '110.0', 'profit': '0.0', 'result': 'lose', 'name': 'Бельграно (р) - Тигре (р)', 'status': 'calculated'}, 12857932120: {'time': '2018-12-11 02:52:38', 'kof': '1.25', 'sum_bet': '220.0', 'profit': '275.0', 'result': 'win', 'name': 'Депортиво Рока - Сансинена СиД', 'status': 'calculated'}, 12857890418: {'time': '2018-12-11 02:48:28', 'kof': '1.20', 'sum_bet': '240.0', 'profit': '288.0', 'result': 'win', 'name': 'Депортиво Рока - Сансинена СиД', 'status': 'calculated'}, 12856857931: {'time': '2018-12-11 01:33:05', 'kof': '1.82', 'sum_bet': '150.0', 'profit': '273.0', 'result': 'win', 'name': 'Эвертон - Уотфорд: Уотфорд забьет', 'status': 'calculated'}, 12855343857: {'time': '2018-12-11 00:16:53', 'kof': '2.05', 'sum_bet': '130.0', 'profit': '0.0', 'result': 'lose', 'name': 'Ньюкасл Юн U23 - Норвич С U23: Обе забьют', 'status': 'calculated'}, 12855423062: {'time': '2018-12-11 00:20:35', 'kof': '5.70', 'sum_bet': '50.0', 'profit': '0.0', 'result': 'lose', 'name': 'Виллем II (р) - Дордрехт (р)', 'status': 'calculated'}}
    # ol_list={998: {'time': '2019-02-18 19:27:29', 'kof': '2.02', 'sum_bet': '135', 'profit': '0', 'result': 'Проиграло', 'name': 'Куин оф Саут (рез) - Росс Каунти (рез)', 'status': 'None'}, 997: {'time': '2019-02-18 16:23:32', 'kof': '1.75', 'sum_bet': '165', 'profit': '289', 'result': 'Выиграло', 'name': 'Окжетпес (до 18) - Кызыл-Жар  СК (до 18)', 'status': 'None'}, 996: {'time': '2019-02-18 16:12:02', 'kof': '1.5', 'sum_bet': '200', 'profit': '300', 'result': 'Выиграло', 'name': 'Германия (жен) (до 16) - Шотландия (жен) (до 16)', 'status': 'None'}, 995: {'time': '2019-02-18 16:09:53', 'kof': '2.3', 'sum_bet': '130', 'profit': '0', 'result': 'Проиграло', 'name': 'Окжетпес (до 18) - Кызыл-Жар  СК (до 18)', 'status': 'None'}, 994: {'time': '2019-02-18 15:35:07', 'kof': '2.45', 'sum_bet': '120', 'profit': '294', 'result': 'Выиграло', 'name': 'Окжетпес (до 18) - Кызыл-Жар  СК (до 18)', 'status': 'None'}, 993: {'time': '2019-02-18 15:27:49', 'kof': '2.1', 'sum_bet': '140', 'profit': '120', 'result': 'Проиграло', 'name': 'Окжетпес (до 18) - Кызыл-Жар  СК (до 18)', 'status': '120'}, 992: {'time': '2019-02-18 15:15:34', 'kof': '3.4', 'sum_bet': '85', 'profit': '0', 'result': 'Проиграло', 'name': 'Искра Смоленск - СШОР Зенит', 'status': 'None'}, 991: {'time': '2019-02-18 15:03:38', 'kof': '2.05', 'sum_bet': '145', 'profit': '297', 'result': 'Выиграло', 'name': 'Окжетпес (до 18) - Кызыл-Жар  СК (до 18)', 'status': 'None'}, 990: {'time': '2019-02-18 14:13:11', 'kof': '1.97', 'sum_bet': '145', 'profit': '286', 'result': 'Выиграло', 'name': 'Арамбаг - Нофель', 'status': 'None'}, 989: {'time': '2019-02-18 13:38:17', 'kof': '2.18', 'sum_bet': '130', 'profit': '283', 'result': 'Выиграло', 'name': 'Буллин Лайонс (до 20) - Мэннингем Юн Блюз (до 20)', 'status': 'None'}, 988: {'time': '2019-02-18 13:24:13', 'kof': '1.35', 'sum_bet': '215', 'profit': '290', 'result': 'Выиграло', 'name': 'Тараз (до 18) - Ордабасы (до 18)', 'status': 'None'}, 987: {'time': '2019-02-18 13:23:13', 'kof': '2.75', 'sum_bet': '105', 'profit': '289', 'result': 'Выиграло', 'name': 'Тараз (до 18) - Ордабасы (до 18)', 'status': 'None'}, 986: {'time': '2019-02-18 13:14:19', 'kof': '1.55', 'sum_bet': '185', 'profit': '0', 'result': 'Проиграло', 'name': 'Тараз (до 18) - Ордабасы (до 18)', 'status': 'None'}, 985: {'time': '2019-02-18 13:10:49', 'kof': '2.05', 'sum_bet': '140', 'profit': '0', 'result': 'Проиграло', 'name': 'Тараз (до 18) - Ордабасы (до 18)', 'status': 'None'}, 984: {'time': '2019-02-18 13:07:46', 'kof': '1.85', 'sum_bet': '160', 'profit': '0', 'result': 'Проиграло', 'name': 'Тараз (до 18) - Ордабасы (до 18)', 'status': 'None'}, 983: {'time': '2019-02-18 13:06:17', 'kof': '2.1', 'sum_bet': '140', 'profit': '0', 'result': 'Проиграло', 'name': 'Тараз (до 18) - Ордабасы (до 18)', 'status': 'None'}, 982: {'time': '2019-02-18 13:03:20', 'kof': '3.25', 'sum_bet': '90', 'profit': '0', 'result': 'Проиграло', 'name': 'Тараз (до 18) - Ордабасы (до 18)', 'status': 'None'}, 981: {'time': '2019-02-18 11:12:12', 'kof': '2.15', 'sum_bet': '140', 'profit': '0', 'result': 'Проиграло', 'name': 'Маркет Света - Ленинградец', 'status': 'None'}}
    # print('fb_list=' + str(fb_list))
    # print('ol_list=' + str(ol_list))

    # READ FORKS INFO
    f = open(file_name, encoding='utf-8')
    for line in f.readlines():
        fork = json.loads(line.strip())
        for id, info in fork.items():
            ts = int(id)
            val = datetime.fromtimestamp(ts)
            time = val.strftime('%Y-%m-%d %H:%M:%S')

            fb_reg_id = info['fonbet'].get('reg_id', '')
            fb_info = fb_list.get(fb_reg_id, {'': ''})

            o_reg_id = info['olimp'].get('reg_id', '')
            o_info = ol_list.get(o_reg_id, {'': ''})

            if fb_info.get('profit', 0.0) == 'None':
                fb_info_profit = 0.0
            else:
                fb_info_profit = fb_info.get('profit', 0.0)

            out = out + \
                  str(id) + ';' + \
                  str(time) + ';' + \
                  str(info['fonbet'].get('kof', 0.0)).replace('.', ',') + ';' + \
                  str(info['olimp'].get('kof', 0.0)).replace('.', ',') + ';' + \
 \
                  str(round(float(info['fonbet'].get('amount', 0.0)))) + ';' + \
                  str(round(float(info['olimp'].get('amount', 0.0)))) + ';' + \
 \
                  str(info['fonbet'].get('reg_id', '')) + ';' + \
                  str(info['olimp'].get('reg_id', '')) + ';' + \
 \
                  str(fb_info.get('time', '')) + ';' + \
                  str(o_info.get('time', '')) + ';' + \
 \
                  str(fb_info.get('kof', '')).replace('.', ',') + ';' + \
                  str(o_info.get('kof', '')).replace('.', ',') + ';' + \
 \
                  str(round(float(fb_info.get('sum_bet', 0.0)))) + ';' + \
                  str(o_info.get('sum_bet', '')) + ';' + \
 \
                  str(round(float(fb_info_profit))) + ';' + \
                  str(o_info.get('profit', '')) + ';' + \
 \
                  str(fb_info.get('result', '')) + ';' + \
                  str(o_info.get('result', '')) + ';' + \
 \
                  str(fb_info.get('name', '')) + ';' + \
                  str(o_info.get('name', '')) + ';' + \
 \
                  str(fb_info.get('status', '')) + ';' + \
                  str(o_info.get('status', '')) + ';' + \
 \
                  str(info['fonbet'].get('bet_type', '')) + ';' + \
                  str(info['olimp'].get('bet_type', '')) + ';' + \
 \
                  str(info['fonbet'].get('balance', '')) + ';' + \
                  str(info['olimp'].get('balance', '')) + ';' + \
 \
                  str(info['fonbet'].get('err', '')) + ';' + \
                  str(info['olimp'].get('err', '')) + ';' +  '\n'

        header = 'ID;time;pre_fb_kof;pre_o_kof;pre_fb_sum;pre_o_sum;' \
                 'fb_id;o_id;fb_time;o_time;fb_kof;o_kof;fb_sum_bet;o_sum_bet;' \
                 'fb_profit;o_profit;fb_result;o_result;fb_name;o_name;fb_status;' \
                 'o_status;f_kof_type;o_kof_type;fb_bal;ol_bal;fb_err;ol_err;\n'

        with open('statistics.csv', 'w', encoding='utf-8') as f:
            f.write(header + out)


export_hist(OLIMP_USER, FONBET_USER)
