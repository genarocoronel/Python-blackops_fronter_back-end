import asyncio
from aiohttp import ClientSession, BasicAuth

from bs4 import BeautifulSoup as BS4


async def get_report(username, password):
    # BASIC AUTH
    ba = BasicAuth('documentservicesolutions', 'grapackerown')

    async with ClientSession() as session:
        async with session.get('https://stage-sc.consumerdirect.com/login/',
                               auth=ba) as response:
            csrf_token = (await response.text()).split('_csrf" value="')[1].split('"/>')[0]

        form_data = {
            '_csrf': csrf_token,
            'loginType': 'CUSTOMER',
            'j_username': username,
            'j_password': password
        }
        async with session.post('https://stage-sc.consumerdirect.com/login',
                                data=form_data,
                                auth=ba) as response:
            await response.read()

        async with session.get('https://stage-sc.consumerdirect.com/member/credit-report/3b/',
                               auth=ba) as response:
            pdt = (await response.text()).split('cc2-test.sd.demo.truelink.com/dsply.aspx?pdt=')[1].split('&xsl')[0]

        async with session.get('https://cc2-test.sd.demo.truelink.com/dsply.aspx?'
                               f'pdt={pdt}&'
                               'xsl=CC2CONSUMERDIRECT_3BREPORTVANTAGE3SCORE_JS',
                               auth=ba) as response:
            soup = BS4((await response.text()), 'html.parser')


"""
debt_name       <td class="crWhiteTradelineHeader"><b>JPMCB CARD</b></td>
creditor        same as debt_name
type            7+ types of loans
ecoa            <td class="accountHistoryColorRow">Individual</td>
account_number  <td>585637245464**** 
push            NO
last_collector 
"""


def scrap_table(html):
    soup = BS4(html, 'html.parser')
    tables = soup.findAll('table', attrs={'border': '1',
                                          'cellspacing': '0',
                                          'cellpadding': '0',
                                          'xmlns:d1p1': 'com/truelink/ds/sch/report/truelink/v3',
                                          'bordercolor': '#eeeeee'})
    for table in tables:
        crwtlh = table.findAll('td', {'class': 'crWhiteTradelineHeader'})
        if len(crwtlh) == 3:
            row = dict()
            print('============================================================')
            row['debt_name'] = row['creditor'] = crwtlh[1].text
            row['push'] = 'No'
            for tr in table.find('table', {'class': 'crLightTableBackground'}).findAll('tr'):
                tds = tr.findAll('td')
                b = tds[0].find('b')
                if b:
                    print(tds[0].find('b').string)
                    for td in tds[1:]:
                        if '--' not in td.string:
                            if b.string == 'Account #:':
                                row['account_number'] = td.string.strip()
                            print(td.string.strip())

            print()
    print(len(tables))


async def test():
    with open('smc1.html', 'r', encoding='latin-1') as file:
        scrap_table(file)


asyncio.get_event_loop().run_until_complete(test())
