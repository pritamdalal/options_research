create table option_price(
	UnderlyingSymbol varchar(10) null,
    UnderlyingPrice real null,
    Flags varchar(3) null,
    OptionSymbol varchar(25) null,
    CP varchar(4) null,
    Expiration date null,
    DataDate date null,
    Strike real null,
    LastPx real null,
    BidPx real null,
    AskPx real null,
    Volume bigint null,
    OpenInterest bigint null,
    T1OpenInterest bigint null
);