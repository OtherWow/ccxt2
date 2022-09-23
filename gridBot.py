import time
from json import dumps
import ccxt
from loguru import logger
import mading as md
from account import Account


class Grid(object):
    def __init__(self):
        self.此网格上边界价格 = 0
        self.此网格下边界价格 = 0
        self.此网格数量 = 0
        self.此网格订单号 = ""
        self.此网格持仓数量 = 0


def 创建网格(user):
    # md.撤销所有订单(user)
    md.查询账户持仓情况(user)
    if user.position_amt != 0:
        logger.info(f"{user.name}账户有持仓，无法创建网格")
        return

    user.now_price = 1300
    网格价格范围 = (user.网格区间上限 - user.网格区间下限) / user.网格数量
    单网格数量 = round(user.投入金额 * user.leverage / user.now_price / user.网格数量, user.交易对数量精度)
    当前下边界价格 = user.网格区间下限
    for i in range(user.网格数量):
        grid = Grid()
        grid.此网格上边界价格 = 当前下边界价格 + 网格价格范围
        grid.此网格下边界价格 = 当前下边界价格
        grid.此网格数量 = 单网格数量,
        当前下边界价格 = 当前下边界价格 + 网格价格范围
        user.grid_list.append(grid)

    print(*user.grid_list, sep='\n')

def 网格补单(user):
    for grid in user.grid_list:
        if grid.此网格订单号 == "":
            if user.position_side == "LONG": #做多

            else if user.position_side == "SHORT": #做空

            else:
                logger.info(f"{user.name} 请先设置持仓方向！")
                return
            grid.此网格订单号 = md.下单(user, grid.此网格下边界价格, grid.此网格数量, "buy")
            logger.info(f"{user.name}网格补单，订单号：{grid.此网格订单号}")
            time.sleep(0.5)


if __name__ == '__main__':
    user_main = Account("cx")
    user_hedge = Account("syb")
    md.init_exchange(user_main, user_hedge)
    md.get_token(user_main, user_hedge)
    md.获取交易对规则2(user_main, user_hedge)
    创建网格(user_main)
