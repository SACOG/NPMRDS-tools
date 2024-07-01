/*
Post processing for time stamp data for NPMRDS
1 - load into temporary staging table in which time stamp is loaded as string
2 - copy from staging table into final table, in the process converting
	string timestamp into SQL Server datetime timestamp.

	**THIS QUERY JUST CREATES THE TWO TABLES (STAGING AND FINAL)
*/

--drop staging table if exists
IF OBJECT_ID('{0}', 'U') IS NOT NULL 
DROP TABLE {0};


--drop final table if exists
IF OBJECT_ID('{1}', 'U') IS NOT NULL 
DROP TABLE {1};


CREATE TABLE {0} ( --name of staging table
	tmc_code varchar(9) NULL,
	measurement_tstamp varchar(25) NULL,
	speed real NULL,
	historical_average_speed real NULL,
	reference_speed real NULL,
	travel_time_seconds real NULL,
	data_density varchar(1) NULL
)


CREATE TABLE {1} ( --name of final table
	tmc_code varchar(9) NULL,
	measurement_tstamp datetime NULL,
	speed real NULL,
	historical_average_speed real NULL,
	reference_speed real NULL,
	travel_time_seconds real NULL,
	data_density varchar(1) NULL
)




