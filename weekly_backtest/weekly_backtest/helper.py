import numpy as np
import pandas as pd
import sqlalchemy
from sqlalchemy.sql import text


def db_vol_forecast(estimator='close-to-close'):
    df_vol_forecast = pd.read_csv('../data/close_to_close_forecasts.csv')
    return(df_vol_forecast)


def db_otm_options(underlying, expiration, trade_date):
    
    sql = f'''
    select *
    from otm_history
    where underlying = '{underlying}'
    and expiration = '{expiration}'
    and trade_date = '{trade_date}'
    order by strike;
    '''

    # creating sql alchemy engine
    url = 'postgresql+psycopg2://postgres:$3lfl0v3@localhost:5432/delta_neutral'
    engine = sqlalchemy.create_engine(url)
    
    # grabbing data from database
    with engine.connect() as conn:
        query = conn.execute(text(sql))         
        df_otm = pd.DataFrame(query.fetchall())

    return df_otm


# should this be a helper or should this be in the class, it doesn't act on the database
def calc_strangle(df_otm_options, target_delta):
    strangle = []

    # calculating the abs diff between the delta and the target delta for all options
    df_otm_options['target_delta'] = target_delta
    df_otm_options['abs_delta_diff'] = abs(df_otm_options['delta'] - df_otm_options['target_delta'])

    # calculating the put trade
    df_put_trade = df_otm_options.query('cp=="put"').sort_values('abs_delta_diff').head(1)
    strangle.append(df_put_trade)

    # calculating the call trade
    df_call_trade = df_otm_options.query('cp=="call"').sort_values('abs_delta_diff').head(1)
    strangle.append(df_call_trade)

    df_strangle = pd.concat(strangle).reset_index(drop=True)

    return df_strangle


def db_option_pnl_history(underlying, expiration, cp, strike, start_date, end_date):
    
    # constructing the query
    sql = f'''
    select * 
    from option_pnl_history
    where underlying = '{underlying}'
    and expiration = '{expiration}'
    and cp = '{cp}'
    and strike = '{strike}'
    and trade_date >= '{start_date}'
    and trade_date <= '{end_date}';
    '''

    # creating sql alchemy engine
    url = 'postgresql+psycopg2://postgres:$3lfl0v3@localhost:5432/delta_neutral'
    engine = sqlalchemy.create_engine(url)

    # quarying the database
    with engine.connect() as conn:
        query = conn.execute(text(sql))         
        df_option_pnl_history = pd.DataFrame(query.fetchall())

    # dropping unused columns
    cols_to_drop = ['implied_forward', 'implied_vol', 'sh_opt_ask', 'sh_opt_mid', 'sh_hedge', 'sh_total_mid', 'lg_opt_bid', 'lg_opt_mid', 'lg_hedge', 'lg_total_mid']
    df_option_pnl_history.drop(columns=cols_to_drop, inplace=True)
    
    return(df_option_pnl_history)


def calc_trade_pnl_history(underlying, expiration, cp, strike, execution, last_trade_date, quantity):

    # grabbing pnl history from database
    df_pnl = db_option_pnl_history(underlying, expiration, cp, strike, execution, last_trade_date)

    # making sure the pnls are in the right order and adding quantity
    df_pnl.sort_values(['d2x'], ascending=False, inplace=True)
    df_pnl['quantity'] = quantity
    df_pnl

    # using the correct pnl column based on direction of trade
    if quantity > 0:
        df_pnl['unit_pnl_bid_ask'] = df_pnl['lg_total_bid']
        df_pnl['unit_pnl_mid'] = df_pnl['lg_total_bid']
    else:
        df_pnl['unit_pnl_bid_ask'] = df_pnl['sh_total_ask']
        df_pnl['unit_pnl_mid'] = df_pnl['sh_total_ask']
    
    # filling in the execution date PNL with the negative of the spread
    spread = df_pnl['spread'].iloc[0]
    df_pnl.iloc[0, df_pnl.columns.get_loc('unit_pnl_bid_ask')] = -spread
    df_pnl.iloc[0, df_pnl.columns.get_loc('unit_pnl_mid')] = -spread / 2

    # calculating the dollar PNL, using size which is just the absolute value of quantity
    df_pnl['dollar_pnl_bid_ask'] = df_pnl['unit_pnl_bid_ask'] * np.abs(df_pnl['quantity']) * 100
    df_pnl['dollar_pnl_mid'] = df_pnl['unit_pnl_mid'] * np.abs(df_pnl['quantity']) * 100
    
    return(df_pnl)