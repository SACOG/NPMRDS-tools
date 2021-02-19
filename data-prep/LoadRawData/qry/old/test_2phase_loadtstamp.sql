CREATE TABLE test_tt_tbl ( --name of final table
	tmc_code varchar(9) NULL,
	measurement_tstamp datetime NULL,
	speed real NULL,
	average_speed real NULL,
	reference_speed real NULL,
	travel_time_seconds real NULL,
	data_density varchar(1) NULL
)


INSERT INTO test_tt_tbl --name of final table
SELECT
	tmc_code,
	REPLACE(measurement_tstamp, '''','') AS measurement_tstamp,
	speed,
	average_speed,
	reference_speed,
	travel_time_seconds,
	data_density	
FROM TEST_BCP_trucktbl --name of temporary table

--DROP TABLE {1} --name of temporary table
--DROP TABLE test_tt_tbl