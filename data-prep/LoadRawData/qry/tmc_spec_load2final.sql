/*
Post processing for time stamp data for NPMRDS
1 - load into temporary staging table in which time stamp is loaded as string
2 - copy from staging table into final table, in the process converting
	string timestamp into SQL Server datetime timestamp.

**THIS SCRIPT COMPLETES ONLY STEP 2**
*/

INSERT INTO {1} --name of final table
SELECT
	tmc,
	road,
	direction,
	intersection,
	state,
	county,
	zip,
	start_latitude,
	start_longitude,
	end_latitude,
	end_longitude,
	miles,
	road_order,
	timezone_name,
	type,
	country,
	tmclinear,
	frc,
	border_set,
	f_system,
	urban_code,
	faciltype,
	structype,
	thrulanes,
	route_numb,
	route_sign,
	route_qual,
	altrtename,
	aadt,
	aadt_singl,
	aadt_combi,
	nhs,
	nhs_pct,
	strhnt_typ,
	strhnt_pct,
	truck,
	isprimary,
	REPLACE(active_start_date, '''','') AS active_start_date,
	REPLACE(active_end_date, '''','') AS active_end_date
FROM {0} --name of staging table

DROP TABLE {0} --remove staging table when finished to clean up




