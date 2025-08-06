"""
Name: pandas2sqltable.py
Purpose: Make dataframe from SQL Server query results
    https://docs.microsoft.com/en-us/sql/machine-learning/data-exploration/python-dataframe-sql-server?view=sql-server-ver15
        
          
Author: Darren Conly
Last Updated: Apr 2021
Updated by: <name>
Copyright:   (c) SACOG
Python Version: 3.x
"""
from time import perf_counter as perf

import pandas as pd
import urllib
import pyodbc
import re

import sqlalchemy as sqla # needed to run pandas df.to_sql() function

def get_odbc_driver():
    # gets name of ODBC driver, with name "ODBC Driver <version> for SQL Server"
    drivers = [d for d in pyodbc.drivers() if 'ODBC Driver ' in d]
    
    if len(drivers) == 0:
        errmsg = f"ERROR. No usable ODBC Driver found for SQL Server." \
        f"drivers found include {drivers}. Check ODBC Administrator program" \
        "for more information."
        
        raise Exception (errmsg)
    else:
        d_versions = [re.findall('\d+', dv)[0] for dv in drivers] # [re.findall('\d+', dv)[0] for dv in drivers]
        latest_version = max([int(v) for v in d_versions])
        driver = f"ODBC Driver {latest_version} for SQL Server"
    
        return driver
    
# extract SQL Server query results into a pandas dataframe   
def sqlqry_to_df(query_str, dbname, servername='SQL-SVR', trustedconn='yes'):   
    # consider using connectorx for this; supposedly makes loading much faster
    # https://sfu-db.github.io/connector-x/intro.html

    driver = get_odbc_driver()  

    conn_str = f"DRIVER={driver};" \
        f"SERVER={servername};" \
        f"DATABASE={dbname};" \
        f"Trusted_Connection={trustedconn}"
        
    conn_str = urllib.parse.quote_plus(conn_str)
    engine = sqla.create_engine(f"mssql+pyodbc:///?odbc_connect={conn_str}")
       
    start_time = perf()

    # create SQL table from the dataframe
    print("Executing query. Results loading into dataframe...")
    try:
        df = pd.read_sql_query(sql=query_str, con=engine)
    except ResourceClosedError:
        msg = """ResourceClosedError. Ensure that the query returns rows and that you have the following at the start of your query:
        SET ANSI_WARNINGS OFF 
        SET NOCOUNT ON
        """
        raise Exception(msg)
        
    rowcnt = df.shape[0]
    
    et_mins = round((perf() - start_time) / 60, 2)
    print(f"Successfully executed query in {et_mins} minutes. {rowcnt} rows loaded into dataframe.")
    
    return df
    



if __name__ == '__main__':
    
    #==========Make dataframe from SQL Server query========
    db = 'NPMRDS'
    qry = 'SELECT TOP 10 * FROM npmrds_2017_alltmc_trucks'
    
    tdf = sqlqry_to_df(qry, db)
    
    
    
        
    
    
