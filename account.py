from decimal import Decimal


class Account(object):

    def __init__(self, name):
        # 项目运行需要的参数
        self.port = 80
        self.now_price = 0.0  # 当前市场标记价格
        self.listen_key = ''  # 监听的key
        self.entry_price = 0.0  # 仓位价格
        self.entry_num = 0.0  # 仓位数量
        self.entry_value = 0.0  # 仓位价值
        self.now_timestamp = 0  # 时间戳，解决tradingview重复发请求的问题
        self.busd_wallet_balance = 0.0  # 账户busd余额
        self.usdt_wallet_balance = 0.0  # 账户usdt余额
        self.wallet_balance = 0.0  # 账户余额
        self.initial_margin = 0.0  # 维持保证金
        self.position_amt = 0.0  # 持仓数量
        self.real_position_amt = 0.0  # 实际持仓数量
        self.last_cover_price = 0.0  # 最后一次的补仓价格
        self.last_cover_num = 0.0  # 最后一次的补仓价格
        self.cover_num = 0.0  # 本次补仓数量
        self.cover_price = 0.0  # 本次补仓金额
        self.cover_statistics = 0  # 补仓次数统计
        self.cover_need = 0.0  # 需要达到多少触发补仓
        self.cover_value = 0.0  # 补仓价值
        self.order_info = ''  # 订单信息
        self.stop_profit = 0.0  # 止盈点位
        self.sell_touch_price = 0.0  # 卖出触发价格
        self.buy_touch_price = 0.0  # 买入触发价格
        self.last_entry_num = 0.0  # 最后一次的仓位数量
        self.min_entry_num = 0.0  # 最小仓位数量
        self.限价单订单簿 = []  # 限价单订单簿
        self.止盈止损订单簿 = []  # 止盈止损订单号
        self.止损单号=''  # 止损单号
        self.止盈单号=''  # 止盈单号
        self.马丁触发价格 = 0.0
        self.首单价值 = 0.0
        # 自定义参数
        # ==========================================apiKey=========================================
        if name == "cx":
            self.name = "cx"
            self.api_key = 'sic88888TE9NcizAOq3Z4KaD6vHig3TxMYYeac42tlNr22cEXTJV0hvjMhSoeZ5f'
            self.secret = 'iYAyAe2DWpFLp7Ow89A0OaTm5TbomwBRI1TgLM3KhVLntwlPCbxv2aqjvPLeV7E9'
        elif name == "syb":
            self.name = "syb"
            self.api_key = 'B9KD1UB4LHHGGQsQ54q4Tk2ONcSQEPxVvM8XEksEH89ocSwedC4OsQHLduOvVeJT'
            self.secret = 'ZW7rikzhuN6kXUcnR23bzpIor2GrLUVNFz4ln9AFLvDS1AgDJ5AhhHcgq3agb9qn'
        elif name == "yyn_big":
            self.name = "yyn_big"
            self.api_key = 'NtgY0dBifINkKgzo3JCxsyQYTnGgVqWnaJvnmRAuTtVUcwMs951rgqx4RbIC6z1O'
            self.secret = '0Ck4Q7LMoN9nR3Mt6pwjQxL8F4ru4omdGua4gwyMNHEPW5FOyRZFoqeHQMXhO6Nb'
        elif name == "yyn_small":
            self.name = "yyn_small"
            self.api_key = 'WgDjyszZYXz21MDlrvZxtYgrPtdmIZkP81gdiAX4XmmomHU21Hk8kqLtwcT93yOY'
            self.secret = 'PozIcU1yTTnMyGUe9Cq9VUKhKGg3yq5MK257RM8ghbM0va7U0RKNey9BFdLF5KQx'
        # ==========================================交易对相关参数设置===================================
        self.symbol = 'LUNA2BUSD'  # 交易对  LUNA2BUSD   ETHUSDT
        self.websocket_symbol = 'luna2busd'  # 交易对  luna2busd   ethusdt
        self.trade_currency = 'BUSD'  # 交易货币  USDT  BUSD
        self.市价手续费率 = 0.0003  # 手续费率
        self.限价手续费率 = 0.00012  # 手续费率
        self.交易对价格精度 = 4  # 交易对价格精度
        self.交易对数量精度 = 0  # 交易对价格精度
        self.position_side = 'SHORT'  # 持仓方向 可选参数 SHORT(做空) LONG(做多)
        self.首单数量 = 50  # 首单数量
        self.first_order_type = 'LIMIT'  # 首单挂单类型 支持 MARKET(市价单) LIMIT(限价单)
        self.leverage = 20.0  # 杠杆倍数
        self.margin_type = 'CROSSED'  # 保证金模式 ISOLATED(逐仓), CROSSED(全仓)
        self.right_now_order = False  # 是否立即下首单
        self.right_now_order_after_stop = False  # 止盈止损后立刻下首单 False True
        self.need_sign = True  # 是否需要指标 False True
        # ==========================================止盈参数设置===================================
        # 止盈类型 两种都支持 取最大值 percent(百分比) fixed(固定差额) 参考标准为仓位价格
        self.止盈类型 = 0  # 0 固定金额止盈  1 百分比止盈
        self.开启止盈 = True  # 是否开启止盈 False True
        self.止盈相对于首单 = False
        self.止盈总金额 = 1  # 止盈总金额
        self.止盈百分比 = 0.4  # 止盈百分比 相对于保证金
        self.首单止盈百分比 = 0.1  # 首单止盈百分比 相对于保证金
        # ==========================================止损参数设置===================================
        self.止损类型 = 0  # 0 固定金额止盈  1 百分比止盈
        self.开启止损 = True  # 是否打开止损 True(打开) False(关闭)
        self.止损相对于首单 = True
        self.止损总金额 = 20  # 亏损达到50u市价止损
        self.止损百分比 = 105.4  # 止损百分比 相对于保证金
        self.首单止损百分比 = 105.4
        # ==========================================补仓参数设置===================================
        self.首次补仓数量 = 100  # 首次补仓数量
        self.最大补仓次数 = 3  # 最大补仓次数
        self.补仓倍数 = 2  # 倍数补仓的倍数 如 倍数为2 第一次补仓10个 则后面依次是 20 40 80 160 320
        self.cover_price_type = 'percent'  # 补仓单价格叠加类型 支持 percent(这次补仓的价格必须高于上次的百分之多少) fixed(这次补仓的价格必须高于上次的多少)
        self.补仓价格倍数 = 1.0  # 价格梯度 补仓单价格叠加类型*价格梯度
        # 补仓单价格叠加类型=percent 时生效  固定下跌0.5% => 0  0.5  0.1  0.15  0.2
        #                               固定下跌0.5% 加了梯度3后 => 0  0.5  (0.5+0.5)*3=3  (3+0.5)*3 =10.5  (10.5+5)*3
        self.补仓价格百分比例 = 0.6  # 这次补仓的价格必须高于上次的百分之多少 如 设置1 第一次补仓价格为5 则后面依次是 5*(1+1%) (5*(1+1%))(1+1%)

        # 补仓单价格叠加类型=fixed 时生效    固定下跌0.01 => 0  0.01  0.02  0.03  0.04  0.05
        #                               固定下跌0.01 加了梯度3后 => 0  0.01  (0.01+0.01)*3=0.06  (0.06+0.01)*3=2.1  (2.1+0.01)+3=6.33
        self.fixed_price_cover = 0.01  # 这次补仓的价格必须高于上次的多少 如 设置0.01 第一次补仓价格为5 则后面依次是 5.01 5.02 5.03
        self.cover_type = 'MARKET'  # 补仓单挂单类型 支持 MARKET(市价单) LIMIT(限价单)
        self.protect_position = 99  # 计划建仓占比 取值0-100 50就是最多买入半仓


if __name__ == '__main__':
    d = Account
    d.now_price = 1.8674  # 当前价格
    profit_show_type = ''
    show_type = ''
    cover_show_type = ''
    stop_profit_percent = 0.0
    target_price = 0.0
    d.cover_num = d.first_order_num
    for i in range(1, d.max_cover_num + 2):
        if d.cover_price_type == 'percent':
            # 固定下跌0.5% => 0  0.5  0.1  0.15  0.2
            # 固定下跌0.5% 加了梯度3后 => 0  0.5  (0.5+0.5)*3=3  (3+0.5)*3 =10.5  (10.5+5)*3
            d.cover_need = round(
                ((d.cover_need + d.percent_price_cover) * d.price_gradient) if i != 2 else d.percent_price_cover, 2)
            cover_show_type = "{:.2f}%".format(d.cover_need)
        else:
            # 固定下跌0.01 => 0  0.01  0.02  0.03  0.04  0.05
            # 固定下跌0.01 加了梯度3后 => 0  0.01  (0.01+0.01)*3=0.06  0.07  0.1
            d.cover_need = round(
                ((d.cover_need + d.fixed_price_cover) * d.price_gradient) if i != 2 else d.fixed_price_cover, 2)
            cover_show_type = "{:.2f}{}".format(d.cover_need, d.trade_currency)

        if d.position_side == 'Long':  # 做多
            show_type = '下跌'
            profit_show_type = '上涨'
            if d.cover_price_type == 'percent':
                target_price = (1 - d.cover_need / 100) * d.entry_price
            else:
                target_price = (1 - d.cover_need) * d.entry_price

        else:  # 做空
            show_type = '上涨'
            profit_show_type = '下跌'

            if d.cover_price_type == 'percent':
                target_price = (1 + d.cover_need / 100) * d.entry_price
            else:
                target_price = d.cover_need + d.entry_price

        d.cover_num = round(d.cover_num * d.multiple_num_cover if i != 2 else d.first_cover_num, 2)
        d.cover_value = round(d.cover_num * target_price, 2)
        d.entry_price = (d.entry_num * d.entry_price + d.cover_num * target_price) / (d.entry_num + d.cover_num)
        d.entry_num = d.entry_num + d.cover_num
        d.entry_value = d.entry_num * d.entry_price

        if i == 1:
            d.cover_need = 0.00
            if d.cover_price_type == 'percent':
                cover_show_type = "{:.2f}%".format(d.cover_need)
            else:
                cover_show_type = "{:.2f}{}".format(d.cover_need, d.trade_currency)
            d.cover_num = d.first_order_num
            target_price = d.now_price
            d.cover_value = round(d.cover_num * target_price, 2)
            d.entry_num = d.first_order_num
            d.entry_price = d.now_price
            d.entry_value = Decimal(d.entry_num) * Decimal(d.entry_price)

        if d.position_side == 'Long':  # 做多
            d.stop_profit = max(
                round(d.entry_price * (1 + d.percent_stop_profit * 0.01), 5),
                round(d.entry_price + d.fixed_stop_profit, 5))  # 止盈点位 = 仓位价格-目标盈利
            stop_profit_percent = (Decimal(d.stop_profit) - Decimal(target_price)) / Decimal(target_price) * 100
        else:  # 做空
            d.stop_profit = min(
                round(d.entry_price * (1 - d.percent_stop_profit * 0.01), 5),
                round(d.entry_price - d.fixed_stop_profit, 5))  # 止盈点位 = 仓位价格+目标盈利
            stop_profit_percent = (Decimal(target_price) - Decimal(d.stop_profit)) / Decimal(target_price) * 100

        print(
            "第{0}次补仓 {1}:{2} 触发补仓 订单数量：{3:>10.3f} {4} ".format(str(i - 1), show_type, cover_show_type, d.cover_num,
                                                               d.symbol) +
            "订单价值：{0:>8.2f} {1} 保证金：{2:>8.2f} {1} 触发价格：{3:>6.4f}      仓位价格：{4:>6.4f}      止盈点位：{5:>6.4f}      触发价格{6}{7:>2.2f}% 达到盈利点，".format(
                d.cover_value,
                d.trade_currency, d.cover_value / 20,
                target_price, d.entry_price, d.stop_profit, profit_show_type, stop_profit_percent)
            + "仓位数量：{0:>10.3f} {1} 仓位价值：{2:>8.2f} {3}".format(d.entry_num,
                                                              d.symbol, d.entry_value, d.trade_currency))

        # print("第" + str(i - 1) + "次补仓 " + show_type + "：" + cover_show_type + " 触发补仓 订单数量：" + "{:>10.5f}".format(
        #     d.cover_num) + d.symbol + " 订单价值：" + "{:>7.2f}".format(
        #     d.cover_value) + d.trade_currency + " 触发价格：" + "{:>7.5f}".format(target_price)
        #       + " 仓位价格：" + "{:>7.5f}".format(d.entry_price) + " 止盈点位：" + "{:>7.5f}".format(
        #     d.stop_profit) + " 触发价格" + profit_show_type + "{:>2.2f}".format(
        #     stop_profit_percent) + "% 达到盈利点，仓位数量：" + "{:>10.5f}".format(
        #     d.entry_num) + d.symbol + " 仓位价值：" + "{:>8.2f}".format(d.entry_value) + d.trade_currency)
