import threading
import time
from urllib.parse import quote
from json import dumps
import ccxt
from loguru import logger
import http.client
import os

# =============================初始化交易所并获取市场行情==================================
from grid.gridBot import Grid
from user.account import Account


def init_exchange(user_main: Account, user_hedge: Account):
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


def 获取交易对规则2(user_main: Account, user_hedge: Account):
    symbol_info = user_main.exchange.fapiPublicGetExchangeInfo()
    for temp in symbol_info['symbols']:
        if temp['symbol'] == user_main.symbol:
            user_main.交易对价格精度 = int(temp['pricePrecision'])
            user_main.交易对数量精度 = int(temp['quantityPrecision'])
            user_main.价格保护百分比 = float(temp['triggerProtect'])
            user_hedge.交易对价格精度 = int(temp['pricePrecision'])
            user_hedge.交易对数量精度 = int(temp['quantityPrecision'])
            user_hedge.价格保护百分比 = float(temp['triggerProtect'])
            logger.info(
                f"用户{user_main.name} 的交易对规则为：【交易对价格精度】：{user_main.交易对价格精度} 【交易对数量精度】：{user_main.交易对数量精度} 【价格保护百分比】：{user_main.价格保护百分比}")
            logger.info(
                f"用户{user_hedge.name} 的交易对规则为：【交易对价格精度】：{user_hedge.交易对价格精度} 【交易对数量精度】：{user_hedge.交易对数量精度} 【价格保护百分比】：{user_hedge.价格保护百分比}")
    return


def get_token(user_main: Account, user_hedge: Account):
    user_main.listen_key = user_main.exchange.fapiPrivatePostListenKey()['listenKey']
    user_hedge.listen_key = user_hedge.exchange.fapiPrivatePostListenKey()['listenKey']
    logger.debug("定时器获得use1-listenKey:" + user_main.listen_key)
    logger.debug("定时器获得use2-listenKey:" + user_hedge.listen_key)
    threading.Timer(60 * 59, get_token, args={user_main, user_hedge}).start()


def get_timestamp():
    return int(round(time.time() * 1000))


def get_webserver_time():
    conn = http.client.HTTPConnection('www.baidu.com')
    conn.request("GET", "/")
    r = conn.getresponse()
    # r.getheaders() #获取所有的http头
    ts = r.getheader('date')  # 获取http头date部分
    # 将GMT时间转换成北京时间
    ltime = time.strptime(ts[5:25], "%d %b %Y %H:%M:%S")
    print(ltime)
    ttime = time.localtime(time.mktime(ltime) + 8 * 60 * 60)
    print(ttime)
    dat = "date %u-%02u-%02u" % (ttime.tm_year, ttime.tm_mon, ttime.tm_mday)
    tm = "time %02u:%02u:%02u" % (ttime.tm_hour, ttime.tm_min, ttime.tm_sec)
    print(dat, tm)
    os.system(dat)
    os.system(tm)


@logger.catch()
def 查询账户持仓情况(user: Account):
    # =============================查询账户持仓情况==================================
    account_info = user.exchange.fapiPrivateV2GetAccount({"timestamp": get_timestamp()})
    for temp in account_info['assets']:
        if user.trade_currency in temp['asset']:
            user.wallet_balance = float(temp['walletBalance'])
            logger.info(
                user.name + "【" + user.symbol + "】 账户余额: " + str(user.wallet_balance) + " " + user.trade_currency)
            break
    for temp in account_info['positions']:
        if user.symbol == temp['symbol']:
            user.entry_price = float(temp['entryPrice'])  # 仓位价格
            user.initial_margin = float(temp['initialMargin'])  # 当前所需起始保证金
            user.position_amt = abs(float(temp['positionAmt']))  # 持仓数量
            user.real_position_amt = float(temp['positionAmt'])  # 实际持仓数量
            if user.position_amt == 0:
                user.cover_statistics = 0
            elif user.cover_statistics == 0:
                user.cover_statistics = 1
            logger.info(user.name + "【" + user.symbol + "】 账户【" + user.symbol + "】持仓情况=> 仓位数量：" + str(
                user.real_position_amt) + " " + user.symbol + " 仓位价格:" + str(
                user.entry_price) + " " + user.trade_currency + " 当前所需起始保证金:" + str(
                user.initial_margin) + " " + user.trade_currency)
            logger.debug(temp)
            break


@logger.catch()
def 查询当前所有挂单(user: Account):
    order_info = user.exchange.fapiPrivateGetOpenOrders({
        'symbol': user.symbol,
        'timestamp': get_timestamp(),
    })
    logger.debug(user.name + "【" + user.symbol + "】查询当前所有挂单=>" + str(order_info))
    return order_info


@logger.catch()
def 查询当前所有挂单NoSymbol(user: Account):
    order_info = user.exchange.fapiPrivateGetOpenOrders({
        'timestamp': get_timestamp(),
    })
    logger.debug(user.name + "【" + user.symbol + "】查询当前所有挂单=>" + str(order_info))
    return order_info


@logger.catch()
def 统计账户挂单详情(user: Account):
    orderInfo = 查询当前所有挂单NoSymbol(user)
    count_1000LUNCBUSD = 0
    count_1000LUNCUSDT = 0
    for temp in orderInfo:
        if temp['symbol'] == '1000LUNCBUSD':
            count_1000LUNCBUSD += 1
        if temp['symbol'] == '1000LUNCUSDT':
            count_1000LUNCUSDT += 1
    logger.info(f"{user.name}账号挂单详情： 1000LUNCBUSD挂单数量:{count_1000LUNCBUSD} , 1000LUNCUSDT挂单数量:{count_1000LUNCUSDT}")


@logger.catch()
def 市价平仓(user: Account):
    quantity = round(float(user.position_amt), user.交易对数量精度)
    if user.real_position_amt > 0:
        user.order_info = user.exchange.fapiPrivatePostOrder({
            'symbol': user.symbol,  # luna
            'side': 'SELL',  # 买入平仓
            'type': 'MARKET',  # 市价单
            'quantity': quantity
        })
    elif user.real_position_amt < 0:
        user.order_info = user.exchange.fapiPrivatePostOrder({
            'symbol': user.symbol,  # luna
            'side': 'BUY',  # 买入平仓
            'type': 'MARKET',  # 市价单
            'quantity': quantity
        })
    else:
        logger.info(user.name + "【" + user.symbol + "】账户持仓为0,无需平仓")
    if user.real_position_amt != 0:
        logger.debug("市价平仓=>" + str(user.order_info))
        logger.info(
            user.name + "【" + user.symbol + "】市价平仓成功！平仓数量：{:6f}".format(user.position_amt) + " 市价单价格：{:.6f}".format(
                user.now_price))


@logger.catch()
def 市价单(user: Account, num, side):
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
    logger.info(user.name + "【" + user.symbol + "】市价单下单成功！市价单数量：{:6f}".format(num) + " 市价单价格：{:.6f}".format(
        user.now_price) + "方向：" + 方向)

@logger.catch()
def 限价单_多线程(user: Account, grid:Grid,price, side):
    try:
        order_info = user.exchange.fapiPrivatePostOrder({
            'symbol': user.symbol,
            'side': side,
            'type': 'LIMIT',  # 限价单
            'quantity': round(grid.此网格数量, user.交易对数量精度),  # 数量
            'price': round(price, user.交易对价格精度),  # 价格
            'timestamp': get_timestamp(),
            'timeInForce': "GTC",
        })
        grid.订单方向= side
        grid.此网格订单号=str(order_info['orderId'])
        user.限价单订单簿.append(order_info['orderId'])
        user.order_map[grid.此网格订单号] = grid
        if side == 'BUY':
            方向 = "买入"
        else:
            方向 = "卖出"
        logger.info(
            f"{grid.网格名称}挂单成功，订单号：{grid.此网格订单号}，价格：{order_info['price']}，数量：{order_info['origQty']}，方向：{order_info['side']}")
        time.sleep(0.01)
    except Exception as e:
        logger.error(f"{grid.网格名称}挂单失败，价格：{price}，数量：{grid.此网格数量}，方向：{side},重试,错误信息：{e}")
        Account.executor.submit(lambda p: 限价单_多线程(*p), (user, grid, grid.此网格上边界价格, "SELL"))

@logger.catch()
def 限价单(user: Account, num, price, side):
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
        user.name + "【" + user.symbol + "】限价单下单成功！限价单数量：{:6f}".format(num) + " 限价单价格：{:.6f}".format(
            price) + "方向：" + 方向 + " 当前价格：" + str(
            user.now_price))


def 限价单抛异常(user: Account, num, price, side, grid: Grid):
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
    grid.订单方向 = side
    grid.此网格订单号 = user.order_info['orderId']
    if side == 'BUY':
        方向 = "买入"
    else:
        方向 = "卖出"
    logger.info(grid.网格名称 + "限价单下单成功！限价单数量：{:6f}".format(num) + " 限价单价格：{:.6f}".format(price) + "方向：" + 方向 + " 当前价格：" + str(user.now_price))



@logger.catch()
def 限价止损单(user: Account, 触发价, 委托价):
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
        logger.info(user.name + "【" + user.symbol + "】限价止损单下单成功！触发价:" + str(触发价) + " 委托价：" + str(委托价) + " 当前价格:" + str(
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
        logger.info(user.name + "【" + user.symbol + "】限价止损单下单成功！触发价:" + str(触发价) + " 委托价：" + str(委托价) + " 当前价格:" + str(
            user.now_price) + " 首单价值：" + str(user.首单价值) + "方向：卖出")


@logger.catch()
def 限价止损单自填数量(user: Account, 触发价, 委托价, 数量):
    if user.position_side == 'SHORT':
        user.order_info = user.exchange.fapiPrivatePostOrder({
            'symbol': user.symbol,
            'side': 'BUY',  # 买入平仓
            'type': 'STOP',  # 限价止损
            'quantity': round(数量, user.交易对数量精度),
            'stopPrice': round(触发价, user.交易对价格精度),
            "price": round(委托价, user.交易对价格精度),
            'priceProtect': 'TRUE',
        })
        logger.info(user.name + "【" + user.symbol + "】限价止损单下单成功！触发价:" + str(触发价) + " 委托价：" + str(委托价) + " 当前价格:" + str(
            user.now_price) + " 首单价值：" + str(user.首单价值) + "方向：买入")
    if user.position_side == 'LONG':
        user.order_info = user.exchange.fapiPrivatePostOrder({
            'symbol': user.symbol,
            'side': 'SELL',  # 卖出平仓
            'type': 'STOP',  # 限价止损
            'quantity': round(数量, user.交易对数量精度),
            'stopPrice': round(触发价, user.交易对价格精度),
            "price": round(委托价, user.交易对价格精度),
            'priceProtect': 'TRUE',
        })
        logger.info(user.name + "【" + user.symbol + "】限价止损单下单成功！触发价:" + str(触发价) + " 委托价：" + str(委托价) + " 当前价格:" + str(
            user.now_price) + " 首单价值：" + str(user.首单价值) + "方向：卖出")


@logger.catch()
def 市价止损单(user: Account, 委托价):
    if user.position_side == 'SHORT':
        user.order_info = user.exchange.fapiPrivatePostOrder({
            'symbol': user.symbol,
            'side': 'BUY',  # 买入平仓
            'type': 'STOP_MARKET',  # 市价止损
            'closePosition': 'TRUE',
            'stopPrice': round(委托价, user.交易对价格精度),
            'priceProtect': 'TRUE',
        })
        logger.info(user.name + "【" + user.symbol + "】市价止损单下单成功！ 委托价：" + str(委托价) + " 当前价格:" + str(
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
        logger.info(user.name + "【" + user.symbol + "】市价止损单下单成功！ 委托价：" + str(委托价) + " 当前价格:" + str(
            user.now_price) + " 首单价值：" + str(user.首单价值) + "方向：卖出")


@logger.catch()
def 限价止盈单(user: Account, 触发价, 委托价):
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
        logger.info(user.name + "【" + user.symbol + "】限价止盈单下单成功！触发价:" + str(触发价) + " 委托价：" + str(委托价) + " 当前价格:" + str(
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
        logger.info(user.name + "【" + user.symbol + "】限价止盈单下单成功！触发价:" + str(触发价) + " 委托价：" + str(委托价) + " 当前价格:" + str(
            user.now_price) + " 首单价值：" + str(user.首单价值) + "方向：卖出")


@logger.catch()
def 市价止盈单(user: Account, 委托价):
    if user.position_side == 'SHORT':
        user.order_info = user.exchange.fapiPrivatePostOrder({
            'symbol': user.symbol,
            'side': 'BUY',  # 买入平仓
            'type': 'TAKE_PROFIT_MARKET',  # 市价止损
            'closePosition': 'TRUE',
            'stopPrice': round(委托价, user.交易对价格精度),
            'priceProtect': 'TRUE',
        })
        logger.info(user.name + "【" + user.symbol + "】市价止盈单下单成功！ 委托价：" + str(委托价) + " 当前价格:" + str(
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
        logger.info(user.name + "【" + user.symbol + "】市价止盈单下单成功！ 委托价：" + str(委托价) + " 当前价格:" + str(
            user.now_price) + " 首单价值：" + str(user.首单价值) + "方向：卖出")


@logger.catch()
def 撤销所有订单(user: Account):
    user.exchange.fapiPrivate_delete_allopenorders({
        'symbol': user.symbol,
        'timestamp': get_timestamp()
    })
    user.止盈止损订单簿 = []
    user.限价单订单簿 = []
    logger.debug(user.name + "【" + user.symbol + "】撤销所有订单成功！")


@logger.catch()
def 批量撤销订单(user: Account, order_book):
    if len(order_book) > 0:
        idsString = dumps(order_book).replace(" ", "")
        idsString = quote(idsString)
        user.exchange.fapiPrivateDeleteBatchOrders({
            'symbol': user.symbol,
            'orderIdList': idsString,
            'timestamp': get_timestamp()
        })
        logger.debug("idsString:" + str(idsString))
        logger.info(user.name + "【" + user.symbol + "】批量撤销订单成功！ 订单号：" + str(order_book))
