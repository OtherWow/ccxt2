import threading
import time
from urllib.parse import quote
from json import dumps
import ccxt
from loguru import logger


# =============================初始化交易所并获取市场行情==================================
def init_exchange(user_main, user_hedge):
    user_main.exchange = ccxt.binance({
        'apiKey': user_main.api_key,
        'secret': user_main.secret,
        'timeout': 30000,  # unified exchange property
        'enableRateLimit': True,
    })
    user_hedge.exchange = ccxt.binance({
        'apiKey': user_hedge.api_key,
        'secret': user_hedge.secret,
        'timeout': 30000,  # unified exchange property
        'enableRateLimit': True,
    })


def 获取交易对规则(user):
    symbol_info = user.exchange.fapiPublicGetExchangeInfo()
    for temp in symbol_info['symbols']:
        if temp['symbol'] == user.symbol:
            user.交易对价格精度 = int(temp['pricePrecision'])
            user.交易对数量精度 = int(temp['quantityPrecision'])
            user.价格保护百分比 = float(temp['triggerProtect'])
    return


def 获取交易对规则2(user_main, user_hedge):
    symbol_info = user_main.exchange.fapiPublicGetExchangeInfo()
    for temp in symbol_info['symbols']:
        if temp['symbol'] == user_main.symbol:
            user_main.交易对价格精度 = int(temp['pricePrecision'])
            user_main.交易对数量精度 = int(temp['quantityPrecision'])
            user_main.价格保护百分比 = float(temp['triggerProtect'])
            user_hedge.交易对价格精度 = int(temp['pricePrecision'])
            user_hedge.交易对数量精度 = int(temp['quantityPrecision'])
            user_hedge.价格保护百分比 = float(temp['triggerProtect'])
            logger.info(f"用户{user_main.name} 的交易对规则为：【交易对价格精度】：{user_main.交易对价格精度} 【交易对数量精度】：{user_main.交易对数量精度} 【价格保护百分比】：{user_main.价格保护百分比}")
            logger.info(f"用户{user_hedge.name} 的交易对规则为：【交易对价格精度】：{user_hedge.交易对价格精度} 【交易对数量精度】：{user_hedge.交易对数量精度} 【价格保护百分比】：{user_hedge.价格保护百分比}")
    return


def get_token(user_main, user_hedge):
    user_main.listen_key = user_main.exchange.fapiPrivatePostListenKey()['listenKey']
    user_hedge.listen_key = user_hedge.exchange.fapiPrivatePostListenKey()['listenKey']
    logger.debug("定时器获得use1-listenKey:" + user_main.listen_key)
    logger.debug("定时器获得use2-listenKey:" + user_hedge.listen_key)
    threading.Timer(60 * 59, get_token, args={user_main, user_hedge}).start()


def get_timestamp():
    return int(round(time.time() * 1000))


# 先下对冲单，对冲单根据信号开单
def sign1(sign_data, user_main, user_hedge):
    # 根据信号开仓
    查询账户持仓情况(user_main)
    查询账户持仓情况(user_hedge)
    if user_main.position_amt > 0 or user_hedge.position_amt > 0:
        logger.info("收到信号" + str(sign_data['type']) + ",但是主账户已持仓" + str(user_main.position_amt) + " 或 对冲单已持仓" + str(
            user_hedge.position_amt) + "，忽略本次信号。对冲单持仓数量：" + str(
            user_hedge.position_amt) + " 对冲单持仓价格：" + str(user_hedge.entry_price) + " 当前价格：" + str(user_hedge.now_price))
        return
    # 对冲单开首单
    if sign_data['type'] == 'sell':
        logger.info(user_hedge.name + "收到信号" + str(sign_data['type']) + "对冲单开始做空开仓 当前价格：" + str(user_hedge.now_price))
        user_hedge.position_side = 'SHORT'
        user_main.position_side = 'LONG'
        撤销所有订单(user_hedge)
        市价单(user_hedge, user_hedge.首单数量, "SELL")
        time.sleep(2)
        查询账户持仓情况(user_hedge)
        user_hedge.首单价值 = user_hedge.position_amt * user_hedge.entry_price
        user_main.马丁触发价格 = user_hedge.entry_price * (1 - user_hedge.对冲单价格变动百分比触发马丁)
        止盈止损单(user_hedge)
        logger.info(user_hedge.name + "对冲单已做空开仓 持仓数量：" + str(
            user_hedge.position_amt) + " 持仓价格：" + str(user_hedge.entry_price) + " 对冲单首单价值：" + str(
            user_hedge.首单价值) + "马丁触发价格：" + str(user_main.马丁触发价格))
        return

    elif sign_data['type'] == 'buy':
        logger.info(user_hedge.name + "收到信号" + str(sign_data['type']) + "对冲单开始做多开仓 当前价格：" + str(user_hedge.now_price))
        user_hedge.position_side = 'LONG'
        user_main.position_side = 'SHORT'
        撤销所有订单(user_hedge)
        市价单(user_hedge, user_hedge.首单数量, "BUY")
        time.sleep(2)
        查询账户持仓情况(user_hedge)
        user_hedge.首单价值 = user_hedge.position_amt * user_hedge.entry_price
        user_main.马丁触发价格 = user_hedge.entry_price * (1 + user_hedge.对冲单价格变动百分比触发马丁)
        止盈止损单(user_hedge)
        logger.info(user_hedge.name + "对冲单已做多开仓 持仓数量：" + str(
            user_hedge.position_amt) + " 持仓价格：" + str(user_hedge.entry_price) + " 对冲单首单价值：" + str(
            user_hedge.首单价值) + "马丁触发价格：" + str(user_main.马丁触发价格))
        return


def 马丁开首单(user_main, user_hedge):
    查询账户持仓情况(user_main)
    查询账户持仓情况(user_hedge)
    if user_main.position_amt == 0 and user_hedge.position_amt > 0:
        user_main.马丁触发价格 = 0
        撤销所有订单(user_main)
        if user_main.position_side == 'SHORT':
            市价单(user_main, user_main.首单数量, 'SELL')
        if user_main.position_side == 'LONG':
            市价单(user_main, user_main.首单数量, 'BUY')
        time.sleep(2)
        查询账户持仓情况(user_main)
        user_main.首单价值 = user_main.position_amt * user_main.entry_price
        止盈止损单(user_main)
        查询账户持仓情况(user_hedge)
        logger.debug("开始下对冲但止盈单,触发价:" + str(user_main.对冲单平仓触发价) + "委托价:" + str(user_main.对冲单平仓委托价) + " 当前价格：" + str(
            user_hedge.now_price) + " 仓位价格：" + str(user_hedge.entry_price))
        try:
            限价止盈单(user_hedge, (user_hedge.now_price + user_main.对冲单平仓委托价) / 2, user_main.对冲单平仓委托价)
        except Exception as e:
            logger.error(user_hedge.name + "限价止盈单异常:" + str(e))

        查询账户持仓情况(user_main)
        # 开始循环下限价单
        if user_main.position_side == 'SHORT':
            num = user_main.首次补仓数量
            last_percent = 0
            for i in range(user_main.最大补仓次数):
                last_percent = user_main.补仓价格百分比例 / 100 + last_percent * user_main.补仓价格倍数
                price = user_main.entry_price * (1 + last_percent)
                try:
                    限价单(user_main, num, price, 'SELL')
                except Exception as e:
                    logger.error(
                        user_main.name + "第{}次限价单下单出错 ".format(i + 1) + str(e) + " 价格：" + str(price) + " 数量：" + str(
                            num))
                num = num * user_main.补仓倍数
        if user_main.position_side == 'LONG':
            num = user_main.首次补仓数量
            last_percent = 0
            for i in range(user_main.最大补仓次数):
                last_percent = user_main.补仓价格百分比例 / 100 + last_percent * user_main.补仓价格倍数
                price = user_main.entry_price * (1 - last_percent)
                try:
                    限价单(user_main, num, price, 'BUY')
                except Exception as e:
                    logger.error(
                        user_main.name + "第{}次限价单下单出错 ".format(i + 1) + str(e) + " 价格：" + str(price) + " 数量：" + str(
                            num))
                num = num * user_main.补仓倍数
    else:
        user_main.马丁触发价格 = 0
        return


@logger.catch()
def 双马丁策略(user_main, user_hedge):
    查询账户持仓情况(user_main)
    查询账户持仓情况(user_hedge)
    if user_hedge.position_amt > 0:
        市价平仓(user_hedge)
        time.sleep(2)
        查询账户持仓情况(user_hedge)
    if user_main.position_amt == 0 and user_hedge.position_amt == 0:
        撤销所有订单(user_main)
        撤销所有订单(user_hedge)
        user_main.马丁补单当前索引 = 0
        user_main.马丁补单单号字典 = {}
        if user_main.position_side == 'SHORT':
            市价单(user_main, user_main.首单数量, 'SELL')
        if user_main.position_side == 'LONG':
            市价单(user_main, user_main.首单数量, 'BUY')
        time.sleep(2)
        查询账户持仓情况(user_main)
        user_main.首单价值 = user_main.position_amt * user_main.entry_price
        止盈止损单(user_main)
        # 开始循环下限价单
        if user_main.position_side == 'SHORT':
            num = user_main.首次补仓数量
            last_percent = 0
            for i in range(user_main.最大补仓次数):
                last_percent = user_main.补仓价格百分比例 / 100 + last_percent * user_main.补仓价格倍数
                price = user_main.entry_price * (1 + last_percent)
                try:
                    限价单(user_main, num, price, 'SELL')
                    user_main.马丁补单单号字典[i] = user_main.order_info['orderId']
                except Exception as e:
                    logger.error(
                        user_main.name + "第{}次限价单下单出错 ".format(i + 1) + " 价格：" + str(price) + " 数量：" + str(
                            num) + str(e))
                num = num * user_main.补仓倍数
        if user_main.position_side == 'LONG':
            num = user_main.首次补仓数量
            last_percent = 0
            for i in range(user_main.最大补仓次数):
                last_percent = user_main.补仓价格百分比例 / 100 + last_percent * user_main.补仓价格倍数
                price = user_main.entry_price * (1 - last_percent)
                try:
                    限价单(user_main, num, price, 'BUY')
                    user_main.马丁补单单号字典[i] = user_main.order_info['orderId']
                except Exception as e:
                    logger.error(
                        user_main.name + "第{}次限价单下单出错 ".format(i + 1) + " 价格：" + str(price) + " 数量：" + str(
                            num) + str(e))
                num = num * user_main.补仓倍数
    else:
        logger.info(user_main.name + " 持仓数量：" + str(user_main.position_amt) + " 持仓价格：" + str(
            user_main.entry_price) + "=】【=" + user_hedge.name + " 持仓数量：" + str(
            user_hedge.position_amt) + " 持仓价格：" + str(user_hedge.entry_price) + " 仓位不为0,无法开单")

def 对冲马丁(user):
    查询账户持仓情况(user)
    if user.position_amt == 0:
        撤销所有订单(user)
        if user.position_side == 'SHORT':
            市价单(user, user.首单数量, 'SELL')
        if user.position_side == 'LONG':
            市价单(user, user.首单数量, 'BUY')
        time.sleep(2)
        查询账户持仓情况(user)
        user.首单价值 = user.position_amt * user.entry_price
        止盈止损单(user)
        # 开始循环下限价单
        if user.position_side == 'SHORT':
            num = user.首次补仓数量
            last_percent = 0
            for i in range(user.最大补仓次数):
                last_percent = user.补仓价格百分比例 / 100 + last_percent * user.补仓价格倍数
                price = user.entry_price * (1 + last_percent)
                try:
                    限价单(user, num, price, 'SELL')
                except Exception as e:
                    logger.error(
                        user.name + "第{}次限价单下单出错 ".format(i + 1) + " 价格：" + str(price) + " 数量：" + str(
                            num) + str(e))
                num = num * user.补仓倍数
        if user.position_side == 'LONG':
            num = user.首次补仓数量
            last_percent = 0
            for i in range(user.最大补仓次数):
                last_percent = user.补仓价格百分比例 / 100 + last_percent * user.补仓价格倍数
                price = user.entry_price * (1 - last_percent)
                try:
                    限价单(user, num, price, 'BUY')
                except Exception as e:
                    logger.error(
                        user.name + "第{}次限价单下单出错 ".format(i + 1) + " 价格：" + str(price) + " 数量：" + str(
                            num) + str(e))
                num = num * user.补仓倍数
    else:
        logger.info(user.name + "账户持仓不为0,无法开单，持仓数量:" + str(user.position_amt) + " 持仓价格:" + str(user.entry_price))
        return

def 马丁(user):
    查询账户持仓情况(user)
    if user.position_amt == 0:
        撤销所有订单(user)
        if user.position_side == 'SHORT':
            市价单(user, user.首单数量, 'SELL')
        if user.position_side == 'LONG':
            市价单(user, user.首单数量, 'BUY')
        time.sleep(2)
        查询账户持仓情况(user)
        user.首单价值 = user.position_amt * user.entry_price
        止盈止损单(user)
        # 开始循环下限价单
        if user.position_side == 'SHORT':
            num = user.首次补仓数量
            last_percent = 0
            for i in range(user.最大补仓次数):
                last_percent = user.补仓价格百分比例 / 100 + last_percent * user.补仓价格倍数
                price = user.entry_price * (1 + last_percent)
                try:
                    限价单(user, num, price, 'SELL')
                except Exception as e:
                    logger.error(
                        user.name + "第{}次限价单下单出错 ".format(i + 1) + " 价格：" + str(price) + " 数量：" + str(
                            num) + str(e))
                num = num * user.补仓倍数
        if user.position_side == 'LONG':
            num = user.首次补仓数量
            last_percent = 0
            for i in range(user.最大补仓次数):
                last_percent = user.补仓价格百分比例 / 100 + last_percent * user.补仓价格倍数
                price = user.entry_price * (1 - last_percent)
                try:
                    限价单(user, num, price, 'BUY')
                except Exception as e:
                    logger.error(
                        user.name + "第{}次限价单下单出错 ".format(i + 1) + " 价格：" + str(price) + " 数量：" + str(
                            num) + str(e))
                num = num * user.补仓倍数
    else:
        logger.info(user.name + "账户持仓不为0,无法开单，持仓数量:" + str(user.position_amt) + " 持仓价格:" + str(user.entry_price))
        return


@logger.catch()
def 查询账户持仓情况(user):
    # =============================查询账户持仓情况==================================
    account_info = user.exchange.fapiPrivateV2GetAccount({"timestamp": get_timestamp()})
    for temp in account_info['assets']:
        if user.trade_currency in temp['asset']:
            user.wallet_balance = float(temp['walletBalance'])
            logger.info(user.name + " 账户余额: " + str(user.wallet_balance) + " " + user.trade_currency)
            break
    for temp in account_info['positions']:
        if user.symbol in temp['symbol']:
            user.entry_price = float(temp['entryPrice'])  # 仓位价格
            user.initial_margin = float(temp['initialMargin'])  # 当前所需起始保证金
            user.position_amt = abs(float(temp['positionAmt']))  # 持仓数量
            user.real_position_amt = float(temp['positionAmt'])  # 实际持仓数量
            if user.position_amt == 0:
                user.cover_statistics = 0
            elif user.cover_statistics == 0:
                user.cover_statistics = 1
            logger.info(user.name + " 账户【" + user.symbol + "】持仓情况=> 仓位数量：" + str(
                user.real_position_amt) + " " + user.symbol + " 仓位价格:" + str(
                user.entry_price) + " " + user.trade_currency + " 当前所需起始保证金:" + str(
                user.initial_margin) + " " + user.trade_currency)
            logger.debug(temp)
            break


@logger.catch()
def 查询当前所有挂单(user):
    order_info = user.exchange.fapiPrivateGetOpenOrders({
        'symbol': user.symbol,
        'timestamp': get_timestamp(),
    })
    logger.debug(user.name + "查询当前所有挂单=>" + str(order_info))


@logger.catch()
def 市价平仓(user):
    if user.real_position_amt > 0:
        user.order_info = user.exchange.fapiPrivatePostOrder({
            'symbol': user.symbol,  # luna
            'side': 'SELL',  # 买入平仓
            'type': 'MARKET',  # 市价单
            'quantity': round(float(user.position_amt), 6)
        })
    elif user.real_position_amt < 0:
        user.order_info = user.exchange.fapiPrivatePostOrder({
            'symbol': user.symbol,  # luna
            'side': 'BUY',  # 买入平仓
            'type': 'MARKET',  # 市价单
            'quantity': round(float(user.position_amt), 6)
        })
    logger.debug("市价平仓=>" + str(user.order_info))
    logger.info(user.name + "市价平仓成功！平仓数量：{:6f}".format(user.position_amt) + " 市价单价格：{:.6f}".format(user.now_price))


@logger.catch()
def 市价单(user, num, side):
    user.order_info = user.exchange.fapiPrivatePostOrder({
        'symbol': user.symbol,
        'side': side,
        'type': 'MARKET',  # 限价单
        'quantity': round(num, user.交易对数量精度),  # 数量
        'timestamp': get_timestamp(),
    })
    logger.debug("市价单=>" + str(user.order_info))
    if side == 'BUY':
        方向 = "买入"
    else:
        方向 = "卖出"
    logger.info(user.name + "市价单下单成功！市价单数量：{:6f}".format(num) + " 市价单价格：{:.6f}".format(user.now_price) + "方向：" + 方向)


@logger.catch()
def 限价单(user, num, price, side):
    user.order_info = user.exchange.fapiPrivatePostOrder({
        'symbol': user.symbol,
        'side': side,
        'type': 'LIMIT',  # 限价单
        'quantity': round(num, user.交易对数量精度),  # 数量
        'price': round(price, user.交易对价格精度),  # 价格
        'timestamp': get_timestamp(),
        'timeInForce': "GTC",
    })
    user.限价单订单簿.append(user.order_info['orderId'])
    if side == 'BUY':
        方向 = "买入"
    else:
        方向 = "卖出"
    logger.info(
        user.name + "限价单下单成功！限价单数量：{:6f}".format(num) + " 限价单价格：{:.6f}".format(price) + "方向：" + 方向 + " 当前价格：" + str(
            user.now_price))


@logger.catch()
def 限价止损单(user, 触发价, 委托价):
    if user.position_side == 'SHORT':
        user.order_info = user.exchange.fapiPrivatePostOrder({
            'symbol': user.symbol,
            'side': 'BUY',  # 买入平仓
            'type': 'STOP',  # 限价止损
            'quantity': round(user.position_amt, user.交易对数量精度),
            'stopPrice': round(触发价, user.交易对价格精度),
            "price": round(委托价, user.交易对价格精度),
            'priceProtect': 'TRUE',
        })
        logger.info(user.name + "限价止损单下单成功！触发价:" + str(触发价) + " 委托价：" + str(委托价) + " 当前价格:" + str(
            user.now_price) + " 首单价值：" + str(user.首单价值) + "方向：买入")
    if user.position_side == 'LONG':
        user.order_info = user.exchange.fapiPrivatePostOrder({
            'symbol': user.symbol,
            'side': 'SELL',  # 卖出平仓
            'type': 'STOP',  # 限价止损
            'quantity': round(user.position_amt, user.交易对数量精度),
            'stopPrice': round(触发价, user.交易对价格精度),
            "price": round(委托价, user.交易对价格精度),
            'priceProtect': 'TRUE',
        })
        logger.info(user.name + "限价止损单下单成功！触发价:" + str(触发价) + " 委托价：" + str(委托价) + " 当前价格:" + str(
            user.now_price) + " 首单价值：" + str(user.首单价值) + "方向：卖出")


@logger.catch()
def 市价止损单(user, 委托价):
    if user.position_side == 'SHORT':
        user.order_info = user.exchange.fapiPrivatePostOrder({
            'symbol': user.symbol,
            'side': 'BUY',  # 买入平仓
            'type': 'STOP_MARKET',  # 市价止损
            'closePosition': 'TRUE',
            'stopPrice': round(委托价, user.交易对价格精度),
            'priceProtect': 'TRUE',
        })
        logger.info(user.name + "市价止损单下单成功！ 委托价：" + str(委托价) + " 当前价格:" + str(
            user.now_price) + " 首单价值：" + str(user.首单价值) + "方向：买入")
    if user.position_side == 'LONG':
        user.order_info = user.exchange.fapiPrivatePostOrder({
            'symbol': user.symbol,
            'side': 'SELL',  # 卖出平仓
            'type': 'STOP_MARKET',  # 市价止损
            'closePosition': 'TRUE',
            'stopPrice': round(委托价, user.交易对价格精度),
            'priceProtect': 'TRUE',
        })
        logger.info(user.name + "市价止损单下单成功！ 委托价：" + str(委托价) + " 当前价格:" + str(
            user.now_price) + " 首单价值：" + str(user.首单价值) + "方向：卖出")


@logger.catch()
def 限价止盈单(user, 触发价, 委托价):
    if user.position_side == 'SHORT':
        user.order_info = user.exchange.fapiPrivatePostOrder({
            'symbol': user.symbol,
            'side': 'BUY',  # 买入平仓
            'type': 'TAKE_PROFIT',  # 限价止损
            'quantity': round(user.position_amt, user.交易对数量精度),
            'stopPrice': round(触发价, user.交易对价格精度),
            "price": round(委托价, user.交易对价格精度),
            'priceProtect': 'TRUE',
        })
        logger.info(user.name + "限价止盈单下单成功！触发价:" + str(触发价) + " 委托价：" + str(委托价) + " 当前价格:" + str(
            user.now_price) + " 首单价值：" + str(user.首单价值) + "方向：买入")
    if user.position_side == 'LONG':
        user.order_info = user.exchange.fapiPrivatePostOrder({
            'symbol': user.symbol,
            'side': 'SELL',  # 卖出平仓
            'type': 'TAKE_PROFIT',  # 限价止损
            'quantity': round(user.position_amt, user.交易对数量精度),
            'stopPrice': round(触发价, user.交易对价格精度),
            "price": round(委托价, user.交易对价格精度),
            'priceProtect': 'TRUE',
        })
        logger.info(user.name + "限价止盈单下单成功！触发价:" + str(触发价) + " 委托价：" + str(委托价) + " 当前价格:" + str(
            user.now_price) + " 首单价值：" + str(user.首单价值) + "方向：卖出")


@logger.catch()
def 市价止盈单(user, 委托价):
    if user.position_side == 'SHORT':
        user.order_info = user.exchange.fapiPrivatePostOrder({
            'symbol': user.symbol,
            'side': 'BUY',  # 买入平仓
            'type': 'TAKE_PROFIT_MARKET',  # 市价止损
            'closePosition': 'TRUE',
            'stopPrice': round(委托价, user.交易对价格精度),
            'priceProtect': 'TRUE',
        })
        logger.info(user.name + "市价止盈单下单成功！ 委托价：" + str(委托价) + " 当前价格:" + str(
            user.now_price) + " 首单价值：" + str(user.首单价值) + "方向：买入")
    if user.position_side == 'LONG':
        user.order_info = user.exchange.fapiPrivatePostOrder({
            'symbol': user.symbol,
            'side': 'SELL',  # 卖出平仓
            'type': 'TAKE_PROFIT_MARKET',  # 市价止损
            'closePosition': 'TRUE',
            'stopPrice': round(委托价, user.交易对价格精度),
            'priceProtect': 'TRUE',
        })
        logger.info(user.name + "市价止盈单下单成功！ 委托价：" + str(委托价) + " 当前价格:" + str(
            user.now_price) + " 首单价值：" + str(user.首单价值) + "方向：卖出")


@logger.catch()
def 止盈止损单(user):
    查询账户持仓情况(user)
    try:
        批量撤销订单(user, user.止盈止损订单簿)
        user.止盈止损订单簿 = []
    except Exception as e:
        logger.error(user.name + '撤销止盈止损单失败!' + str(e))
    委托价 = 0.0
    触发价 = 0.0
    if user.position_amt > 0:
        if user.开启止损:
            止损百分比 = 0.0
            if user.position_amt == user.首单数量:
                止损百分比 = user.首单止损百分比
            else:
                止损百分比 = user.止损百分比
            if user.止损类型 == 1:  # 0 固定金额止损  1 百分比止损
                if user.止损相对于首单:
                    user.止损总金额 = (止损百分比 / 100) * user.首单价值
                else:
                    user.止损总金额 = (止损百分比 / 100) * (user.position_amt * user.entry_price)
            # =============================计算止损价格==================================
            if user.position_side == 'SHORT':
                # 做空时的止损价格计算： （当前价格-仓位价格+0.0006*当前价格）仓位数量 = 预估损失
                委托价 = (user.止损总金额 / user.position_amt + user.entry_price) / (1 + user.限价手续费率 + user.市价手续费率)
                触发价 = (委托价 + user.now_price) / 2
            if user.position_side == 'LONG':
                # 做多时的止损价格计算： （仓位价格-当前价格+0.0006*当前价格）仓位数量 = 预估损失
                委托价 = (user.entry_price - user.止损总金额 / user.position_amt) / (1 - user.限价手续费率 - user.市价手续费率)
                触发价 = (委托价 + user.now_price) / 2
            try:
                限价止损单(user, 触发价, 委托价)
            except Exception as e:
                logger.error(user.name + "限价止损单发送失败！开始下市价止损单！触发价:" + str(触发价) + " 委托价：" + str(委托价) + " 当前价格:" + str(
                    user.now_price) + " 首单价值：" + str(user.首单价值) + str(e))
                市价止损单(user, 委托价)
            user.止盈止损订单簿.append(user.order_info['orderId'])
            user.止损单号 = user.order_info['orderId']
            logger.info(user.name + "下单标记止损单,止损价格：{:.4f}".format(委托价) + " 预估损失：" + str(
                user.止损总金额) + " 当前仓位价格： {:.4f}".format(
                user.entry_price) + " 当前仓位数量：{:.4f}".format(user.position_amt))
        if user.开启止盈:
            止盈百分比 = 0.0
            if user.position_amt == user.首单数量:
                止盈百分比 = user.首单止盈百分比
            else:
                止盈百分比 = user.止盈百分比
            if user.止盈类型 == 1:  # 0 固定金额止盈  1 百分比止盈
                if user.止盈相对于首单:
                    user.止盈总金额 = (止盈百分比 / 100) * user.首单价值
                else:
                    user.止盈总金额 = (止盈百分比 / 100) * (user.position_amt * user.entry_price)
            # =============================计算止盈价格==================================
            if user.position_side == 'SHORT':
                # 做空时的止盈价格计算： （仓位价格-当前价格-0.0006*当前价格）仓位数量 = 预估盈利
                委托价 = (user.entry_price - user.止盈总金额 / user.position_amt) / (1 + user.限价手续费率 + user.市价手续费率)
                触发价 = (委托价 + user.now_price) / 2
            if user.position_side == 'LONG':
                # 做多时的止盈价格计算： （当前价格-仓位价格-0.0006*当前价格）仓位数量 = 预估损失
                委托价 = (user.止盈总金额 / user.position_amt + user.entry_price) / (1 - user.限价手续费率 - user.市价手续费率)
                触发价 = (委托价 + user.now_price) / 2
            try:
                user.对冲单平仓委托价 = 委托价
                user.对冲单平仓触发价 = 触发价
                限价止盈单(user, 触发价, 委托价)
            except Exception as e:
                logger.error(user.name + "限价止盈单发送失败！开始下市价止盈单！触发价:" + str(触发价) + " 委托价：" + str(委托价) + " 当前价格:" + str(
                    user.now_price) + " 首单价值：" + str(user.首单价值) + str(e))
                市价止盈单(user, 委托价)
            user.止盈止损订单簿.append(user.order_info['orderId'])
            user.止盈单号 = user.order_info['orderId']
            logger.info(
                user.name + "已下单标记止盈单,止盈价格：{:.4f}".format(委托价) + " 预估盈利：" + str(
                    user.止盈总金额) + " 当前仓位价格： {:.4f}".format(
                    user.entry_price) + " 当前仓位数量：{:.4f}".format(user.position_amt))


@logger.catch()
def 撤销所有订单(user):
    user.exchange.fapiPrivate_delete_allopenorders({
        'symbol': user.symbol,
        'timestamp': get_timestamp()
    })
    user.止盈止损订单簿 = []
    user.限价单订单簿 = []
    logger.debug(user.name + "撤销所有订单成功！")


@logger.catch()
def 批量撤销订单(user, order_book):
    if len(order_book) > 0:
        idsString = dumps(order_book).replace(" ", "")
        idsString = quote(idsString)
        user.exchange.fapiPrivateDeleteBatchOrders({
            'symbol': user.symbol,
            'orderIdList': idsString,
            'timestamp': get_timestamp()
        })
        logger.debug("idsString:" + str(idsString))
        logger.info(user.name + "批量撤销订单成功！ 订单号：" + str(order_book))
