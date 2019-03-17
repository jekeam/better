# -*- coding: utf-8 -*-
from bet_olimp import *
from bet_fonbet import *
from better import OLIMP_USER, FONBET_USER
from utils import prnt
from math import ceil
from datetime import datetime
import time, random
import json
import os
from utils import DEBUG

file_name = 'id_forks.txt'
olimp_bet_min = 1000000000
fonbet_bet_min = 999999999999999999999

with open(file_name, encoding='utf-8') as f:
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
    offset = ceil(count / 10) + 1

    is_break = False
    for n in range(0, offset):
        if not is_break:
            js = get_chank(n)
            for id in js.keys():
                if id <= olimp_bet_min:
                    is_break = True
            coupot_list.update(js)
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
    o_list = olimp_get_hist(OLIMP_USER)
    f_list = fonbet_get_hist(FONBET_USER)

    ol_list = json.loads(json.dumps(o_list, ensure_ascii=False))
    fb_list = json.loads(json.dumps(f_list, ensure_ascii=False))

    # print(json.dumps(ol_list, ensure_ascii=False))
    # print(json.dumps(fb_list, ensure_ascii=False))

    # fb_list = {"15001529116": {"time": "2019-03-17 08:16:39", "kof": "1.55", "sum_bet": "650.0", "profit": "0.0", "result": "lose", "name": "Саутерн Таблеландс Юн - УК Пумас: Обе забьют", "status": "calculated"}, "15001533448": {"time": "2019-03-17 08:17:23", "kof": "2.90", "sum_bet": "345.0", "profit": "1001.0", "result": "win", "name": "Саутерн Таблеландс Юн - УК Пумас", "status": "calculated"}, "15001349429": {"time": "2019-03-17 07:47:44", "kof": "1.30", "sum_bet": "780.0", "profit": "1014.0", "result": "win", "name": "Альянса - Сонсонате: Сонсонате забьет", "status": "calculated"}, "15000795396": {"time": "2019-03-17 06:18:07", "kof": "1.70", "sum_bet": "595.0", "profit": "1012.0", "result": "win", "name": "Энвигадо - Рионегро Агилас (Дорадос)", "status": "calculated"}, "15001086039": {"time": "2019-03-17 07:03:01", "kof": "20.00", "sum_bet": "50.0", "profit": "0.0", "result": "lose", "name": "Сан Антонио ФК - Портленд-2", "status": "calculated"}, "14999742887": {"time": "2019-03-17 03:50:59", "kof": "2.25", "sum_bet": "450.0", "profit": "1013.0", "result": "win", "name": "Универсидад Католика - Делфин", "status": "calculated"}, "14998113571": {"time": "2019-03-17 01:59:54", "kof": "3.15", "sum_bet": "315.0", "profit": "0.0", "result": "lose", "name": "Унион Комерсио - Универсидад Сан-Мартин: Обе забьют", "status": "calculated"}, "14996690959": {"time": "2019-03-17 00:54:00", "kof": "1.88", "sum_bet": "530.0", "profit": "530.0", "result": "return", "name": "Торино - Болонья", "status": "calculated"}, "14995655551": {"time": "2019-03-17 00:17:53", "kof": "1.90", "sum_bet": "530.0", "profit": "0.0", "result": "lose", "name": "Анжер - Амьен: Амьен забьет", "status": "calculated"}, "14995638289": {"time": "2019-03-17 00:17:14", "kof": "4.20", "sum_bet": "240.0", "profit": "0.0", "result": "lose", "name": "Анжер - Амьен", "status": "calculated"}, "14997716191": {"time": "2019-03-17 01:39:11", "kof": "2.50", "sum_bet": "420.0", "profit": "1050.0", "result": "win", "name": "Ольмедо - Гуаякиль С", "status": "calculated"}, "14994775175": {"time": "2019-03-16 23:45:07", "kof": "1.75", "sum_bet": "585.0", "profit": "0.0", "result": "lose", "name": "Унион Санта-Фе - Ланус: Ланус забьет", "status": "calculated"}, "14994440566": {"time": "2019-03-16 23:31:13", "kof": "3.00", "sum_bet": "335.0", "profit": "0.0", "result": "lose", "name": "Брессюир - Монморийон: Монморийон забьет", "status": "calculated"}, "14993925090": {"time": "2019-03-16 23:13:31", "kof": "1.78", "sum_bet": "570.0", "profit": "1015.0", "result": "win", "name": "Херенвен - Графсхап", "status": "calculated"}, "14994084766": {"time": "2019-03-16 23:19:33", "kof": "1.45", "sum_bet": "700.0", "profit": "1015.0", "result": "win", "name": "Атлетик Бильбао - Атлетико Мадрид", "status": "calculated"}, "14994110354": {"time": "2019-03-16 23:20:22", "kof": "2.10", "sum_bet": "470.0", "profit": "987.0", "result": "win", "name": "Витория Гимарайнш - Боавишта: Боавишта забьет", "status": "calculated"}, "14994170306": {"time": "2019-03-16 23:22:17", "kof": "1.75", "sum_bet": "580.0", "profit": "1015.0", "result": "win", "name": "Суонси - Манчестер С", "status": "calculated"}, "14994146836": {"time": "2019-03-16 23:21:32", "kof": "1.43", "sum_bet": "705.0", "profit": "1008.0", "result": "win", "name": "Суонси - Манчестер С", "status": "calculated"}, "14993741171": {"time": "2019-03-16 23:06:57", "kof": "2.35", "sum_bet": "420.0", "profit": "0.0", "result": "lose", "name": "Атлетик Бильбао - Атлетико Мадрид", "status": "calculated"}, "14993367286": {"time": "2019-03-16 22:54:51", "kof": "1.88", "sum_bet": "530.0", "profit": "0.0", "result": "lose", "name": "Атлетик Бильбао - Атлетико Мадрид", "status": "calculated"}, "14992840796": {"time": "2019-03-16 22:37:34", "kof": "1.14", "sum_bet": "880.0", "profit": "1003.0", "result": "win", "name": "Суонси - Манчестер С", "status": "calculated"}, "14993723581": {"time": "2019-03-16 23:06:17", "kof": "2.75", "sum_bet": "370.0", "profit": "1018.0", "result": "win", "name": "Санлукено - Картахена", "status": "calculated"}, "14994235380": {"time": "2019-03-16 23:24:06", "kof": "1.55", "sum_bet": "650.0", "profit": "1008.0", "result": "win", "name": "Суонси - Манчестер С", "status": "calculated"}, "14992528115": {"time": "2019-03-16 22:27:44", "kof": "1.23", "sum_bet": "825.0", "profit": "0.0", "result": "lose", "name": "Хапоэль Тель-Авив - Ашдод", "status": "calculated"}, "14991503747": {"time": "2019-03-16 21:56:39", "kof": "4.70", "sum_bet": "215.0", "profit": "1011.0", "result": "win", "name": "Хапоэль Тель-Авив - Ашдод: Обе забьют", "status": "calculated"}, "14993029144": {"time": "2019-03-16 22:43:46", "kof": "2.90", "sum_bet": "350.0", "profit": "1015.0", "result": "win", "name": "Суонси - Манчестер С", "status": "calculated"}, "14991662446": {"time": "2019-03-16 22:01:31", "kof": "6.90", "sum_bet": "145.0", "profit": "0.0", "result": "lose", "name": "Эстеглал Тегеран - Нассаджи Мазандаран", "status": "calculated"}, "14989521152": {"time": "2019-03-16 20:49:31", "kof": "1.30", "sum_bet": "775.0", "profit": "1008.0", "result": "win", "name": "Реал Мадрид - Сельта", "status": "calculated"}, "14988526673": {"time": "2019-03-16 20:17:56", "kof": "1.14", "sum_bet": "880.0", "profit": "1003.0", "result": "win", "name": "Реал Мадрид - Сельта", "status": "calculated"}, "14989061179": {"time": "2019-03-16 20:33:47", "kof": "1.50", "sum_bet": "680.0", "profit": "0.0", "result": "lose", "name": "Вест Хэм Юн - Хаддерсфилд Т", "status": "calculated"}, "14989762731": {"time": "2019-03-16 20:57:34", "kof": "1.43", "sum_bet": "700.0", "profit": "1001.0", "result": "win", "name": "Вольфсбург - Фортуна Дюссельдорф", "status": "calculated"}, "14987996257": {"time": "2019-03-16 19:59:01", "kof": "1.45", "sum_bet": "685.0", "profit": "993.0", "result": "win", "name": "Шальке-04 - Лейпциг", "status": "calculated"}, "14989875590": {"time": "2019-03-16 21:01:31", "kof": "12.00", "sum_bet": "85.0", "profit": "43.0", "result": "lose", "name": "Бешикташ - Гезтепе", "status": "completelySold"}, "14986872625": {"time": "2019-03-16 19:22:16", "kof": "1.95", "sum_bet": "525.0", "profit": "0.0", "result": "lose", "name": "Аль-Сайлия - Аль-Садд", "status": "calculated"}, "14988650857": {"time": "2019-03-16 20:22:07", "kof": "2.45", "sum_bet": "415.0", "profit": "1017.0", "result": "win", "name": "Бернли - Лестер С: Обе забьют", "status": "calculated"}, "14987613021": {"time": "2019-03-16 19:46:36", "kof": "1.75", "sum_bet": "575.0", "profit": "1006.0", "result": "win", "name": "Аль-Дафра - Аль-Шарджа: Аль-Шарджа забьет", "status": "calculated"}, "14988582493": {"time": "2019-03-16 20:19:43", "kof": "1.83", "sum_bet": "550.0", "profit": "1007.0", "result": "win", "name": "Бернли - Лестер С: Лестер С забьет", "status": "calculated"}, "14986010340": {"time": "2019-03-16 18:52:49", "kof": "2.10", "sum_bet": "480.0", "profit": "0.0", "result": "lose", "name": "Лудогорец - Септември София", "status": "calculated"}, "14984254198": {"time": "2019-03-16 17:51:41", "kof": "2.45", "sum_bet": "415.0", "profit": "1017.0", "result": "win", "name": "Лидс Юн - Шеффилд Юн", "status": "calculated"}, "14983999456": {"time": "2019-03-16 17:41:45", "kof": "2.80", "sum_bet": "360.0", "profit": "1008.0", "result": "win", "name": "Уотфорд - Кристал Пэлас: Обе забьют", "status": "calculated"}, "14984890829": {"time": "2019-03-16 18:14:01", "kof": "1.14", "sum_bet": "880.0", "profit": "1003.0", "result": "win", "name": "Наньтун Чжиюнь - Ляонин Хувин", "status": "calculated"}, "14984079016": {"time": "2019-03-16 17:44:53", "kof": "7.40", "sum_bet": "140.0", "profit": "0.0", "result": "lose", "name": "Гол Гохар - Персеполис Пакдашт", "status": "calculated"}, "14984118929": {"time": "2019-03-16 17:46:34", "kof": "1.85", "sum_bet": "550.0", "profit": "1018.0", "result": "win", "name": "Гол Гохар - Персеполис Пакдашт", "status": "calculated"}, "14984223520": {"time": "2019-03-16 17:50:31", "kof": "10.00", "sum_bet": "100.0", "profit": "0.0", "result": "lose", "name": "ПСИС Семаранг - ПСМ Макассар: Обе забьют", "status": "calculated"}, "14983860215": {"time": "2019-03-16 17:36:31", "kof": "2.50", "sum_bet": "405.0", "profit": "0.0", "result": "lose", "name": "ПСИС Семаранг - ПСМ Макассар", "status": "calculated"}, "14984062208": {"time": "2019-03-16 17:44:11", "kof": "2.60", "sum_bet": "390.0", "profit": "1014.0", "result": "win", "name": "ПСИС Семаранг - ПСМ Макассар", "status": "calculated"}}
    # ol_list = {"54": {"time": "2019-03-17 19:10:31", "kof": "1.04", "sum_bet": "970", "profit": "897", "result": "Выиграло", "name": "ФК Данди - Селтик", "status": "897"}, "53": {"time": "2019-03-17 19:07:30", "kof": "1.4", "sum_bet": "710", "profit": "641", "result": "Выиграло", "name": "Локомотив М - ФК Краснодар", "status": "641"}, "52": {"time": "2019-03-17 19:04:11", "kof": "1.55", "sum_bet": "675", "profit": "595", "result": "Выиграло", "name": "Патронато Парана - Дефенса и Хустисия", "status": "595"}, "51": {"time": "2019-03-17 19:00:19", "kof": "2.35", "sum_bet": "430", "profit": "354", "result": "Выиграло", "name": "Локомотив М - ФК Краснодар", "status": "354"}, "50": {"time": "2019-03-17 18:53:46", "kof": "2.98", "sum_bet": "340", "profit": "267", "result": "Проиграло", "name": "Кайсериспор - Истанбул Башакшехир", "status": "267"}, "49": {"time": "2019-03-17 18:39:22", "kof": "1.28", "sum_bet": "795", "profit": "728", "result": "Проиграло", "name": "Арминия - Бохум", "status": "728"}, "48": {"time": "2019-03-17 08:17:22", "kof": "1.54", "sum_bet": "655", "profit": "0", "result": "Проиграло", "name": "Саузерн Тейбландс Юнайтед - ЮС Пумас", "status": "None"}, "47": {"time": "2019-03-17 08:16:38", "kof": "2.89", "sum_bet": "350", "profit": "1012", "result": "Выиграло", "name": "Саузерн Тейбландс Юнайтед - ЮС Пумас", "status": "None"}, "46": {"time": "2019-03-17 07:47:43", "kof": "4.63", "sum_bet": "220", "profit": "0", "result": "Проиграло", "name": "Альянса - Сонсонате", "status": "None"}, "45": {"time": "2019-03-17 07:03:01", "kof": "1.06", "sum_bet": "950", "profit": "1007", "result": "Выиграло", "name": "Сан Антонио ФК - Портленд Тимберс II", "status": "None"}, "44": {"time": "2019-03-17 06:18:06", "kof": "2.5", "sum_bet": "405", "profit": "0", "result": "Проиграло", "name": "Энвигадо   - Рионегро Агилас", "status": "None"}, "43": {"time": "2019-03-17 03:50:58", "kof": "1.85", "sum_bet": "550", "profit": "0", "result": "Проиграло", "name": "Универсидад Католика - Дельфин", "status": "None"}, "42": {"time": "2019-03-17 01:59:33", "kof": "1.5", "sum_bet": "685", "profit": "1028", "result": "Выиграло", "name": "Унион Комерсио - Универсидад Сан Мартин", "status": "None"}, "41": {"time": "2019-03-17 01:39:16", "kof": "1.8", "sum_bet": "580", "profit": "0", "result": "Проиграло", "name": "Ольмедо - Гуаякиль Сити", "status": "None"}, "40": {"time": "2019-03-17 00:53:58", "kof": "2.15", "sum_bet": "470", "profit": "470", "result": "Возврат", "name": "Торино - Болонья", "status": "None"}, "39": {"time": "2019-03-17 00:17:51", "kof": "2.15", "sum_bet": "470", "profit": "1011", "result": "Выиграло", "name": "Анже - Амьен", "status": "None"}, "38": {"time": "2019-03-17 00:17:13", "kof": "1.33", "sum_bet": "760", "profit": "1011", "result": "Выиграло", "name": "Анже - Амьен", "status": "None"}, "37": {"time": "2019-03-17 00:15:52", "kof": "2.15", "sum_bet": "470", "profit": "392", "result": "Проиграло", "name": "Экскурсионистас - Сентраль Кордоба", "status": "392"}, "36": {"time": "2019-03-16 23:45:06", "kof": "2.4", "sum_bet": "415", "profit": "996", "result": "Выиграло", "name": "Унион Санта-Фе - Ланус", "status": "None"}, "35": {"time": "2019-03-16 23:31:11", "kof": "1.52", "sum_bet": "665", "profit": "1011", "result": "Выиграло", "name": "Брессер - Монморийон", "status": "None"}, "34": {"time": "2019-03-16 23:24:06", "kof": "2.9", "sum_bet": "350", "profit": "0", "result": "Проиграло", "name": "Суонси Сити - Манчестер Сити", "status": "None"}, "33": {"time": "2019-03-16 23:22:11", "kof": "2.4", "sum_bet": "420", "profit": "0", "result": "Проиграло", "name": "Суонси Сити - Манчестер Сити", "status": "None"}, "32": {"time": "2019-03-16 23:21:34", "kof": "3.4", "sum_bet": "295", "profit": "0", "result": "Проиграло", "name": "Суонси Сити - Манчестер Сити", "status": "None"}, "31": {"time": "2019-03-16 23:20:21", "kof": "1.9", "sum_bet": "530", "profit": "0", "result": "Проиграло", "name": "Гимарайнш - Боавишта", "status": "None"}, "30": {"time": "2019-03-16 23:19:35", "kof": "3.4", "sum_bet": "300", "profit": "0", "result": "Проиграло", "name": "Атлетик Б - Атлетико Мадрид", "status": "None"}, "29": {"time": "2019-03-16 23:13:31", "kof": "2.35", "sum_bet": "430", "profit": "0", "result": "Проиграло", "name": "Херенвен - Де Графсхап", "status": "None"}, "28": {"time": "2019-03-16 23:06:54", "kof": "1.75", "sum_bet": "580", "profit": "1015", "result": "Выиграло", "name": "Атлетик Б - Атлетико Мадрид", "status": "None"}, "27": {"time": "2019-03-16 23:06:16", "kof": "1.6", "sum_bet": "630", "profit": "0", "result": "Проиграло", "name": "Атлетико Санлукено - Картахена", "status": "None"}, "26": {"time": "2019-03-16 22:54:51", "kof": "2.25", "sum_bet": "470", "profit": "1058", "result": "Выиграло", "name": "Атлетик Б - Атлетико Мадрид", "status": "None"}, "25": {"time": "2019-03-16 22:43:46", "kof": "1.57", "sum_bet": "650", "profit": "0", "result": "Проиграло", "name": "Суонси Сити - Манчестер Сити", "status": "None"}, "24": {"time": "2019-03-16 22:37:34", "kof": "8.5", "sum_bet": "120", "profit": "0", "result": "Проиграло", "name": "Суонси Сити - Манчестер Сити", "status": "None"}, "23": {"time": "2019-03-16 22:27:44", "kof": "5.75", "sum_bet": "175", "profit": "1006", "result": "Выиграло", "name": "Хапоэль Тель-Авив - Ашдод", "status": "None"}, "22": {"time": "2019-03-16 22:01:30", "kof": "1.18", "sum_bet": "855", "profit": "1009", "result": "Выиграло", "name": "Эстеглаль Тегеран - Нассаджи Мазендеран", "status": "None"}, "21": {"time": "2019-03-16 21:56:36", "kof": "1.3", "sum_bet": "785", "profit": "0", "result": "Проиграло", "name": "Хапоэль Тель-Авив - Ашдод", "status": "None"}, "20": {"time": "2019-03-16 21:01:33", "kof": "1.1", "sum_bet": "915", "profit": "1007", "result": "Выиграло", "name": "Бешикташ - Гёзтепе", "status": "None"}, "19": {"time": "2019-03-16 20:57:33", "kof": "3.4", "sum_bet": "300", "profit": "0", "result": "Проиграло", "name": "Вольфсбург - Фортуна Д", "status": "None"}, "18": {"time": "2019-03-16 20:49:30", "kof": "4.5", "sum_bet": "225", "profit": "0", "result": "Проиграло", "name": "Реал М - Сельта", "status": "None"}, "17": {"time": "2019-03-16 20:33:46", "kof": "3.2", "sum_bet": "320", "profit": "1024", "result": "Выиграло", "name": "Вест Хэм - Хаддерсфилд", "status": "None"}, "16": {"time": "2019-03-16 20:22:07", "kof": "1.75", "sum_bet": "585", "profit": "0", "result": "Проиграло", "name": "Бернли  - Лестер", "status": "None"}, "15": {"time": "2019-03-16 20:19:46", "kof": "2.25", "sum_bet": "450", "profit": "0", "result": "Проиграло", "name": "Бернли  - Лестер", "status": "None"}, "14": {"time": "2019-03-16 20:17:55", "kof": "8.5", "sum_bet": "120", "profit": "0", "result": "Проиграло", "name": "Реал М - Сельта", "status": "None"}, "13": {"time": "2019-03-16 20:00:53", "kof": "2", "sum_bet": "480", "profit": "402", "result": "Проиграло", "name": "Штутгарт - Хоффенхайм", "status": "402"}, "12": {"time": "2019-03-16 19:59:01", "kof": "3.2", "sum_bet": "315", "profit": "0", "result": "Проиграло", "name": "Шальке 04 - РБ Лейпциг", "status": "None"}, "11": {"time": "2019-03-16 19:46:38", "kof": "2.37", "sum_bet": "425", "profit": "0", "result": "Проиграло", "name": "Аль-Дафра - Шарджа", "status": "None"}, "10": {"time": "2019-03-16 19:22:15", "kof": "2.15", "sum_bet": "475", "profit": "1021", "result": "Выиграло", "name": "Аль-Сайлия - Аль-Садд", "status": "None"}, "9": {"time": "2019-03-16 18:52:48", "kof": "1.93", "sum_bet": "520", "profit": "1004", "result": "Выиграло", "name": "Лудогорец Разград - Септември София", "status": "None"}, "8": {"time": "2019-03-16 18:14:04", "kof": "8.3", "sum_bet": "120", "profit": "0", "result": "Проиграло", "name": "Нантонг Жиян - Ляонин Хувин", "status": "None"}, "7": {"time": "2019-03-16 17:51:39", "kof": "1.75", "sum_bet": "585", "profit": "0", "result": "Проиграло", "name": "Лидс - Шеффилд Юнайтед", "status": "None"}, "6": {"time": "2019-03-16 17:50:35", "kof": "1.12", "sum_bet": "900", "profit": "1008", "result": "Выиграло", "name": "ПСИС Семаранг  - ПСМ Макассар", "status": "None"}, "5": {"time": "2019-03-16 17:46:39", "kof": "2.25", "sum_bet": "450", "profit": "0", "result": "Проиграло", "name": "Гол Гохар - Персеполис Пакдешт", "status": "None"}, "4": {"time": "2019-03-16 17:44:57", "kof": "1.17", "sum_bet": "860", "profit": "1006", "result": "Выиграло", "name": "Гол Гохар - Персеполис Пакдешт", "status": "None"}, "3": {"time": "2019-03-16 17:44:15", "kof": "1.65", "sum_bet": "610", "profit": "0", "result": "Проиграло", "name": "ПСИС Семаранг  - ПСМ Макассар", "status": "None"}, "2": {"time": "2019-03-16 17:41:44", "kof": "1.55", "sum_bet": "640", "profit": "0", "result": "Проиграло", "name": "Уотфорд - Кристал Пэлас", "status": "None"}, "1": {"time": "2019-03-16 17:36:35", "kof": "1.65", "sum_bet": "595", "profit": "982", "result": "Выиграло", "name": "ПСИС Семаранг  - ПСМ Макассар", "status": "None"}}
    # print('fb_list=' + str(fb_list))
    # print('ol_list=' + str(ol_list))

    # READ FORKS INFO
    with open(file_name, encoding='utf-8') as f:
        for line in f.readlines():
            fork = json.loads(line.strip())
            for id, info in fork.items():
                ts = int(id)
                val = datetime.fromtimestamp(ts)
                time = val.strftime('%Y-%m-%d %H:%M:%S')

                fb_reg_id = info['fonbet'].get('reg_id', '')
                fb_info = fb_list.get(str(fb_reg_id), {})

                o_reg_id = info['olimp'].get('reg_id', '')
                o_info = ol_list.get(str(o_reg_id), {})

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
                      str(info['olimp'].get('err', '')) + ';' + '\n'

            header = 'ID;time;pre_fb_kof;pre_o_kof;pre_fb_sum;pre_o_sum;' \
                     'fb_id;o_id;fb_time;o_time;fb_kof;o_kof;fb_sum_bet;o_sum_bet;' \
                     'fb_profit;o_profit;fb_result;o_result;fb_name;o_name;fb_status;' \
                     'o_status;f_kof_type;o_kof_type;fb_bal;ol_bal;fb_err;ol_err;\n'

        with open(datetime.now().strftime("%d_%m_%Y") + '_statistics.csv', 'w', encoding='utf-8') as f:
            f.write(header + out)

    os.rename(file_name, datetime.now().strftime("%d_%m_%Y") + '_' + file_name)


if __name__ == "__main__":
    export_hist(OLIMP_USER, FONBET_USER)
