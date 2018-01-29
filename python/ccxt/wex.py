# -*- coding: utf-8 -*-

from ccxt.liqui import liqui
import json
from ccxt.base.errors import ExchangeError
from ccxt.base.errors import InsufficientFunds
from ccxt.base.errors import OrderNotFound
from ccxt.base.errors import DDoSProtection


class wex (liqui):

    def describe(self):
        return self.deep_extend(super(wex, self).describe(), {
            'id': 'wex',
            'name': 'WEX',
            'countries': 'NZ',  # New Zealand
            'version': '3',
            'has': {
                'CORS': False,
                'fetchTickers': True,
            },
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/30652751-d74ec8f8-9e31-11e7-98c5-71469fcef03e.jpg',
                'api': {
                    'public': 'https://wex.nz/api',
                    'private': 'https://wex.nz/tapi',
                },
                'www': 'https://wex.nz',
                'doc': [
                    'https://wex.nz/api/3/docs',
                    'https://wex.nz/tapi/docs',
                ],
                'fees': 'https://wex.nz/fees',
            },
            'api': {
                'public': {
                    'get': [
                        'info',
                        'ticker/{pair}',
                        'depth/{pair}',
                        'trades/{pair}',
                    ],
                },
                'private': {
                    'post': [
                        'getInfo',
                        'Trade',
                        'ActiveOrders',
                        'OrderInfo',
                        'CancelOrder',
                        'TradeHistory',
                        'TransHistory',
                        'CoinDepositAddress',
                        'WithdrawCoin',
                        'CreateCoupon',
                        'RedeemCoupon',
                    ],
                },
            },
            'fees': {
                'trading': {
                    'maker': 0.2 / 100,
                    'taker': 0.2 / 100,
                },
                'funding': {
                    'withdraw': {
                        'BTC': 0.001,
                        'LTC': 0.001,
                        'NMC': 0.1,
                        'NVC': 0.1,
                        'PPC': 0.1,
                        'DASH': 0.001,
                        'ETH': 0.003,
                        'BCH': 0.001,
                        'ZEC': 0.001,
                    },
                },
            },
            'exceptions': {
                'messages': {
                    'bad status': OrderNotFound,
                    'Requests too often': DDoSProtection,
                    'not available': DDoSProtection,
                    'external service unavailable': DDoSProtection,
                },
            },
        })

    def parse_ticker(self, ticker, market=None):
        timestamp = ticker['updated'] * 1000
        symbol = None
        if market:
            symbol = market['symbol']
        return {
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'high': self.safe_float(ticker, 'high'),
            'low': self.safe_float(ticker, 'low'),
            'bid': self.safe_float(ticker, 'sell'),
            'ask': self.safe_float(ticker, 'buy'),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': self.safe_float(ticker, 'last'),
            'change': None,
            'percentage': None,
            'average': self.safe_float(ticker, 'avg'),
            'baseVolume': self.safe_float(ticker, 'vol_cur'),
            'quoteVolume': self.safe_float(ticker, 'vol'),
            'info': ticker,
        }

    def handle_errors(self, code, reason, url, method, headers, body):
        if code == 200:
            if body[0] != '{':
                # response is not JSON -> resort to default error handler
                return
            response = json.loads(body)
            if 'success' in response:
                if not response['success']:
                    error = self.safe_string(response, 'error')
                    if not error:
                        raise ExchangeError(self.id + ' returned a malformed error: ' + body)
                    if error == 'no orders':
                        # returned by fetchOpenOrders if no open orders(fix for  #489) -> not an error
                        return
                    feedback = self.id + ' ' + self.json(response)
                    messages = self.exceptions.messages
                    if error in messages:
                        raise messages[error](feedback)
                    if error.find('It is not enough') >= 0:
                        raise InsufficientFunds(feedback)
                    else:
                        raise ExchangeError(feedback)
