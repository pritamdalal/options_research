-- select * 
-- from weekly_expiration
-- where expiration = '2010-06-11';


-- select *
-- from otm_history
-- where underlying = 'QQQ'
-- and expiration = '2015-12-19'
-- and trade_date = '2015-12-11'
-- order by strike desc;

-- this query grabs the number of OTM option for each underlying on each execution date
-- I port the output of this into a Jupyter notebook entitled
-- "number_otm_option_execution_date.ipynb" and then to some further analysis to find
-- the number of eligible underlyings per expiration date, this will determine the universe
-- of underlyings per execution date
select 
	otm_history.underlying,
	weekly_expiration.monthly,
	weekly_expiration.expiration,
	weekly_expiration.execution_date,
	weekly_expiration.last_trade_date,
	count(otm_history.*) as num_otm
from weekly_expiration
left join otm_history
on weekly_expiration.expiration = otm_history.expiration
and weekly_expiration.execution_date = otm_history.trade_date
-- where otm_history.underlying = 'XRT'
-- and otm_history.expiration = '2010-06-19'
-- and otm_history.trade_date = '2010-06-11'
group by 	
	weekly_expiration.monthly,
	weekly_expiration.expiration,
	weekly_expiration.last_trade_date,
	weekly_expiration.execution_date,
	otm_history.underlying
--having count(otm_history.*) >=5
--and weekly_expiration.expiration = '2017-03-10'
order by
	otm_history.underlying,
	weekly_expiration.expiration;

-- select * 
-- from option_price
-- where datadate='2015-12-11'
-- and underlyingsymbol='SPY';