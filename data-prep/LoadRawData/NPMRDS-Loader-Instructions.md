# Using the NPMRDS Data Loader

## Version Notes
* Python version: 3.x
* NPMRDS version: 2.0 (Inrix, effective Feb 2017)

## Dependencies:

**Python Packages**:
* pyodbc
* dbfread

**Other Dependences**
* *Microsoft SQL Server* - This loader assumes you will be using SQL Server DBMS. It will not work on other DBMS platforms (e.g. Postgres, MySQL, etc.), though you can probably modify the code to do so without too much issue if you are familiar with those systems.


* *SQL Server Bulk Copy Program (BCP)* The NPMRDS loader tool relies on SQL Server's Bulk Copy Program (BCP) to quickly and seamlessly load model output tables into SQL Server. Before running the ILUT tool, you must [download the BCP utility from Microsoft](https://docs.microsoft.com/en-us/sql/tools/bcp-utility?view=sql-server-ver15).


    * *Note -- if this link does not work, simply search for "SQL Server BCP
    utility"*

## Using the NPMRDS Data Loader

*Setup configuration*

If you've never used the data loader on your machine, you must first set the following parameters in load_raw_npmrds.py:

1. DataSet.server - set to the name of the instance of SQL Server you're connecting to
2. DataSet.database - set to the name of the database you're loading to

*Normal run instructions*

1. Unzip the downloaded NPMRDS data (extract to a new child folder; don't unzip everything to the current folder)
2. Open "data_load_parameters.csv" and update the input parameter values as applicable, then run the script.

*Specifying columns*

As of January 2022, the travel time data table uses the following columns. If the data table you download has columns that are different, the table will not load correctly to the database.

* tmc_code
* measurement_tstamp
* speed
* reference_speed
* travel_time_seconds
* data_density





