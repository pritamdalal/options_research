-- -- chain_history
-- select *
-- from chain_history
-- where trade_date = '2017-08-04'
-- and expiration = '2017-08-11'
-- and underlying in ('SPY', 'IWM', 'QQQ', 'DIA')

-- -- otm_option
-- select *
-- from otm_history
-- where trade_date = '2017-08-04'
-- and expiration = '2017-08-11'
-- and underlying = 'IWM'
-- order by strike;

-- -- -- option_pnl_history
-- select *
-- from option_pnl_history
-- where underlying = 'QQQ'
-- and expiration = '2017-08-11'
-- and cp = 'call'
-- and strike = 144.5
-- and trade_date >= '2017-08-04'

