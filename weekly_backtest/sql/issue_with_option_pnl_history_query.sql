  
select * 
-- from option_pnl_history
-- where underlying = '{underlying}'
-- and expiration = '{expiration}'
-- and cp = '{cp}'
-- and strike = '{strike}'
-- and trade_date >= '{start_date}'
-- and trade_date <= '{end_date}';


select *
from chain_history
where underlying in ('DIA','IWM','QQQ','SPY')
and expiration = '2010-07-02'
and trade_date = '2010-06-25';

select * 
from otm_history
where underlying = 'DIA'
and expiration = '2010-07-02';


select * 
from option_price
where underlyingsymbol = 'DIA'
and expiration = '2010-07-02';


select * 
from option_pnl_history
where underlying = 'QQQ'
and expiration = '2010-06-19'
and cp = 'put'
and strike = 44
and trade_date >= '2010-06-11'
and trade_date <= '2010-06-18';

select * 
from option_price
where underlyingsymbol = 'QQQ'
and expiration = '2010-06-19'
and cp = 'put'
and strike = 44;


select underlying, expiration, cp, strike, first_date 
from (select underlying, expiration, cp, strike,
min(trade_date) as first_date from otm_history
where underlying = 'QQQ'
group by underlying, expiration, cp, strike) as nested
where first_date >= '2010-01-01'
and first_date <= '2018-12-31'
order by underlying, expiration, cp, strike;


(select underlying, expiration, cp, strike,
min(trade_date) as first_date from otm_history
where underlying = 'QQQ'
group by underlying, expiration, cp, strike)






