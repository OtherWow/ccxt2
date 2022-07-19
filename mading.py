import threading
import time
import ccxt
import mainapp
import mywebsocket
from decimal import Decimal
from urllib.parse import unquote
from http.server import HTTPServer, BaseHTTPRequestHandler
from loguru import logger
from account import Account


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
    return user.exchange.fapiPublicGetExchangeInfo()


def get_token(user_main, user_hedge):
    user_main.listen_key = user_main.exchange.fapiPrivatePostListenKey()['listenKey']
    user_hedge.listen_key = user_hedge.exchange.fapiPrivatePostListenKey()['listenKey']
    logger.debug("定时器获得use1-listenKey:" + user_main.listen_key)
    logger.debug("定时器获得use2-listenKey:" + user_hedge.listen_key)
    threading.Timer(60 * 59, get_token).start()


def get_timestamp():
    return int(round(time.time() * 1000))


def 开首单(user_main, user_hedge):
    user_hedge.首单数量 = 0.0
    # 主账号下限价止盈止损单 下限价补单 对冲账号根据亏损金额下对冲单
    if user_main.position_side == 'SHORT':
        市价单(user_main, user_main.首单数量, 'SELL')
    if user_main.position_side == 'LONG':
        市价单(user_main, user_main.首单数量, 'BUY')
    止盈止损单(user_main)
    查询账户持仓情况(user_main)
    # 开始循环下限价单
    if user_main.position_side == 'SHORT':
        num = user_main.首次补仓数量
        last_percent = 0
        price = 0
        for i in range(user_main.最大补仓次数):
            last_percent = user_main.补仓价格百分比例 / 100 + last_percent * user_main.补仓价格倍数
            price = user_main.entry_price * (1 + last_percent)
            try:
                限价单(user_main, num, price, 'SELL')
            except Exception as e:
                logger.error(user_main.name + "第{}次限价单下单出错 ".format(i+1) + str(e))
            num = num * user_main.补仓倍数

        # 开始下对冲单的市价单
        # 主账号的止损总金额就是对冲账号的目标止盈金额 当最后一个限价单触发时 对冲单就应该已经能对冲亏损了
        # (price-user_main.entry_price-user_main.entry_price*user_main.市价手续费率-price*user_main.限价手续费率)*开单数量 = user_main.止损总金额
        hedge_num = user_main.止损总金额 / (
                price - user_main.entry_price - user_main.entry_price * user_main.市价手续费率 - price * user_main.限价手续费率)
        user_hedge.首单数量 = hedge_num
        市价单(user_hedge, user_hedge.首单数量, 'BUY')
        止盈止损单(user_hedge)
    if user_main.position_side == 'LONG':
        num = user_main.首次补仓数量
        last_percent = 0
        price = 0
        for i in range(user_main.最大补仓次数):
            last_percent = user_main.补仓价格百分比例 / 100 + last_percent * user_main.补仓价格倍数
            price = user_main.entry_price * (1 - last_percent)
            try:
                限价单(user_main, num, price, 'BUY')
            except Exception as e:
                logger.error(user_main.name + "第{}次限价单下单出错 ".format(i+1) + str(e))
                break
            num = num * user_main.补仓倍数

        # 开始下对冲单的市价单
        # 主账号的止损总金额就是对冲账号的目标止盈金额 当最后一个限价单触发时 对冲单就应该已经能对冲亏损了
        # (user_main.entry_price-price-user_main.entry_price*user_main.市价手续费率-price*user_main.限价手续费率)*开单数量 = user_main.止损总金额
        hedge_num = user_main.止损总金额 / (
                user_main.entry_price - price - user_main.entry_price * user_main.市价手续费率 - price * user_main.限价手续费率)
        user_hedge.首单数量 = hedge_num
        市价单(user_hedge, user_hedge.首单数量, 'SELL')
        止盈止损单(user_hedge)


@logger.catch()
def trade_task(user_main, user_hedge):
    查询账户持仓情况(user_main)
    查询账户持仓情况(user_hedge)
    if user_main.position_amt == 0 and user_hedge.position_amt == 0:
        logger.info("主账号与对冲账号皆没有持仓,开始开首单...")
        开首单(user_main, user_hedge)
        查询账户持仓情况(user_main)
        查询账户持仓情况(user_hedge)
    if (user_main.position_amt == 0 and user_hedge.position_amt != 0) or (
            user_main.position_amt != 0 and user_hedge.position_amt == 0):
        logger.info("主账号还有仓位或者对冲账号还有仓位,等待2个账号清空仓位,之后系统会自动开单！")
        return


def 查询账户持仓情况(user):
    # =============================查询账户持仓情况==================================
    account_info = user.exchange.fapiPrivateV2GetAccount({"timestamp": get_timestamp()})
    for temp in account_info['assets']:
        if user.trade_currency in temp['asset']:
            user.wallet_balance = float(temp['walletBalance'])
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
            break


def 市价单(user, num, side):
    user.order_info = user.exchange.fapiPrivatePostOrder({
        'symbol': user.symbol,
        'side': side,
        'type': 'MARKET',  # 限价单
        'quantity': round(num, user.交易对数量精度),  # 数量
        'timestamp': get_timestamp(),
    })
    logger.info(user.name + "市价单下单成功！市价单数量：{:6f}".format(num) + " 市价单价格：{:.6f}".format(user.now_price))


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
    logger.info(user.name + "限价单下单成功！限价单数量：{:6f}".format(num) + " 限价单价格：{:.6f}".format(price))


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
    if user.position_side == 'LONG':
        user.order_info = user.exchange.fapiPrivatePostOrder({
            'symbol': user.symbol,
            'side': 'SELL',  # 卖出平仓
            'type': 'STOP_MARKET',  # 市价止损
            'closePosition': 'TRUE',
            'stopPrice': round(委托价, user.交易对价格精度),
            'priceProtect': 'TRUE',
        })


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
    if user.position_side == 'LONG':
        user.order_info = user.exchange.fapiPrivatePostOrder({
            'symbol': user.symbol,
            'side': 'SELL',  # 卖出平仓
            'type': 'TAKE_PROFIT_MARKET',  # 市价止损
            'closePosition': 'TRUE',
            'stopPrice': round(委托价, user.交易对价格精度),
            'priceProtect': 'TRUE',
        })


def 止盈止损单(user):
    查询账户持仓情况(user)
    try:
        批量撤销订单(user, user.止盈止损订单簿)
    except Exception as e:
        logger.info(user.name + '撤销止盈止损单失败!' + str(e))
    委托价 = 0.0
    触发价 = 0.0
    if user.position_amt > 0:
        if user.开启止损:
            try:
                # =============================计算止损价格==================================
                if user.position_side == 'SHORT':
                    # 做空时的止损价格计算： （当前价格-仓位价格+0.0006*当前价格）仓位数量 = 预估损失
                    委托价 = (user.止损总金额 / user.position_amt + user.entry_price)/(1 + user.限价手续费率 + user.市价手续费率)
                    触发价 = 委托价 * 0.995
                    if 触发价 <= user.now_price:
                        触发价 = user.now_price
                if user.position_side == 'LONG':
                    # 做多时的止损价格计算： （仓位价格-当前价格+0.0006*当前价格）仓位数量 = 预估损失
                    委托价 = (user.entry_price - user.止损总金额 / user.position_amt)/(1 - user.限价手续费率 - user.市价手续费率)
                    触发价 = 委托价 * 1.005
                    if 触发价 >= user.now_price:
                        触发价 = user.now_price
                限价止损单(user, 触发价, 委托价)
            except Exception as e:
                logger.info(user.name + "限价止损单发送失败！下市价止损单！触发价:" + str(触发价) + " 委托价：" + str(委托价) + " 当前价格:" + str(
                    user.now_price) + str(e))
                if user.position_side == 'SHORT':
                    # 做空时的止损价格计算： （当前价格-仓位价格+0.0006*当前价格）仓位数量 = 预估损失
                    委托价 = (user.止损总金额 / user.position_amt + user.entry_price)/(1 + user.市价手续费率 + user.市价手续费率)
                if user.position_side == 'LONG':
                    # 做多时的止损价格计算： （仓位价格-当前价格+0.0006*当前价格）仓位数量 = 预估损失
                    委托价 = (user.entry_price - user.止损总金额 / user.position_amt)/(1 - user.市价手续费率 - user.市价手续费率)
                市价止损单(user, 委托价)
            user.止盈止损订单簿.append(user.order_info['orderId'])
            logger.info(user.name + "下单标记止损单,止损价格：{:.4f}".format(委托价) + " 预估损失：" + str(
                user.止损总金额) + " 当前仓位价格： {:.4f}".format(
                user.entry_price) + " 当前仓位数量：{:.4f}".format(user.position_amt))
        if user.开启止盈:
            try:
                # =============================计算止盈价格==================================
                if user.position_side == 'SHORT':
                    # 做空时的止盈价格计算： （仓位价格-当前价格-0.0006*当前价格）仓位数量 = 预估盈利
                    委托价 = (user.entry_price - user.止盈总金额 / user.position_amt)/(1 + user.限价手续费率 + user.市价手续费率)
                    触发价 = 委托价 * 1.005
                    if 触发价 >= user.now_price:
                        触发价 =user.now_price
                if user.position_side == 'LONG':
                    # 做多时的止盈价格计算： （当前价格-仓位价格-0.0006*当前价格）仓位数量 = 预估损失
                    委托价 = (user.止盈总金额 / user.position_amt + user.entry_price) / (1 - user.限价手续费率 - user.市价手续费率)
                    触发价 = 委托价 * 0.995
                    if 触发价 <= user.now_price:
                        触发价 = user.now_price
                限价止盈单(user, 触发价, 委托价)
            except Exception as e:
                logger.info(user.name + "限价止盈单发送失败！下市价止盈单！触发价:" + str(触发价) + " 委托价：" + str(委托价) + " 当前价格:" + str(
                    user.now_price) + str(e))
                if user.position_side == 'SHORT':
                    # 做空时的止盈价格计算： （仓位价格-当前价格-0.0006*当前价格）仓位数量 = 预估盈利
                    委托价 = (user.entry_price - user.止盈总金额 / user.position_amt)/(1 + user.市价手续费率 + user.市价手续费率)
                if user.position_side == 'LONG':
                    # 做多时的止盈价格计算： （当前价格-仓位价格-0.0006*当前价格）仓位数量 = 预估损失
                    委托价 = (user.止盈总金额 / user.position_amt + user.entry_price) / (1 - user.市价手续费率 - user.市价手续费率)
                市价止盈单(user, 委托价)
            user.止盈止损订单簿.append(user.order_info['orderId'])
            logger.info(
                user.name + "下单标记止盈单,止盈价格：{:.4f}".format(委托价) + " 预估盈利：" + str(
                    user.止盈总金额) + " 当前仓位价格： {:.4f}".format(
                    user.entry_price) + " 当前仓位数量：{:.4f}".format(user.position_amt))


def 撤销所有订单(user):
    user.exchange.fapiPrivate_delete_allopenorders({
        'symbol': user.symbol,
        'timestamp': get_timestamp()
    })
    logger.debug(user.name + "撤销所有订单成功！")


def 批量撤销订单(user, order_book):
    if len(order_book) > 0:
        user.exchange.fapiPrivatePostBatchorders({
            'symbol': user.symbol,
            'orderIdList': order_book,
            'timestamp': get_timestamp()
        })
