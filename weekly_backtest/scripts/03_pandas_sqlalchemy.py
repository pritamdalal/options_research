import sqlalchemy
import pandas as pd
from sqlalchemy.sql import text

url = 'postgresql+psycopg2://postgres:$3lfl0v3@localhost:5432/delta_neutral'

engine = sqlalchemy.create_engine(url)

sql = '''
    select * 
    from option_price
    where datadate = '2018-11-01'
    and underlyingsymbol = 'SPY'
    and expiration = '2018-12-21';
'''

with engine.connect() as conn:
    query = conn.execute(text(sql))         
df = pd.DataFrame(query.fetchall())

print(df)