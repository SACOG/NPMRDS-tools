/*
Post processing for time stamp data for NPMRDS
1 - load into temporary staging table in which time stamp is loaded as string
2 - copy from staging table into final table, in the process converting
	string timestamp into SQL Server datetime timestamp.

**THIS SCRIPT COMPLETES ONLY STEP 2**
*/

INSERT INTO {1} --name of final table
SELECT
	tmc_code,
	REPLACE(measurement_tstamp, '''','') AS measurement_tstamp,
	speed,
	historical_average_speed,
	reference_speed,
	travel_time_seconds,
	data_density	
FROM {0} --name of staging table

DROP TABLE {0} --remove staging table when finished to clean up




