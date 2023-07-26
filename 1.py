'''
周K线趋势追踪策略，轻仓入场，浮盈加仓
# 计算回测区间开盘上涨天数占比，与收盘上涨天数占比
    # 计算3天内收盘上涨或者下跌幅度
    # 开仓：三根周线close>上一根最高价,[close-open]逐渐放大，
    # 第三根周线即将收盘买入
    # 清仓：拿一根
    # 获取前三周每一周的数据
'''
from jqdata import *
import talib
import pandas as pd
import numpy as np
import datetime
import time
import re


## main函数
def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 过滤掉order系列API产生的比error级别低的log
    log.set_level('order', 'error')
    # 输出内容到日志 log.info()
    # log.info('初始函数开始运行且全局只运行一次')

    # 设定全局函数
    # 数据获取周期
    context.LONGPERIOD = 45

    # 交易日数统计
    context.day = 0

    # 记录买入价
    g.porfolio_long_price = {}
    g.porfolio_short_price = {}

    # 合约交易单位
    g.MarginUnit = {
        'AP': 10,  # 苹果
        'BU': 10,  # 石油沥青
        'FG': 20,  # 玻璃
        'RB': 10,  # 螺纹钢
        'Y': 10,  # 豆油
        'ZC': 100,  # 动力煤
        'AG': 15,  # 白银
        'P': 10,  # 棕榈油
        'TA': 5,  # PTA
        'AU': 1000,  # 黄金
        'CU': 5,  # 铜
        'RU': 10,  # 天然橡胶
        'J': 100,  # 焦炭
        'M': 10,  # 豆粕
        'CF': 5,  # 一号棉花
        'SA': 20,  # 纯碱
        'ZN': 5,  # 锌
        'I': 100,  # 铁矿石
        'MA': 10,  # 甲醇
        'SR': 10,  # 白糖
        'UR': 20,  # 尿素
        'IF': 300,  # 沪深300指数期货
        'IH': 300,  # 上证50指数期货
        'IC': 300,  # 中证500指数期货
        'SC': 1000, # 原油期货
    }

    g.future_list = []
    ### 期货相关设定 ###
    # 设定账户为金融账户
    set_subportfolios([SubPortfolioConfig(cash=context.portfolio.starting_cash, type='futures')])
    # 期货类每笔交易时的手续费是：买入时万分之0.23,卖出时万分之0.23,平今仓为万分之23
    set_order_cost(OrderCost(open_commission=0.0001, close_commission=0.0001, close_today_commission=0.0023),
                   type='index_futures')
    # 设定保证金比例
    set_option('futures_margin_rate', 0.25)

    # 设置期货交易的滑点
    set_slippage(StepRelatedSlippage(2))
    # 运行函数（reference_security为运行时间的参考标的；传入的标的只做种类区分，因此传入'IF8888.CCFX'或'IH1602.CCFX'是一样的）
    # 注意：before_open/open/close/after_close等相对时间不可用于有夜盘的交易品种，有夜盘的交易品种请指定绝对时间（如9：30）

    # 开盘前运行
    run_daily(before_market_open, time='8:30', reference_security='FG8888.XZCE')
    # 开盘时运行
    run_daily(market_open, time='9:30', reference_security='FG8888.XZCE')
    # 收盘记录
    run_daily(after_market_close, time='15:30', reference_security='FG8888.XZCE')
    # 风控止损
    run_daily(stop_loss_monitor, time='21:00', reference_security='FG8888.XZCE')


## 开盘前运行函数
def before_market_open(context):
    # 输出运行时间
    # log.info('函数运行时间(before_market_open)：'+str(context.current_dt.time()))

    # 给微信发送消息（添加模拟交易，并绑定微信生效）
    # send_message('美好的一天~')

    ## 获取要操作的股票(g.为全局变量)
    # 获取当月指数期货合约
    g.AP = get_dominant_future('AP')
    g.BU = get_dominant_future('BU')
    g.FG = get_dominant_future('FG')
    g.RB = get_dominant_future('RB')
    g.Y = get_dominant_future('Y')
    g.AG = get_dominant_future('AG')
    g.P = get_dominant_future('P')
    g.TA = get_dominant_future('TA')
    g.AU = get_dominant_future('AU')
    g.CU = get_dominant_future('CU')
    g.RU = get_dominant_future('RU')
    g.J = get_dominant_future('J')
    g.M = get_dominant_future('M')
    g.CF = get_dominant_future('CF')
    g.SA = get_dominant_future('SA')
    g.ZN = get_dominant_future('ZN')
    g.MA = get_dominant_future('MA')
    g.I = get_dominant_future('I')
    g.SR = get_dominant_future('SR')
    g.UR = get_dominant_future('UR')
    g.IF = get_dominant_future('IF')
    g.IH = get_dominant_future('IH')
    g.IC = get_dominant_future('IC')
    g.SC = get_dominant_future('SC')

    # 更新list
    g.future_list = list(
        set([g.AP, g.BU, g.FG, g.RB, g.Y, g.AG, g.P, g.TA, g.AU, g.CU, g.RU, g.J, g.M, g.CF, g.SA, g.ZN, g.I, g.MA,
             g.SR, g.UR,g.IF,g.IH,g.IC,g.SC]))
    g.future_list = [item for item in g.future_list if item != '']
    #   设置交易天数时钟，持续统计交易天数
    context.day = context.day + 1

    # 设置目标年收益率，后续单个期货合约的保证金上限需使用该数据
    context.inc = 0.25

    # 当前可用
    # log.info(context.portfolio.available_cash)


## 开盘时运行函数
def market_open(context):
    # log.info('函数运行时间(market_open):'+str(context.current_dt.time()))
    # future_list = {g.AP, g.BU, g.FG, g.RB, g.Y, g.AG, g.P, g.TA, g.AU, g.CU, g.RU, g.J, g.M, g.CF, g.SA, g.ZN, g.I,
    #               g.MA}
    # future_list = {item for item in future_list if item != ''}
    # log.info(future_list)
    future_list = g.future_list
    # 获取合约数量
    context.num = len(future_list)

    # 主力合约切换主动平仓，使用下面的代码
    for future in context.portfolio.short_positions.keys():
        if future not in g.future_list:
            order_target_value(future, 0, side='short')
            g.porfolio_short_price[future] = 0
    for future in context.portfolio.long_positions.keys():
        if future not in g.future_list:
            order_target_value(future, 0, side='long')
            g.porfolio_long_price[future] = 0
    # 主力合约切换以后不主动平仓，如主动平仓，使用上面的代码
    # 通过以下，发现现象，贴近合约到期月份，不主动平仓，收益是增加的。这一条是否高可能性需要进一步确认。

    for future_code in g.future_list:
        symbol = re.search(r'^(\D+)', future_code).group(1)
        deal_long(context, future_code, symbol)
        deal_short(context, future_code, symbol)


# 交易逻辑
def deal_long(context, future_code, symbol):
    # 当月合约
    current_f = future_code
    # 是否目前有仓位
    cur_long = 0

    # 最新价
    price_l = 0
    # 查看多单仓位情况
    if current_f in context.portfolio.long_positions.keys() and context.portfolio.long_positions[current_f].value > 0:
        cur_long = 1
        price_l = context.portfolio.long_positions[current_f].price
        #
        cost_price = g.porfolio_long_price[current_f]
        if cost_price == 0:
            log.error(current_f,cost_price,"long持仓价为0")
            g.porfolio_long_price[current_f] = context.portfolio.long_positions[current_f].avg_cost

    # 获取当前合约历史数据
    num = 30
    df = attribute_history(current_f, num)
    price_now = df['close'][-1]
    last_day_close = df['close'][-1]

    # 获取周线级别数据，画图
    df_week = attribute_history(current_f, 40, unit='5d')
    ma_40_week = df_week['close'].mean()
    # record(ma_99_week = ma_99_week, close = df_week['close'][-1])
    end_date = context.current_dt
    # 周几
    weekday = context.current_dt.isoweekday()

    # 止盈or止损or加仓
    if cur_long > 0:
        #
        open_position_time = context.portfolio.long_positions[current_f].init_time
        last_open_position_time = context.portfolio.long_positions[current_f].transact_time
        # 更新开仓以来的最高价
        df_high = get_price(current_f, start_date=open_position_time, end_date=context.current_dt, frequency='daily')
        #
        highest_from_open = df_high["close"].max()
        # is_close_position = is_one_week_ago(context.current_dt,context.portfolio.long_positions[current_f].init_time)
        # is_close_position =  (price_l - g.porfolio_price[current_f])/g.porfolio_price[current_f] > 0.05  and is_one_week_ago(context.current_dt,context.portfolio.long_positions[current_f].init_time)

        # 动态止盈：TODO 最高点回踩3%止盈
        is_close_position = (price_l - highest_from_open) / highest_from_open <= -0.05

        # 移动止损: TODO 0.5%
        is_stopping_loss = price_l <= g.porfolio_long_price[current_f] * 0.995 or (
                is_one_week_ago(context.current_dt, open_position_time) and price_l <= g.porfolio_long_price[
            current_f] + 1)
        if is_close_position or is_stopping_loss:
            result = order_target_value(current_f, 0, side='long')
            if result is not None:
                g.porfolio_long_price[current_f] = 0
                return

        # 浮盈加仓
        is_add_position = price_l < last_day_close
        open_cash = min(context.portfolio.available_cash * 0.5,1000000)
        more_amount = amount_available(context, open_cash, price_l, symbol)
        if is_add_position and more_amount > 0:
            result = order(current_f, more_amount, side='long')
            if result is not None and result.filled >0:
                g.porfolio_long_price[current_f] = result.price
                #log.info("long浮盈加仓",current_f,more_amount)
                return

    # 开仓！！！！！！！
    if cur_long == 0:
        # 开仓手数
        # 保证金=合约价格x交易单位x保证金比例
        # 开仓：限制轻每单10w
        open_cash = 100000 if context.portfolio.available_cash < 500000 else 200000
        amount = amount_available(context, open_cash, price_now, symbol)
        is_open_position = (
                weekday == 5 and df_week['open'][-2] > ma_40_week and df_week['close'][-1] > df_week['high'][-2]
                and df_week['low'][-1] > df_week['open'][-2]
                and is_all_week_scaling(df_week[-2:]) and check_weekly_increase(df_week[-2:]))

        # 开仓
        if is_open_position and amount > 0:
            result = order_target(current_f, amount, side='long')
            if result is None:
                log.error('下单错误', current_f, price_now)
            elif result.filled > 0 :
                #
                g.porfolio_long_price[current_f] = context.portfolio.long_positions[current_f].price


# 做空逻辑
def deal_short(context, future_code, symbol):
    # 当月合约
    current_f = future_code
    # 是否目前有仓位
    cur_short = 0

    # 最新价
    price_s = 0
    # 最新持仓价
    cost_price = 0
    # 查看空单仓位情况
    if current_f in context.portfolio.short_positions.keys() and context.portfolio.short_positions[current_f].value > 0:
        cur_short = 1
        price_s = context.portfolio.short_positions[current_f].price
        # 持仓价
        cost_price = g.porfolio_short_price[current_f]
        if cost_price == 0:
            log.error(current_f,cost_price,"short持仓价为0")
            g.porfolio_short_price[current_f] = context.portfolio.short_positions[current_f].avg_cost

    # 获取当前合约历史数据
    num = 30
    df = attribute_history(current_f, num)
    price_now = df['close'][-1]
    last_day_close = df['close'][-1]

    # 获取周线级别数据，画图
    df_week = attribute_history(current_f, 40, unit='5d')
    ma_40_week = df_week['close'].mean()
    # record(ma_99_week = ma_99_week, close = df_week['close'][-1])
    end_date = context.current_dt
    # 周几
    weekday = context.current_dt.isoweekday()

    # 止盈or止损or加仓
    if cur_short > 0:
        #
        open_position_time = context.portfolio.short_positions[current_f].init_time
        last_open_position_time = context.portfolio.short_positions[current_f].transact_time
        # 更新开仓以来的最低价
        df_low = get_price(current_f, start_date=open_position_time, end_date=context.current_dt, frequency='daily')
        #
        lowest_from_open = df_low["close"].min()
        # 动态止盈：TODO 3% 止盈
        is_close_position = (price_s - cost_price) / cost_price <= -0.03

        # 移动止损: TODO 0.5%
        is_stopping_loss = price_s >= cost_price * 1.005 or (
                is_one_week_ago(context.current_dt, open_position_time) and price_s >= price_s)
        if is_close_position or is_stopping_loss:
            result = order_target_value(current_f, 0, side='short')
            if result is not None:
                g.porfolio_short_price[current_f] = 0
                return

        # # 浮盈加仓
        # is_add_position = price_s < cost_price
        # open_cash = min(context.portfolio.available_cash * 0.2,50000)
        # more_amount = amount_available(context, open_cash, price_s, symbol)
        # if is_add_position and more_amount > 0:
        #     result = order(current_f, more_amount, side='short')
        #     if result is not None and result.filled > 0:
        #             g.porfolio_short_price[current_f] = result.price
        #             log.info("short浮盈加仓", current_f, more_amount)
        #             return

    # 开仓！！！！！！！
    if cur_short == 0:
        # 开仓手数
        # 保证金=合约价格x交易单位x保证金比例
        # 开仓：限制每单10w
        open_cash = 50000 if context.portfolio.available_cash < 500000 else 500000
        amount = amount_available(context, open_cash, price_now, symbol)
        is_open_position = (
                weekday == 5 and df_week['open'][-2] < ma_40_week and df_week['close'][-1] < df_week['low'][-2]
                and df_week['high'][-1] < df_week['open'][-2]
                and is_all_week_scaling(df_week[-2:]) and check_weekly_decrease(df_week[-2:]))

        # 开仓
        if is_open_position and amount > 0:
            result = order_target(current_f, amount, side='short')
            if result is None:
                log.error('做空下单错误', current_f, price_now)
            elif result.filled > 0:
                g.porfolio_short_price[current_f] = result.price


# 收盘
def after_market_close(context):
    #log.info("总现金",context.portfolio.available_cash)
    for future_code in g.future_list:
        if future_code in (context.portfolio.long_positions.keys() and context.portfolio.short_positions.keys()):
            if context.portfolio.long_positions[future_code].value >0 and context.portfolio.short_positions[future_code].value >0:
                log.info("同时开了多空",future_code)
    return


'''
-------------------------- 风控--------------------------------------
'''

# 风控,每日执行
def stop_loss_monitor(context):
    for future_code in g.future_list:
        if future_code in context.portfolio.long_positions.keys() and context.portfolio.long_positions[future_code].value > 0:
            deal_stop_long_loss(context, future_code)
        if future_code in context.portfolio.short_positions.keys() and context.portfolio.short_positions[future_code].value > 0:
            deal_stop_short_loss(context, future_code)


def deal_stop_long_loss(context, future_code):
    # 查看多单仓位情况
    current_f = future_code
    price_now = context.portfolio.long_positions[current_f].price
    is_stopping_loss = price_now <= g.porfolio_long_price[current_f] * 0.995
    if is_stopping_loss:
        result = order_target_value(current_f, 0, side='long')
        if result != None:
            g.porfolio_long_price[current_f] = 0


def deal_stop_short_loss(context, future_code):
    # 查看空单仓位情况
    current_f = future_code
    price_now = context.portfolio.short_positions[current_f].price
    is_stopping_loss = price_now >= g.porfolio_short_price[current_f] * 1.005
    if is_stopping_loss:
        result = order_target_value(current_f, 0, side='short')
        if result != None:
            g.porfolio_short_price[current_f] = 0

'''
----------------------------------------------------------------
'''

##util 是否每周都是递增
def check_weekly_increase(weeks_data):
    for i in range(len(weeks_data)):
        if weeks_data['close'][i] - weeks_data['open'][i] <= 0:
            return False
    return True


## 是否每周都是振幅缩小
def check_weekly_decrease(weeks_data):
    for i in range(len(weeks_data)):
        if weeks_data['close'][i] - weeks_data['open'][i] >= 0:
            return False
    return True


## 是否每周都是振幅扩大
def is_all_week_scaling(weeks_data):
    for i in range(len(weeks_data) - 1):
        current_range = abs(weeks_data['close'][i] - weeks_data['open'][i])
        next_range = abs(weeks_data['close'][i + 1] - weeks_data['open'][i + 1])
        if current_range >= next_range:
            return False
    return True


# 是否过去了N周
def is_one_week_ago(current_date, target_date, weeks=1):
    one_week_ago = current_date - timedelta(weeks=weeks)
    if target_date <= one_week_ago:
        return True
    return False


# 浮盈加仓
def add_position():
    return


# 计算能开多少手
def amount_available(context, open_cash, price_now, symbol):
    amount = 0
    open_cash = min(open_cash, context.portfolio.available_cash * 0.95)
    amount = math.floor(open_cash / (price_now * g.MarginUnit[symbol] * context.inc))
    return amount


