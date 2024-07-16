-- select *
-- from option_pnl_history
-- where year(trade_date) = 2018
-- limit 10;


-- select distinct underlying
-- from option_pnl_history;

select * 
from option_pnl_history
where underlying = 'SPY'
and expiration = '2010-06-11'
and cp = 'put'
and strike = 100
and trade_date >= '2010-06-04'
and trade_date <= '2010-06-11';

-- select * 
-- from option_pnl_history
-- where underlying = 'SPY'
-- and expiration = '2010-06-11'
-- and cp = 'put'
-- and strike = 100
-- order by trade_date;