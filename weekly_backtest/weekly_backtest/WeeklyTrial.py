# WeeklyTrial.py

import pandas as pd
import numpy as np
import sqlalchemy
from sqlalchemy.sql import text

from helper import db_vol_forecast
from helper import db_otm_options
from helper import calc_strangle
from helper import calc_trade_pnl_history


class WeeklyTrial:
    def __init__(self,
                 expiration = '2010-06-11',
                 last_trade_date = '2010-06-11',
                 execution = '2010-06-04',
                 universe = ['DIA','IWM','QQQ','SPY'],
                 leg_max = 5,
                 delta_long = 0.3, # delta of long strangles
                 delta_short = 0.3, # delta of short strangles
                 premium_budget = 2000,
                 random_long_short = False):
        
        # inputs from constructor
        self.expiration = expiration
        self.last_trade_date = last_trade_date
        self.execution = execution
        self.universe = universe
        self.leg_max = leg_max
        self.delta_long = delta_long
        self.delta_short = delta_short
        self.premium_budget = premium_budget
        self.random_long_short = random_long_short

        # other attributes that will be calculated along the way
        self.chain_history = None
        self.underlyings = None
        self.otm_options = None
        self.strangle_trades = None
        self.strangle_histories = None
        self.trial_daily_pnls = None
        self.trial_weekly_pnl_bid_ask = None
        self.trial_weekly_pnl_mid = None
        #print('Initialized!')


    def calc_all(self):
        self.calc_chain_history()
        self.calc_vol_premium_forecast()
        self.calc_underlyings_to_trade()
        self.calc_all_otm_options()
        self.calc_all_strangle_trades()
        self.calc_trade_sizes()
        self.calc_strangle_histories()
        self.calc_pnl_by_underlying()
        self.calc_trial_daily_pnls()
        self.calc_trial_weekly_pnl()
        print(f'{self.expiration}')
        return(None)


    def calc_chain_history(self):

        # creating the symbols string for the query
        # should this by it's own small utility function?
        symbols = '('
        for ix_underlying in self.universe:
            symbols += f"'{ix_underlying}',"
        symbols = symbols[:-1] + ')'

        # constructing the query
        sql = f'''
        select *
        from chain_history
        where underlying in {symbols}
        and expiration = '{self.expiration}'
        and trade_date = '{self.execution}';
        '''

        # creating sql alchemy engine
        url = 'postgresql+psycopg2://postgres:$3lfl0v3@localhost:5432/delta_neutral'
        engine = sqlalchemy.create_engine(url)

        # executing the query
        with engine.connect() as conn:
            query = conn.execute(text(sql))         
            df_chain_history = pd.DataFrame(query.fetchall())

        # Because we queried from a database, the expiration and trade_date come in as datetime objects.  
        # Let's turn these into strings so they can be compared to the dates in the DataFrames we read in from CSVs.
        df_chain_history['expiration'] = df_chain_history['expiration'].apply(str)
        df_chain_history['trade_date'] = df_chain_history['trade_date'].apply(str)

        # this is the point of the function to define chain_history
        self.chain_history = df_chain_history

        return(None)


    def calc_vol_premium_forecast(self, estimator='close-to-close'):

        # this will eventually be a call to a database via db_vol_forecast
        df_vol_forecast = db_vol_forecast(estimator)

        # joining together vol forecasts and calculating volatility premium
        self.chain_history = \
            (
            self.chain_history 
                .merge(df_vol_forecast, how='left',
                    left_on=['underlying', 'trade_date'],
                    right_on=['ticker', 'week_end'],)
                .assign(vol_prem_forecast = lambda df: df['swap_rate_mid'] - df['close_to_close'])
            )
        
        return(None)

    def calc_underlyings_to_trade(self):
        # determining leg-size
        leg_size = self.leg_max
        if len(self.chain_history) < 2 * self.leg_max:
            leg_size = len(self.chain_history) // 2

        # sort by vol premium, lowest on top, highest on bottom
        self.chain_history.sort_values(by=['vol_prem_forecast'], inplace=True)

        # go long the underlyings with the lowest vol premium
        longs = list(self.chain_history.head(leg_size)['underlying'])

        # go short the underlyings with the highest vol premium
        shorts = list(self.chain_history.tail(leg_size)['underlying'])


        # randomizing the longs and shorts is to test if there is
        # actual edge in the volatility estimates
        if self.random_long_short:
            df_chain_history_shuffled = self.chain_history.sample(frac=1)
            longs = list(df_chain_history_shuffled.head(leg_size)['underlying'])
            shorts = list(df_chain_history_shuffled.tail(leg_size)['underlying'])


        # putting this information into a DataFrame
        # eventually this DataFrame will hold quantity information; 
        # quantity is the combined measure of size and direction.
        unds = longs + shorts
        dirs = leg_size * [1] + leg_size * [-1]
        df_directions = pd.DataFrame({
            'underlying':unds,
            'direction':dirs,
        })

        # adding expiration and execution to this DataFrame
        df_directions['expiration'] = self.expiration
        df_directions['execution'] = self.execution

        self.underlyings = df_directions
        return(None)
    

    def calc_all_otm_options(self):
        # results will be put in a Dict
        otm_options = {}
        
        # iterating through all underlyings
        # and grabbing OTM options
        for ix_underlying in self.underlyings['underlying']:
            df_otm = db_otm_options(ix_underlying, self.expiration, self.execution)
            otm_options[ix_underlying] = df_otm

        self.otm_options = otm_options
        return(None)
    

    def calc_all_strangle_trades(self):
        # results will be in a Dict
        trades = {}
        for ix_underlying in self.underlyings['underlying']:
            # grabbing direction from df_direction
            dir = self.underlyings.query('underlying==@ix_underlying')['direction'].iloc[0]

            # determine the direction of the trade
            if dir == 1:
                target_delta = self.delta_long
            else:
                target_delta = self.delta_short

            # calculate an individual strangle
            df_strangle = calc_strangle(self.otm_options[ix_underlying], target_delta)
            df_strangle['direction'] = dir
            
            # adding strangle to dict
            trades[ix_underlying] = df_strangle
        
        self.strangle_trades = trades
        return(None)

    
    def calc_trade_sizes(self):
        # creating column in df directions to hold size and quantity
        self.underlyings['size'] = np.nan
        self.underlyings['quantity'] = np.nan
        
        # number of underlyings to trade
        num_und= len(self.underlyings)

        # iterating through all underlyings and calculating the trade size
        for ix_underlying in self.strangle_trades:
            #df_strangle = self.strangle_trades[ix_underlying]
            
            # the strangle price is the sum of the mid prices
            #strangle_price = df_strangle['mid'].sum()
            strangle_price = self.strangle_trades[ix_underlying]['mid'].sum()
        
            # will buy or sell premium_budget/num_und per underlying; and at least trade 1
            size = np.round((self.premium_budget / num_und) / (strangle_price * 100), 0)
            if size < 1:
                size = 1
        
            # save the size in the strangle trades
            #df_strangle['size'] = size
            self.strangle_trades[ix_underlying]['size'] = size
            self.underlyings.loc[self.underlyings['underlying'] == ix_underlying, 'size'] = size
        
            # quantity will take into account direction and size
            #quantity = df_strangle['direction'][0] * size #df_strangle['size']
            #df_strangle['quantity'] = quantity
            quantity = self.strangle_trades[ix_underlying]['direction'][0] * size
            self.strangle_trades[ix_underlying]['quantity'] = quantity
            self.underlyings.loc[self.underlyings['underlying'] == ix_underlying, 'quantity'] = quantity

        return(None)


    def calc_strangle_histories(self):
        self.strangle_histories = {}

        # iterate through all the strangles
        for ix_underlying in self.strangle_trades:
            sh = []
            # for each trade in a strangle, get its trade_pnl_history
            for index, row in self.strangle_trades[ix_underlying].iterrows():
                und = row['underlying']
                exp = row['expiration']
                cp = row['cp']
                k = row['strike']
                qty = row['quantity']
                th = calc_trade_pnl_history(und, exp, cp, k, self.execution, self.last_trade_date, qty)
                sh.append(th)
            # creating a single DataFrame for each strangle
            strangle_history = pd.concat(sh)

            # putting the strangle DataFrame into a Dict, one entry per underlyings
            self.strangle_histories[ix_underlying] = strangle_history
        
        return(None)


    def calc_pnl_by_underlying(self):
        # looping through all the strangle trades
        for ix_underlying in self.strangle_histories:
            df_strangle_history = self.strangle_histories[ix_underlying]
            # calculating the daily bid-ask PNLs
            df_strangle_daily_pnl_bid_ask = \
                (
                df_strangle_history
                    .groupby('trade_date')[['dollar_pnl_bid_ask']].sum()
                    .reset_index()
                )
            # calculating the daily mid PNLs
            df_strangle_daily_pnl_mid = \
                (
                df_strangle_history
                    .groupby('trade_date')[['dollar_pnl_mid']].sum()
                    .reset_index()
                )
            # summing up the daily pnls for a weekly total pnls
            strangle_pnl_bid_ask = df_strangle_daily_pnl_bid_ask['dollar_pnl_bid_ask'].sum()
            strangle_pnl_mid = df_strangle_daily_pnl_mid['dollar_pnl_mid'].sum()
            # saving the weekly total PNL
            self.underlyings.loc[self.underlyings['underlying'] == ix_underlying, 'pnl_bid_ask'] = strangle_pnl_bid_ask
            self.underlyings.loc[self.underlyings['underlying'] == ix_underlying, 'pnl_mid'] = strangle_pnl_mid

        return(None)

    def calc_trial_daily_pnls(self):
        underlying_pnls = []
        # iterating through strangle histories
        for ix_underlying in self.strangle_histories:
            df = self.strangle_histories[ix_underlying]
            underlying_pnls.append(df)
        # putting all strangle histories into a single DataFrame
        df_underlying_pnls = pd.concat(underlying_pnls)

        # calculating daily PNLs for entire trial
        self.trial_daily_pnls = \
            (
            df_underlying_pnls.groupby(['trade_date'])[['dollar_pnl_bid_ask', 'dollar_pnl_mid']].sum()
            .reset_index()
            )
        
        return(None)
    
    def calc_trial_weekly_pnl(self):
        # calculating PNL for entire trial
        self.trial_weekly_pnl_bid_ask = self.trial_daily_pnls['dollar_pnl_bid_ask'].sum()
        self.trial_weekly_pnl_mid = self.trial_daily_pnls['dollar_pnl_mid'].sum()

        return(None)




def main():
    wt = WeeklyTrial()
    wt.calc_chain_history()
    print(wt.chain_history)
    
    wt.calc_vol_premium_forecast()
    print(wt.chain_history)
    
    wt.calc_underlyings_to_trade()
    print(wt.underlyings)
    
    wt.calc_all_otm_options()
    print(wt.otm_options)
    
    wt.calc_all_strangle_trades()
    print(wt.strangle_trades)
    
    wt.calc_trade_sizes()
    print(wt.underlyings)
    print(wt.strangle_trades)
    
    wt.calc_strangle_histories()
    print(wt.strangle_histories)
    
    wt.calc_pnl_by_underlying()
    print(wt.underlyings)
    
    wt.calc_trial_daily_pnls()
    print(wt.trial_daily_pnls)
    
    wt.calc_trial_weekly_pnl()
    print(wt.trial_weekly_pnl_bid_ask)
    print(wt.trial_weekly_pnl_mid)

    # universe = ['DIA',
    # 'IWM',
    # 'QQQ',
    # 'SPY',
    # 'EEM',
    # 'EFA',
    # 'EWW',
    # 'EWY',
    # 'EWZ',
    # 'FXE',
    # 'FXI',
    # 'FXY',
    # 'GDX',
    # 'GLD',
    # 'IYR',
    # 'SLV',
    # 'SMH',
    # 'TLT',
    # 'USO',
    # 'XBI',
    # 'XHB',
    # 'XLB',]
    # expiration = '2010-12-23'
    # last_trade_date = '2010-12-23'
    # execution = '2010-12-17'
    # #universe = ['DIA','IWM','QQQ','SPY']
    # leg_max = 5 # the maximum number of longs and shorts (for the initial iteration, since I am focused on a small universe this won't matter)
    # delta_long = 0.1 # delta of long strangles
    # delta_short = 0.1 # delta of short strangles
    # premium_budget = 2000

    # wt = WeeklyTrial( 
    #     expiration = expiration,
    #     last_trade_date = last_trade_date,
    #     execution = execution,
    #     universe = universe,
    #     leg_max = leg_max,
    #     delta_long = delta_long, # delta of long strangles
    #     delta_short = delta_short, # delta of short strangles
    #     premium_budget = premium_budget
    # )
    # wt.calc_all()
    # wt = WeeklyTrial()
    # wt.calc_all()


if __name__ == "__main__":
    main()
