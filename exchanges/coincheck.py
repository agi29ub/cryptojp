#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
from .base.exchange import *
import time
import requests
from datetime import datetime
from urllib.parse import urlencode
import calendar
import hmac
import hashlib
import http.client

COINCHECK_REST_URL = 'coincheck.jp'


class Coincheck(Exchange):
    def __init__(self, apikey, secretkey):
        def httpGet(url, resource, params, apikey, secretkey):
            nonce = int("{:.6f}".format(
                time.time()).replace('.', ''))
            text = str.encode(str(nonce) + "https://" + url +
                              resource + urlencode(params))
            headers = {
                "ACCESS-KEY": apikey,
                "ACCESS-NONCE": str(nonce),
                "ACCESS-SIGN":  hmac.new(str.encode(secretkey), text, hashlib.sha256).hexdigest(),
            }
            return self.session.get('https://' + url + resource,
                                    headers=headers, data=urlencode(params)).json()

        def httpPost(url, resource, params, apikey, secretkey, *args, **kwargs):
            nonce = int("{:.6f}".format(
                time.time()).replace('.', ''))
            text = str.encode(str(nonce) + "https://" + url +
                              resource + urlencode(params))
            headers = {
                "ACCESS-KEY": apikey,
                "ACCESS-NONCE": str(nonce),
                "ACCESS-SIGN":  hmac.new(str.encode(secretkey), text, hashlib.sha256).hexdigest(),
            }
            return self.session.post('https://' + url + resource,
                                     headers=headers, data=urlencode(params)).json()
        super().__init__(apikey, secretkey)
        self.session = requests.session()
        self.httpPost = httpPost
        self.httpGet = httpGet

    def markets(self):
        return ("btc_jpy",)

    def ticker(self, item=''):
        TICKER_RESOURCE = "/api/ticker"
        params = {}
        json = self.session.get('https://' + COINCHECK_REST_URL +
                                TICKER_RESOURCE).json()

        return Ticker(
            timestamp=int(json["timestamp"]),
            last=float(json["last"]),
            bid=float(json["bid"]),
            ask=float(json["ask"]),
            high=float(json["high"]),
            low=float(json["low"]),
            volume=float(json["volume"])
        )

    def board(self, item=''):
        BOARD_RESOURCE = "/api/order_books"
        params = {}
        json = self.session.get('https://' + COINCHECK_REST_URL +
                                BOARD_RESOURCE).json()
        return Board(
            asks=[Ask(price=float(ask[0]), size=float(ask[1]))
                  for ask in json["asks"]],
            bids=[Bid(price=float(bid[0]), size=float(bid[1]))
                  for bid in json["bids"]],
            mid_price=(float(json["asks"][0][0]) +
                       float(json["bids"][0][0])) / 2
        )

    def order(self, item, order_type, side, price, size, *args, **kwargs):
        if item != "btc_jpy":
            return
        ORDER_RESOURCE = "/api/exchange/orders"
        if order_type.lower() == 'market':
            side = 'market_' + side
            if 'buy' in side.lower():
                params = {
                    "pair": item,
                    "order_type": side,
                    "market_buy_amount": size
                }
            else:
                params = {
                    "pair": item,
                    "order_type": side,
                    "amount": size
                }
        else:
            params = {
                "pair": item,
                "order_type": side,
                "rate": price,
                "amount": size
            }
        json = self.httpPost(COINCHECK_REST_URL,
                             ORDER_RESOURCE, params, self._apikey, self._secretkey)
        return json["id"]

    def balance(self):
        BALANCE_RESOURCE = "/api/accounts/balance"
        params = {
        }
        json = self.httpGet(COINCHECK_REST_URL,
                            BALANCE_RESOURCE, params, self._apikey, self._secretkey)
        balances = {}
        balances['JPY'] = [
            float(json['jpy']) + float(json['jpy_reserved']), float(json['jpy'])]
        balances['BTC'] = [
            float(json['btc']) + float(json['btc_reserved']), float(json['btc'])]
        return balances
