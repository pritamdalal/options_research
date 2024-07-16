create table weekly_expiration(
	underlying varchar(10) null,
    monthly boolean null,
    expiration date null,
    last_trade_date date null,
    execution_date date null
);