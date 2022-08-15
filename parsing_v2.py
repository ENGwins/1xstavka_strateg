import datetime
import json
import time

import requests
from fake_useragent import UserAgent
import xlsxwriter

from db_commands import add_bet, select_all_record

url = '1xstavka.ru/live/volleyball'

url2 = 'https://1xstavka.ru/LiveFeed/Get1x2_VZip?count=10&mode=4&top=true&partner=51'

my_games_fav = {}


def count(func):
    """
    Декоратор - счётчик
    """

    counters = {}

    def wrapper(*args, **kwargs):
        counters[func] = counters.get(func, 0) + 1
        # print(f'Функция {func.__name__} вызвана {counters[func]} раз')
        if counters[func] > 43200:
            gas = []
            my_games_fav.clear()
            counters[func] = 0
        return func(*args, **kwargs)

    return wrapper


CONDITION = {
    'голТБ': [],
}

MY_GAMES = {

}

test = {
    'Выигрыш-1': 'Выигрыш-2',
    'Выигрыш-2': 'Выигрыш',
    'Выигрыш': 'Выигрыш',
    'Проигрыш-1': 'Проигрыш-2',
    'Проигрыш-2': 'Проигрыш',
    'Проигрыш': 'Проигрыш',
    'В игре': 'В игре'
}


async def parsing_football():
    """
    Здесь происходит отбор матчей по категории футбол
    :return:
    """

    agent = UserAgent()
    headers = {
        'Accept': 'application/json, text/plain, */*',

        'User-Agent': agent.random
    }

    params = {
        'sports': '1',
        'count': '50',
        'antisports': '188',
        'mode': '4',
        'country': '1',
        'partner': '51',
        'getEmpty': 'true',
        'noFilterBlockEvent': 'true',
    }
    response_ = ''

    game_id_all = []
    while response_ == '':
        try:
            response_ = requests.get('https://1xstavka.ru/LiveFeed/Get1x2_VZip', params=params, headers=headers,
                                     timeout=3)
            result_all = response_.json()
            with open('result_football_live.json', 'w', encoding='utf-8') as file:  # файл со всеми играми линии
                json.dump(result_all, file, sort_keys=True, ensure_ascii=False, indent=4)
        except:
            time.sleep(5)
            print('Не получилось подключиться')
            continue

    with open('result_football_live.json', 'r',
              encoding='utf-8') as file_read:  # открывает на чтение json и вытаскиваем матчи
        result_all = json.load(file_read)

    for all_football in result_all['Value']:
        game_id_d = []
        try:
            if all_football['SE'] == 'Football' and all_football['T'] > 99 \
                    and all_football['SC']['CPS'] != 'Игра завершена':
                game_id_d.append(all_football["L"])  # лига
                id = all_football['I']
                game_id_all.append(id)

        except:
            pass
    await check_win(game_id_all)


async def check_win(game_id_all):
    for game_id in game_id_all:
        temp = MY_GAMES.get(game_id, False)
        try:
            info_json = await info_game_json(game_id)
            game_dict = await info_game_detal(info_json)
            coef = await get_coef_strateg1(info_json)

            if not temp:  # если нет игры в словаре
                MY_GAMES[game_id] = {'Рассылка': False, 'Лига': game_dict[game_id].get('Лига', '-'),
                                     'Команда 1': game_dict[game_id].get('Команды')[0],
                                     'Команда 2': game_dict[game_id].get('Команды')[1],
                                     'Cотояние': 'Не добавлен в игру',
                                     'Стратегия': 'Не выбрана',
                                     'Коэффициент': coef,
                                     'Условие выигрыша': '-'}
            else:  # если игра найдена, смотрим добавлена ли стратегия
                if MY_GAMES[game_id]['Стратегия'] == 'Не выбрана' \
                        and MY_GAMES[game_id]['Cотояние'] == 'Не добавлен в игру'\
                        and MY_GAMES[game_id]['Коэффициент'] is not None:  # новая игра

                    strateg1, name1 = await strate1(game_dict, game_id)  # проверка на стратегию 1
                    # strateg2, name2 = await strate2(game_dict, game_id)  # проверка на стратегию 2
                    if strateg1:  # если матч пододит под стратегию
                        # рассылка
                        # получение коэффициента
                        print('Следим за матчем. Рассылка матча ', MY_GAMES[game_id]['Команда 1'],
                              MY_GAMES[game_id]['Команда 2'], '-st1-')
                        MY_GAMES[game_id] = {
                            'Cотояние': 'В игре',
                            'Стратегия': f'{name1}',
                            'Коэффициент': coef
                        }

                    # если матч за которым следим по st1 то нужно проверить выигрыш
                    # смотрим пододит ли нам матч


                elif MY_GAMES[game_id]['Cотояние'] != 'Проигрыш' \
                        and MY_GAMES[game_id]['Cотояние'] != 'Выигрыш':  # матчи в игре кроме Выигриша и Проигрыша

                    check_win_st1 = await cond_win_strateg1(game_dict, game_id)  # Проверка выигрыша по стретегии 1

                    if check_win_st1 == 'Подходит':  # если Подходит
                        new_state = test[MY_GAMES[game_id]['Cотояние']]
                        MY_GAMES[game_id]['Cотояние'] = new_state
                        if MY_GAMES[game_id]['Cотояние'] == 'В игре':
                            MY_GAMES[game_id]['Cотояние'] = 'Выигрыш-1'
                            print('Кажется выигрыш!!!', game_dict[game_id]['Команды'], game_dict[game_id]['Счет'],
                                  MY_GAMES[game_id]['Cотояние'])
                        # сделать рассылку о выигрыше и обновить БД

                        elif MY_GAMES[game_id]['Cотояние'] == 'Выигрыш':
                            print('Точно выигрыш!!!', game_dict[game_id]['Команды'], game_dict[game_id]['Счет'],
                                  MY_GAMES[game_id]['Cотояние'], MY_GAMES[game_id]['Стратегия'],
                                  MY_GAMES[game_id]['Коэффициент'])

                            score=game_dict[game_id]['Счет'][0],game_dict[game_id]['Счет'][1]
                            await add_bet(strateg=str(MY_GAMES[game_id]['Стратегия']),
                                          game_id=int(game_id),
                                          score=str(score),
                                          comand_1=str(game_dict[game_id]['Команды'][0]),
                                          comand_2=str(game_dict[game_id]['Команды'][1]),
                                          state='Выигрыш',
                                          coef=MY_GAMES[game_id]['Коэффициент'])

                    elif check_win_st1 == 'Не подходит':
                        new_state = test[MY_GAMES[game_id]['Cотояние']]
                        MY_GAMES[game_id]['Cотояние'] = new_state
                        if MY_GAMES[game_id]['Cотояние'] == 'В игре':
                            MY_GAMES[game_id]['Cотояние'] = 'Проигрыш-1'
                            # MY_GAMES[game_id]['Cотояние'] = 'Проигрыш'
                            print('Кажется Проигрыш', game_dict[game_id]['Команды'], game_dict[game_id]['Счет'],
                                  MY_GAMES[game_id]['Cотояние'])
                        # запись в БД
                        elif MY_GAMES[game_id]['Cотояние'] == 'Проигрыш':
                            print('Точно Проигрыш', game_dict[game_id]['Команды'], game_dict[game_id]['Счет'],
                                  MY_GAMES[game_id]['Cотояние'], MY_GAMES[game_id]['Стратегия'])

                            score=game_dict[game_id]['Счет'][0],game_dict[game_id]['Счет'][1]
                            await add_bet(strateg=str(MY_GAMES[game_id]['Стратегия']),
                                          game_id=int(game_id),
                                          score=str(score),
                                          comand_1=str(game_dict[game_id]['Команды'][0]),
                                          comand_2=str(game_dict[game_id]['Команды'][1]),
                                          state='Проигрыш',
                                          coef=MY_GAMES[game_id]['Коэффициент'])


                elif game_dict[game_id]['Тайм'] == 'Игра завершена':
                    del game_dict[game_id]
                    print('Удалили из словаря игру ', game_dict[game_id]['Команды'])

        except Exception as ex:
            print(ex)
    # print(MY_GAMES)


async def info_game_json(game_id):
    global result_all
    agent = UserAgent()
    headers = {
        'Accept': 'application/json, text/plain, */*',

        'User-Agent': agent.random
    }

    url = f'https://melbet.ru/LiveFeed/GetGameZip?id={game_id}&partner=195'

    response_ = ''
    while response_ == '':
        try:
            response_ = requests.get(url, headers=headers,
                                     timeout=3)
            result_all = response_.json()
            with open(f'temp/result_football{game_id}_live.json', 'w',
                      encoding='utf-8') as file:  # файл со всеми играми линии
                json.dump(result_all, file, sort_keys=True, ensure_ascii=False, indent=4)
        except Exception as ex:
            time.sleep(5)

            print('Не получилось подключиться в info_game_json', game_id)
            print(ex)
            continue
    return result_all


async def info_game_detal(info_json):
    """
    возвращает словарь игры
    :param info_json:
    :return:
    """
    global game_id, Minut

    game_dict = {}
    try:
        corner = []  # угловые
        penalty = []  # пенальти
        shotsOn = []  # удары в створ
        shotsOff = []  # удары мимо ворот
        Attacks = []  # атаки
        DanAttacks = []  # опасные атаки
        freeKick = []  # штрафные
        red_cards = []
        yel_cards = []

        for i in info_json['Value']['SC']['S']:
            if i['Key'] == 'ICorner1':
                corner.append(i.get('Value', 0))
            elif i['Key'] == 'ICorner2':
                corner.append(i.get('Value', 0))
            elif i['Key'] == 'IPenalty1':
                penalty.append(i.get('Value', 0))
            elif i['Key'] == 'IPenalty2':
                penalty.append(i.get('Value', 0))
            elif i['Key'] == 'ShotsOn1':
                shotsOn.append(i.get('Value', 0))
            elif i['Key'] == 'ShotsOn2':
                shotsOn.append(i.get('Value', 0))
            elif i['Key'] == 'shotsOff1':
                shotsOff.append(i.get('Value', 0))
            elif i['Key'] == 'shotsOff2':
                shotsOff.append(i.get('Value', 0))
            elif i['Key'] == 'Attacks1':
                Attacks.append(i.get('Value', 0))
            elif i['Key'] == 'Attacks2':
                Attacks.append(i.get('Value', 0))
            elif i['Key'] == 'DanAttacks1':
                DanAttacks.append(i.get('Value', 0))
            elif i['Key'] == 'DanAttacks2':
                DanAttacks.append(i.get('Value', 0))
            elif i['Key'] == 'FreeKick1':
                freeKick.append(i.get('Value', 0))
            elif i['Key'] == 'FreeKick2':
                freeKick.append(i.get('Value', 0))
            elif i['Key'] == 'IYellowCard1':
                yel_cards.append(i.get('Value', 0))
            elif i['Key'] == 'IYellowCard2':
                yel_cards.append(i.get('Value', 0))
            elif i['Key'] == 'IRedCard1':
                red_cards.append(i.get('Value', 0))
            elif i['Key'] == 'IRedCard2':
                red_cards.append(i.get('Value', 0))

        score = [result_all['Value']['SC']['FS'].get('S1', 0), result_all['Value']['SC']['FS'].get('S2', 0)]

        comands = result_all['Value']['O1'], result_all['Value']['O2']
        liga = result_all['Value'].get('L', '-')

        Minut = int(result_all['Value']['SC'].get('TS', 0) / 60)
        taim = result_all['Value']['SC'].get('CPS', '-')

        game_id = result_all['Value'].get('I')
        game_dict[game_id] = {'Команды': comands, 'Счет': score,
                              'Красные карточки': red_cards, 'Желтые карточки': yel_cards,
                              'Штрафные': freeKick, 'Опасные атаки': DanAttacks, 'Атаки': Attacks,
                              'Удары мимо': shotsOff, 'Удары в створ': shotsOn,
                              'Пенальти': penalty, 'Угловые': corner, 'Лига': liga,
                              'Минута': Minut, 'Тайм': taim}

        # здесь будут критерии отбора в process_game передаем id нужной игры
        # await process_game(game_id)
        # print(corner)
    except Exception as ex:
        print(ex)
    return game_dict


async def strate1(game_dict, game_id):
    """
    total=1
    Minut>50
    red_cards=0

    выигрыш при тотале более 2
    :return:
    """

    total = sum(game_dict[game_id]['Счет'])
    Minut = game_dict[game_id].get('Минута')
    taim = game_dict[game_id].get('Тайм')
    red_cards = game_dict[game_id].get('Красные карточки')
    total_red_cards = 0
    for card in red_cards:
        total_red_cards += int(card)
    if total == 0 and taim == '2-й Тайм' and 66 > Minut > 45:
        return True, 'st1'
    else:
        return False, 'st1'


async def cond_win_strateg1(game_dict, game_id):
    """
    1. Тотал >2

    :return:
    """

    total = sum(game_dict[game_id]['Счет'])
    end = game_dict[game_id]['Тайм']
    Minut = game_dict[game_id]['Минута']
    if total > 0 and Minut < 61:
        return 'Подходит'
    # elif end == 'Игра завершена':
    # elif end == 'Перерыв':
    elif Minut > 60:
        return 'Не подходит'
    else:
        return 'В игре'


async def get_coef_strateg1(info_json):
    # print(info_json['Value']['E'])
    for i in info_json['Value']['E']:
        if i['T'] == 812 and i['P'] == 60.001:
            # print(i['C'],info_json['Value']['O1'])
            return i['C']
        # for n in i['E']:
        #  print(n)

        # if i['Key'] == 'ICorner1':
        #  corner.append(i.get('Value', 0))


async def csv_all():
    all_rec = await select_all_record()
    workbook = xlsxwriter.Workbook('отчет.xlsx')
    worksheet = workbook.add_worksheet()
    content = ['Стратегия', 'Команды', 'Cчет','Коэффициент', 'Результат']
    colm=0
    for cl in content:

        worksheet.write(0, colm, cl)
        colm+=1

    row = 1

    for rec in all_rec:
        item = [rec.strateg, rec.comand, rec.score, float(rec.coef), rec.state]
        column=0
        for wr in item:
            worksheet.write(row, column, wr)

            column += 1
        row+=1

    workbook.close()

    # print(len(all))
