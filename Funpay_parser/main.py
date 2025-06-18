import constants as ct
from starter import Starter
import asyncio
import bs4
from aiohttp import ClientSession
import re
import os
import json
from fake_useragent import UserAgent
import random
from pycbrf.toolbox import ExchangeRates
from datetime import datetime


def try_deco(tries=3):
    """Decorator that's trying to get page by 'tries' times"""
    def try_deco_inner(func):
        async def __wrapper__(*args, **kwargs):
            try:
                await func(*args, **kwargs)
                return
            except:
                await asyncio.sleep(random.uniform(1, 10))
                for _ in range(tries - 1):
                    try:
                        await func(*args, **kwargs)
                        return
                    except:
                        await asyncio.sleep(random.uniform(1, 10))
                print('\t[---] Слишком много запросов! Делаем брейк-тайм...')
                await asyncio.sleep(random.uniform(10, 30))
        return __wrapper__
    return try_deco_inner


@try_deco(tries=5)
async def get_acc_price(href, session, category_name, funpay_href, params, funpay_acc_price, semaphore):
    """Part of getting account info from steamid.pro"""
    async with semaphore:
        print('\t\t\tПолучаем информацию об аккаунте...')

        data = {'url': href}
        async with session.post(ct.CALCULATOR_URL, data=data) as calculator_r:
            calculator_parser = bs4.BeautifulSoup(await calculator_r.text(), 'lxml')
            block = calculator_parser.find('div', class_='container')
            info_block = block.find('ol').find_next_sibling().find_next_sibling()
            children_list = []
            for children in info_block.children:
                if children.__class__ is bs4.element.Tag:
                    children_list.append(children)
            info_first, info_second = children_list[:2]
            username, info_tab_lst = info_first.find('h1').text.strip(), info_first.find('ul', class_='player-info').find_all('li')
            steam_lvl, acc_age = info_tab_lst[0].text.strip(), info_tab_lst[2].text.strip()
            acc_price_usd = int(info_second.find('span', class_='number-price').text.strip().lstrip('$'))
            rates = ExchangeRates(datetime.now().strftime('%Y-%m-%d'))
            acc_price_rub = int(acc_price_usd * rates['USD'].value)
            profit = acc_price_rub - funpay_acc_price
            profit, funpay_acc_price = str(profit) + '₽', str(funpay_acc_price) + '₽'
            acc_price_usd, acc_price_rub = str(acc_price_usd) + '$', str(acc_price_rub) + '₽'
            bans_block_block = info_block.find_next_sibling()
            children_list_2 = []
            for children in bans_block_block.children:
                if children.__class__ is bs4.element.Tag:
                    children_list_2.append(children)
            bans_block = children_list_2[1]
            ban_table_first, ban_table_second = bans_block.find_all('table')
            bans = ban_table_first.find_all('tr')
            game_bans, vac_bans, community_bans, trade_bans = [i.find_all('td')[1].text.strip() for i in bans]
            hours = ban_table_second.find_all('tr')
            total_hours = hours[0].find_all('td')[1].text.strip()

            result_dict = {
                'params': params,
                'funpay_href': funpay_href,
                'steam_href': href,
                'username': username,
                'steam_lvl': steam_lvl,
                'acc_age': acc_age,
                'acc_price':
                    {
                        'acc_price_usd': acc_price_usd,
                        'acc_price_rub': acc_price_rub
                    },
                'funpay_acc_price': funpay_acc_price,
                'bans':
                    {
                        'game_bans': game_bans,
                        'vac_bans': vac_bans,
                        'community_bans': community_bans,
                        'trade_bans': trade_bans
                    },
                'total_hours': total_hours,
                'profit': profit
            }
        
        json_file_path = f'{ct.PARSE_DATA_FOLDER}{os.sep}{category_name.replace(' ', '_')}.json'

        with open(json_file_path, 'r', encoding='utf-8') as f_r:
            f_read = f_r.read()
            if f_read.strip().replace(' ', ''):
                last_data = json.loads(f_read)
            else:
                last_data = []
        
        with open(json_file_path, 'w', encoding='utf-8') as f_w:
            to_dump = last_data + [result_dict]
            json.dump(fp=f_w, obj=to_dump, ensure_ascii=False, indent=4)


@try_deco(tries=5)
async def parse_offer(href, session, category_name, semaphore):
    """Part of parsing offer page"""
    async with semaphore:
        print('\t\tПарсим предложение...')

        tasks = []

        async with session.get(href) as offer_r:
            offer_parser = bs4.BeautifulSoup(await offer_r.text(), 'lxml')
            params_block = offer_parser.find('div', id='content').find('div', class_='param-list').find('div', class_='row')
            params = {}
            for param in [i for i in params_block.children if i.__class__ is bs4.element.Tag]:
                param = param.find('div', class_='param-item')
                params[param.find('h5').text.strip()] = param.find('div').text.strip()
            short_desc = params_block.find_next_sibling()
            params[short_desc.find('h5').text.strip()] = short_desc.find('div').text.strip()
            desc = short_desc.find_next_sibling().find('div').text.strip()
            steam_hrefs = [i.strip().lower() for i in re.findall(pattern=r'https://steamcommunity.com/.+\s', string=desc)]

            funpay_acc_price = offer_parser.find('div', id='content').find('div', class_='param-list').find('form', action=ct.FUNPAY_ORDER_URL).find('div', class_='form-group hidden').find_next_sibling().find('select').find('option').get('data-content')
            funpay_acc_price = bs4.BeautifulSoup(funpay_acc_price, 'lxml')
            funpay_acc_price = funpay_acc_price.find('span', class_='payment').find('span', class_='payment-value').text.lower().strip()
            funpay_acc_price = int(float(re.search(pattern=r'\b\d+(\s\d+)?(\.\d+)?\b', string=funpay_acc_price).group(0)))

            for steam_href in steam_hrefs:
                tasks.append(get_acc_price(steam_href, session, category_name, href, params, funpay_acc_price, semaphore))
            
            await asyncio.gather(*tasks)


@try_deco(tries=10)
async def parse_category(session, tasks, category_name, category_href, semaphore):
    """Part of parsing category page"""
    count = 1
    try:
        async with session.get(category_href) as category_r:
            category_parser = bs4.BeautifulSoup(await category_r.text(), 'lxml')
            offers = category_parser.find('div', id='content').find('div', class_='tc-header').find_next_siblings()
            offers_hrefs = list(map(lambda x: x.get('href').strip().lower(), offers))
            for offer_href in offers_hrefs:
                tasks.append(asyncio.create_task(parse_offer(offer_href, session, category_name, semaphore)))
                await asyncio.sleep(random.uniform(0, 0.2))
                print(f'\t[+] Задача {count} создана!')
                count += 1
    except AttributeError:
        pass


async def main(data):
    if not os.path.exists(ct.PARSE_DATA_FOLDER):
        os.mkdir(ct.PARSE_DATA_FOLDER)

    headers = {'User-Agent': UserAgent().random}
    async with ClientSession(headers=headers) as session:
        """Part of parsing funpay categories, that need to parse"""
        to_parse_lst = data['to_parse_lst']
        
        flag = False
        
        if data.get('parsed_hrefs') is None:
            flag = True
        else:
            parsed_hrefs = data['parsed_hrefs']

            for to_parse in to_parse_lst:
                if to_parse not in parsed_hrefs.keys():
                    flag = True
                    break

        if flag:
            async with session.get(ct.FUNPAY_URL) as r:
                parsed_hrefs = {}
                
                parser = bs4.BeautifulSoup(await r.text(), 'lxml')
                content = parser.find('div', id='content')
                categories_rows = content.find('div', class_='promo-games promo-games-all').find('div', class_='promo-game-list').find_all('div', class_='row row-10 flex')
                for categories_row in categories_rows:
                    for category in categories_row.children:
                        if category.__class__ is bs4.element.Tag:
                            category_name = category.find('div', class_='game-title').find('a').text.strip().lower()
                            if category_name in to_parse_lst:
                                for li in category.find_all('li'):
                                    if re.fullmatch(pattern=r'.*аккаунт.*', string=li.find('a').text.strip().lower()):
                                        href = li.find('a').get('href').strip().lower()
                                        parsed_hrefs[category_name] = href

                parsed_hrefs = {'parsed_hrefs': parsed_hrefs}

                with open(ct.DATA_FOLDER + os.sep + ct.CONFIG_FILE, 'w', encoding='utf-8') as cfg:
                    json.dump(fp=cfg, obj={**data, **parsed_hrefs}, ensure_ascii=False, indent=4)

                parsed_hrefs = parsed_hrefs['parsed_hrefs']

        """Part of find best offers"""
        tasks = []
        semaphore = asyncio.Semaphore(ct.SEMAPHORE_VALUE)

        for category_name, category_href in parsed_hrefs.items():
            print(f'[INFO] Парсим категорию "{category_name}"...')
            json_file_path = f'{ct.PARSE_DATA_FOLDER}{os.sep}{category_name.replace(' ', '_')}.json'
    
            if os.path.exists(json_file_path):
                os.remove(json_file_path)

            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(fp=f, obj=[], ensure_ascii=False, indent=4)

            await parse_category(session, tasks, category_name, category_href, semaphore)
        
        await asyncio.gather(*tasks)


if __name__ == '__main__':
    data = Starter.start()
    print('[INFO] Запускаем парсинг...')
    asyncio.run(main(data))
