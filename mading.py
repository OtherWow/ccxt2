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


def get_token(user_main, user_hedge):
    user_main.listen_key = user_main.exchange.fapiPrivatePostListenKey()['listenKey']
    user_hedge.listen_key = user_hedge.exchange.fapiPrivatePostListenKey()['listenKey']
    logger.debug("定时器获得use1-listenKey:" + user_main.listen_key)
    logger.debug("定时器获得use2-listenKey:" + user_hedge.listen_key)
    threading.Timer(60 * 59, get_token).start()


def get_timestamp():
    return int(round(time.time() * 1000))

# @logger.catch()
# def trade(sign_data):
#     # =============================查询账户持仓情况==================================
#     account_info = exchange.fapiPrivateV2GetAccount({"timestamp": get_timestamp()})
#
#     for temp in account_info['assets']:
#         if d.trade_currency in temp['asset']:
#             d.wallet_balance = float(temp['walletBalance'])
#             break
#     for temp in account_info['positions']:
#         if d.symbol in temp['symbol']:
#             d.entry_price = float(temp['entryPrice'])
#             if d.sell_touch_price == 0:
#                 d.sell_touch_price = d.entry_price
#             if d.entry_price == 0:
#                 d.stop_done = True
#                 d.cover_statistics = 0
#             elif d.cover_statistics == 0:
#                 d.cover_statistics = 1
#             d.initial_margin = abs(float(temp['initialMargin']))  # 当前所需起始保证金
#             d.position_amt = abs(float(temp['positionAmt']))  # 持仓数量
#             d.real_position_amt = float(temp['positionAmt'])  # 实际持仓数量
#             break
#     # ====================================================================================买入做多的逻辑========================================================================================
#     if not d.need_sign:
#         # 仓位变化触发 如果仓位为0，则开首单，之后先撤销所有订单，然后下3个限价单，然后下止盈止损
#         if d.position_amt == 0:
#             logger.info("开始下首单")
#             d.min_entry_num = d.first_order_num
#             开首单()
#             return
#         logger.info("开始下止盈止损单")
#         止盈止损单()
#         num = d.position_amt
#         price = d.now_price
#         d.min_entry_num = d.position_amt + d.position_amt * d.multiple_num_cover
#         for i in range(3):
#             num *= d.multiple_num_cover
#             price *= (1 + d.percent_price_cover / 100)
#             logger.info("开始下限价单" + str(i))
#             限价单(num, price)
#             time.sleep(0.5)
#
#         return
#
#     if sign_data['type'] == 'buy':
#         if d.trust_sign:
#             if d.real_position_amt > 0 and d.entry_price > d.now_price + 0.005:  # 如果实际持仓数量大于0 表示是做多，碰到买入信号，先卖出之前的订单，在买入现在的
#                 市价卖出(d.position_amt)
#                 logger.info("已按市价卖出平仓！当前价格：" + str(d.now_price))
#                 time.sleep(1)
#                 市价买入(d.first_order_num)
#                 logger.info("已按市价买入开仓！当前价格：" + str(d.now_price))
#             if d.real_position_amt < 0:  # 如果实际持仓数量小于0 表示是做空，碰到买入信号，先买入现在的，在卖出之前的
#                 市价买入(d.position_amt)
#                 logger.info("已按市价买入平仓！当前价格：" + str(d.now_price) + " 仓位价格：" + str(d.entry_price) + " 预计盈利:+" + str(
#                     d.position_amt * (d.entry_price - d.now_price)) + " " + d.trade_currency + "盈利 " + str(
#                     d.position_amt * (d.entry_price - d.now_price) / d.initial_margin * 100) + "%")
#                 time.sleep(1)
#                 市价买入(d.first_order_num)
#                 logger.info("已按市价买入开仓做多！当前价格：" + str(d.now_price))
#             return
#         # 进来第一步先判断持仓方向 做空的话就是平仓
#         if d.position_side == 'SHORT':
#             if d.initial_margin == 0:
#                 logger.info("收到买入信号，但是还未建仓！当前价格：" + str(d.now_price))
#                 return
#             plan_profit = (d.entry_price - d.now_price) * d.position_amt
#             stop_profit_percent = plan_profit / d.initial_margin * 100
#             if d.now_price > d.entry_price:
#                 logger.info("当前价格：" + str(d.now_price) + "高于仓位价格：" + str(d.entry_price) + " 暂不平仓！")
#                 return
#             # 平仓之前 先看利润是否已经达到了要求
#             d.stop_profit = min(
#                 round(d.entry_price * (1 - d.percent_stop_profit * 0.01), 5),
#                 round(d.entry_price - d.fixed_stop_profit, 5))  # 止盈点位 = 仓位价格+目标盈利
#             if d.now_price > d.stop_profit:
#                 #  如果当前价格高于于目标止盈价格,则返回
#                 logger.info("当前价格：" + str(d.now_price) + "高于计划止盈价格：" + str(d.stop_profit) + " 暂不平仓！")
#                 return
#             buy_market_close_position()
#             logger.info(
#                 "已按市价买入平仓！当前价格：{:.4f}".format(d.now_price) + " 仓位价格：{:.4f}".format(d.entry_price) + " 预计盈利:+" + str(
#                     plan_profit) + " " + d.trade_currency + "盈利 " + str(stop_profit_percent) + "%")
#             if d.right_now_order:
#                 sell_market(d.first_order_num)
#                 logger.info("立即开首单策略执行成功！已按照市价卖出做空! " + " 市场价格：" + str(d.now_price) + " 数量：" + str(
#                     d.first_order_num) + "价值:" + str(
#                     d.now_price * d.first_order_num) + " " + d.trade_currency)
#         else:  # 做多
#             return
#
#     # ====================================================================================卖出做空的逻辑========================================================================================
#     elif sign_data['type'] == 'sell':
#         if d.trust_sign:
#             if d.real_position_amt > 0:  # 如果实际持仓数量大于0 表示是做多，碰到买入信号，先卖出之前的订单，在买入现在的
#                 市价卖出(d.position_amt)
#                 logger.info("已按市价卖出平仓！当前价格：" + str(d.now_price) + " 仓位价格：" + str(d.entry_price) + " 预计盈利:+" + str(
#                     d.position_amt * (d.now_price - d.entry_price)) + " " + d.trade_currency + "盈利 " + str(
#                     d.position_amt * (d.now_price - d.entry_price) / d.initial_margin * 100) + "%")
#                 time.sleep(1)
#                 市价卖出(d.first_order_num)
#                 logger.info("已按市价卖出开仓做空！当前价格：" + str(d.now_price))
#             if d.real_position_amt < 0 and d.entry_price + 0.005 < d.now_price:  # 如果实际持仓数量小于0 表示是做空，碰到买入信号，先买入现在的，在卖出之前的
#                 市价买入(d.position_amt)
#                 logger.info("已按市价买入平仓！当前价格：" + str(d.now_price))
#                 time.sleep(1)
#                 市价卖出(d.first_order_num)
#                 logger.info("已按市价卖出开仓做空！当前价格：" + str(d.now_price))
#             return
#         # 进来第一步先判断持仓方向 做空的话就是卖出补仓
#         if d.position_side == 'SHORT':
#             # =======================================保护措施相关的代码==========================================
#             # 补仓先看补仓次数用完没。用完了直接返回
#             if d.cover_statistics > d.max_cover_num:
#                 logger.info(
#                     "当前补仓次数：" + str(d.cover_statistics) + " 已超过最大补仓次数：" + str(d.max_cover_num) + "，暂停补仓！ 当前价格：" + str(
#                         d.now_price))
#                 return
#             temp = d.initial_margin / d.wallet_balance * 100
#             if temp >= d.protect_position:
#                 logger.info("保证金占比达到" + str(temp) + "%，暂停补仓！当前价格：" + str(d.now_price))
#                 return
#             # =======================================补仓价格相关的代码==========================================
#             if d.cover_statistics == 0:
#                 # 第一次开单价格 = 现价
#                 target_price = d.now_price
#             else:
#                 if d.cover_statistics == 1:
#                     if d.cover_price_type == 'percent':
#                         # 第一次补单价格 = 上一次触发(开单价)卖出价格*(1+补仓百分比)
#                         target_price = round(d.sell_touch_price * (1 + d.percent_price_cover / 100), 2)
#                     else:
#                         target_price = round(d.sell_touch_price + d.fixed_price_cover, 2)
#                 else:
#                     if d.cover_price_type == 'percent':
#                         # 之后的补单价格 = 上一次触发(开单价)卖出价格*(1+补仓百分比)
#                         target_price = round(d.sell_touch_price * (1 + d.percent_price_cover / 100 * d.price_gradient),
#                                              6)
#                     else:
#                         target_price = round((d.sell_touch_price + d.fixed_price_cover * d.price_gradient), 6)
#             if d.now_price >= target_price:
#                 logger.info("当前价: {:.4f}".format(d.now_price) + " >= 设定的触发价格: {:.4f}".format(target_price) + "可以执行补仓！")
#                 d.cover_price = target_price
#             else:
#                 logger.info("当前价: {:.4f}".format(d.now_price) + " < 设定的触发价格: {:.4f}".format(target_price) + "放弃补仓！")
#                 return
#             # =======================================补仓数量相关的代码==========================================
#             if d.cover_statistics == 0:
#                 # 第0次补单数量 = 首次建仓数量
#                 d.cover_num = d.first_order_num
#             else:
#                 if d.cover_statistics == 1:
#                     # 第一次补单数量 = 首次补单数量
#                     d.cover_num = d.first_cover_num
#                 else:
#                     # 之后的补单数量 = 最后一次补单数量 * 设定的倍数
#                     d.cover_num = round(d.cover_num * d.multiple_num_cover, 2)
#             d.cover_value = round(d.cover_num * d.now_price, 2)
#             # =======================================平仓代码==================================================
#             sell_market(d.cover_num)
#         else:  # 做多
#             return
#
#
# def f_sum(a, b):
#     return Decimal(a) + Decimal(b)
#
#
def 查询账户持仓情况(user):
    # =============================查询账户持仓情况==================================
    account_info = user.exchange.fapiPrivateV2GetAccount({"timestamp": get_timestamp()})
    for temp in account_info['assets']:
        if user.trade_currency in temp['asset']:
            user.wallet_balance = float(temp['walletBalance'])
            break
    for temp in account_info['positions']:
        if user.symbol in temp['symbol']:
            user.entry_price = float(temp['entryPrice']) # 仓位价格
            if user.sell_touch_price == 0:
                user.sell_touch_price = user.entry_price
            if user.entry_price == 0:
                user.cover_statistics = 0
            elif user.cover_statistics == 0:
                user.cover_statistics = 1
            user.initial_margin = float(temp['initialMargin'])  # 当前所需起始保证金
            user.position_amt = abs(float(temp['positionAmt']))  # 持仓数量
            user.real_position_amt = float(temp['positionAmt'])  # 实际持仓数量
            break
#
#
# def 限价单(num, price):
#     if d.position_side == 'SHORT':
#         d.order_info = exchange.fapiPrivatePostOrder({
#             'symbol': d.symbol,
#             'side': 'SELL',  # 卖出做空
#             'type': 'LIMIT',  # 市价单
#             'quantity': round(num, 6),  # 数量
#             'price': round(price, d.symbol_precision),  # 价格
#             'timestamp': get_timestamp(),
#             'timeInForce': "GTC",
#         })
#     if d.position_side == 'LONG':
#         d.order_info = exchange.fapiPrivatePostOrder({
#             'symbol': d.symbol,
#             'side': 'BUY',  # 卖出做空
#             'type': 'LIMIT',  # 市价单
#             'quantity': round(num, 6),  # 数量
#             'price': round(price, d.symbol_precision),  # 价格
#             'timeInForce': "GTC",
#             'timestamp': get_timestamp()
#         })
#
#
# def 止盈止损单():
#     查询账户持仓情况()
#     if len(d.stop_profit_order_book) != 0:
#         try:
#             # 批量撤销订单(d.stop_profit_order_book)
#             撤销所有订单()
#         except:
#             logger.error("批量撤销订单失败！订单号列表：{}".format(d.stop_profit_order_book))
#     if d.position_amt > 0:
#         if d.open_stop_loss:
#             # =============================计算止损价格==================================
#             price = d.stop_loss_total / d.position_amt + d.entry_price
#             stop_price = price * 0.995
#             if stop_price <= d.now_price:
#                 stop_price = d.now_price * 1.01
#             try:
#                 order_info = exchange.fapiPrivatePostOrder({
#                     'symbol': d.symbol,
#                     'side': 'BUY',  # 买入平仓
#                     'type': 'STOP',  # 限价止损
#                     'quantity': round(d.position_amt, 6),
#                     'stopPrice': round(stop_price, d.symbol_precision),
#                     "price": round(price, d.symbol_precision),
#                     'priceProtect': 'TRUE',
#                 })
#             except:
#                 logger.info(
#                     "限价止损单发送失败！下市价止损单！price:" + str(price) + " stop_price：" + str(stop_price) + " now_price:" + str(
#                         d.now_price))
#                 order_info = exchange.fapiPrivatePostOrder({
#                     'symbol': d.symbol,
#                     'side': 'BUY',  # 买入平仓
#                     'type': 'STOP_MARKET',  # 市价止损
#                     'closePosition': 'TRUE',
#                     'stopPrice': round(price, d.symbol_precision),
#                     'priceProtect': 'TRUE',
#                 })
#             d.stop_profit_order_book.append(order_info['orderId'])
#             logger.info(
#                 "下单标记止损单,止损价格：{:.4f}".format(stop_price) + " 预估损失：" + str(
#                     d.stop_loss_total) + " 当前仓位价格： {:.4f}".format(
#                     d.entry_price) + " 当前仓位数量：{:.4f}".format(d.position_amt))
#         if d.open_stop_profit:
#             # =============================计算止盈价格==================================
#             # 目标价格= (仓位价格-预计盈利/仓位数量)/1.0004
#             stop_price = (d.entry_price - d.stop_profit_total / d.position_amt) / 1.0004
#             if stop_price < 0:
#                 stop_price = 0.0001
#             order_info = exchange.fapiPrivatePostOrder({
#                 'symbol': d.symbol,
#                 'side': 'BUY',  # 买入平仓
#                 'type': 'TAKE_PROFIT_MARKET',  # 市价止盈
#                 'closePosition': 'TRUE',
#                 'stopPrice': round(stop_price, d.symbol_precision),
#                 'priceProtect': 'TRUE',
#             })
#             d.stop_profit_order_book.append(order_info['orderId'])
#             logger.info(
#                 "下单标记止盈单,止盈价格：{:.4f}".format(stop_price) + " 预估盈利：" + str(
#                     d.stop_profit_total) + " 当前仓位价格： {:.4f}".format(
#                     d.entry_price) + " 当前仓位数量：{:.4f}".format(d.position_amt))
#     return order_info['orderId']
#
#
def 开首单(user_main, user_hedge):
    if user_main.position_side == 'SHORT':
        user_main.order_info = user_main.exchange.fapiPrivatePostOrder({
            'symbol': user_main.symbol,
            'side': 'SELL',  # 卖出做空
            'type': 'MARKET',  # 市价单
            'quantity': round(user_main.first_order_num, 6),  # 数量
            'timestamp': get_timestamp()
        })
    if user_main.position_side == 'LONG':
        user_main.order_info = user_main.exchange.fapiPrivatePostOrder({
            'symbol': user_main.symbol,
            'side': 'BUY',  # 卖出做空
            'type': 'MARKET',  # 市价单
            'quantity': round(user_main.first_order_num, 6),  # 数量
            'timestamp': get_timestamp()
        })
    logger.info("开首单成功！首单数量：{:6f}".format(user_main.first_order_num) + " 首单价格：{:.4f}".format(user_main.now_price))
#
#
# def 撤销所有订单():
#     exchange.fapiPrivate_delete_allopenorders({
#         'symbol': d.symbol,
#         'timestamp': get_timestamp()
#     })
#
#
# def 批量撤销订单(order_book):
#     exchange.fapiPrivate_delete_batchorders({
#         'symbol': d.symbol,
#         'orderIdList': order_book,
#         'timestamp': get_timestamp()
#     })
#
#
# # 市价卖出做空
# def sell_market(num):
#     try:
#         if d.cover_type == 'MARKET':
#             d.order_info = exchange.fapiPrivatePostOrder({
#                 'symbol': d.symbol,  # luna
#                 'side': 'SELL',  # 卖出做空
#                 'type': 'MARKET',  # 市价单
#                 'quantity': round(num, 6),  # 数量
#                 'timestamp': get_timestamp()
#             })
#         elif d.cover_type == 'LIMIT':
#             d.order_info = exchange.fapiPrivatePostOrder({
#                 'symbol': d.symbol,  # luna
#                 'side': 'SELL',  # 卖出做空
#                 'type': 'LIMIT',  # 限价单
#                 'quantity': round(num, 6),  # 数量
#                 'price': Decimal(d.cover_price),  # 委托价格
#                 'timestamp': get_timestamp()
#             })
#         else:
#             logger.info("不支持的挂单类型！当前类型：" + d.cover_type)
#         if d.entry_price == 0:
#             # 如果仓位价格是0表示是首单，所以补仓统计更新为0
#             d.cover_statistics = 1
#         else:
#             d.cover_statistics += 1
#
#         # 最后一次的补仓价格
#         d.last_cover_price = d.now_price
#         # 最后一次的补仓数量
#         d.last_cover_num = num
#
#         d.sell_touch_price = d.now_price
#         logger.info("已按照市价卖出做空! " + " 市场价格：" + str(d.now_price) + " 数量：" + str(d.cover_num) + " 价值:" + str(
#             d.cover_value) + " " + d.trade_currency)
#         # 挂止损单
#         止盈止损单()
#
#     except Exception as e:
#         logger.error(e)
#         logger.error(f'error file:{e.__traceback__.tb_frame.f_globals["__file__"]}')
#         logger.error(f"error line:{e.__traceback__.tb_lineno}")
#         d.now_timestamp = get_timestamp()
#     return d.order_info['orderId']
#
#
# def 市价买入(num):
#     order_info = exchange.fapiPrivatePostOrder({
#         'symbol': d.symbol,  # luna
#         'side': 'BUY',  # 市价买入
#         'type': 'MARKET',  # 市价单
#         'quantity': round(float(num), 6)
#     })
#
#
# def 市价卖出(num):
#     order_info = exchange.fapiPrivatePostOrder({
#         'symbol': d.symbol,  # luna
#         'side': 'SELL',  # 市价卖出
#         'type': 'MARKET',  # 市价单
#         'quantity': round(float(num), 6)
#     })
#
#
# # 市价买入平仓
# def buy_market_close_position():
#     try:
#         # print('d.luna_position_amt:'+str(d.luna_position_amt))
#         order_info = exchange.fapiPrivatePostOrder({
#             'symbol': d.symbol,  # luna
#             'side': 'BUY',  # 买入平仓
#             'type': 'MARKET',  # 市价单
#             'quantity': round(float(d.position_amt), 6)
#         })
#         d.cover_statistics = 0
#         d.buy_touch_price = d.now_price
#     except Exception as e:
#         logger.error(e)
#         logger.error(f'error file:{e.__traceback__.tb_frame.f_globals["__file__"]}')
#         logger.error(f"error line:{e.__traceback__.tb_lineno}")
#         d.now_timestamp = get_timestamp()
#     return order_info['orderId']
#
#
# # 删除所有订单
# def delete_all_order():
#     exchange.fapiPrivate_delete_allopenorders({
#         'symbol': d.symbol,
#         'timestamp': get_timestamp()
#     })
#     time.sleep(2)
#
#
# def get_token():
#     d.listen_key = exchange.fapiPrivatePostListenKey()['listenKey']
#     logger.debug("定时器获得listenKey:" + d.listen_key)
#     threading.Timer(60 * 59, get_token).start()
#
#
# def init_webhooks():
#     addr = ('', d.port)
#     server = HTTPServer(addr, RequestHandler)
#     server.serve_forever()
#
#
# class RequestHandler(BaseHTTPRequestHandler):
#
#     def do_POST(self):
#         data = self.rfile.read(int(self.headers['content-length']))
#         data = unquote(str(data, encoding='utf-8'))
#         # print("转化前data:" + data)
#         data = json.dumps(eval(data))
#         # print("转化后data:" + data)
#         json_obj = json.loads(data)
#         if d.now_timestamp != json_obj['timestamp']:
#             d.now_timestamp = json_obj['timestamp']
#             trade(json_obj)
