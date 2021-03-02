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
Currently, the is no interface for the Data Loader (time permitting this will improve). In the meantime, you will need to open load_raw_npmrds_data.py in a python editor, fill in the appropriate parameter values near the bottom of the script, and run the script.
