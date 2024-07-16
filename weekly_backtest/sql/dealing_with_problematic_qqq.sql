-- select distinct underlying
-- from option_pnl_history;


-- select * from option_pnl_history limit 10;

-- select
-- 	underlying,
-- 	min(trade_date),
-- 	max(trade_date)
-- from option_pnl_history
-- group by underlying;


-- select *
-- from option_pnl_history
-- where underlying = 'SPY'
-- and trade_date='2021-12-16';


-- select *
-- from option_pnl_history
-- where underlying='SPY'
-- and expiration='2021-12-17'
-- and cp='call'
-- and strike='255'
-- order by trade_date;

-- delete
-- from option_pnl_history
-- where underlying='GLD';

-- select *
-- from otm_history
-- where underlying = 'QQQ'
-- and expiration = '2014-12-20'
-- and cp = 'call'
-- and strike < 94
-- and strike > 93
-- order by trade_date;

-- select *
-- from option_price
-- where underlyingsymbol='QQQ'
-- and strike>93
-- and strike<94;


-- select * 
-- from option_price 
-- where underlyingsymbol = 'QQQ' 
-- and expiration = '2014-12-20' 
-- and strike = 93.63 
-- and cp = 'call'; 
-- and datadate >= '2014-02-27' 
-- and datadate <= '2014-12-20' 
-- order by datadate;


-- select distinct strike
-- from otm_history
-- where underlying = 'QQQ'
-- order by strike;


-- select distinct strike
-- from option_price
-- where underlyingsymbol = 'QQQ'
-- order by strike;


-- select *
-- from otm_history
-- where underlying = 'QQQ'
-- and expiration = '2014-12-20'
-- and trade_date = '2014-02-27'
-- order by strike;


-- select distinct strike
-- from option_pnl_history
-- where underlying = 'QQQ'
-- order by strike;


-- select distinct strike
-- from otm_history
-- where underlying = 'QQQ'
-- and abs(strike-34.63) < 0.01

-- select distinct underlying
-- from option_pnl_history;