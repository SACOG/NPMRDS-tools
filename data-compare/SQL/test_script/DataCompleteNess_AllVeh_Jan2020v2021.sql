/*
Name: DataCompleteNessByHOD_PaxVeh.sql
Purpose: For indicated analysis periods (days of week, hours of day, months of year, etc) get
the total number of possible speed analysis epochs. This allows user to get a better sense of
data completeness, e.g., the total number of epochs with data out of the total number of possible epochs

INSTRUCTIONS:
	1 - Insert the query that creates the #calendar_tbl at the beginning. Use the same calendar table
		throughout the rest of your query, applying filters to it as needed.
	2 - specify start and end dates
	3 - specify epoch duration in minutes
	4 - for query of resulting calendar table, specify same hour/month/day filters you apply
		to your main query
	5 - choose the correct tmc vintage and travel time tables you want to run the test on
           
Author: Darren Conly
Last Updated: Jan 2021
Updated by: <name>
Copyright:   (c) SACOG
SQL Flavor: SQL Server
*/

USE NPMRDS
GO

--=======QUERY TO GENERATE ROWS OF EVERY HOUR FOR SPECIFIED TIME PERIOD=================
DECLARE @DataYear INT = 2020
DECLARE @EpochLenMins INT = 15

--variables that don't need editing very often, assuming you want 1 calendar year of data
DECLARE @StartDate AS DATETIME = DATETIMEFROMPARTS(@DataYear,1,1,0,0,0,0) --(year, month, day, hour, mins, secs)
DECLARE @EndDate AS DATETIME = DATETIMEFROMPARTS(@DataYear,1,31,23,59,59,999)
DECLARE @EpochsPerHour AS INT = 60 / @EpochLenMins
;

--recursive CTE query to get all dates in year
WITH dates AS (
    SELECT @StartDate AS date_val
    UNION ALL
    SELECT DATEADD(HOUR, 1, date_val)
	FROM dates
    WHERE date_val < @EndDate
)

SELECT * 
INTO #calendar_tbl
FROM dates
OPTION (MAXRECURSION 10000) --~8,800 hours in a year; max possible recursion is 32,000 rows

--total possible epochs in a year
DECLARE @AnnualEpochs AS INT = (SELECT COUNT(*) * @EpochsPerHour FROM #calendar_tbl)

--===========Data completeness by month for each TMC=================

--SELECT
--	DATEPART(mm, date_val) AS month,
--	COUNT(*) * @EpochsPerHour AS poss_epochs
--INTO #tot_epochs_x_month
--FROM #calendar_tbl
--GROUP BY DATEPART(mm, date_val)


--table with total possible epochs over course of year for each hour of the day
SELECT
	DATEPART(hh, date_val) AS hod,
	COUNT(date_val) * @EpochsPerHour AS poss_epochs_hod
INTO #epochs_x_hod
FROM #calendar_tbl
GROUP BY DATEPART(hh, date_val)


--make cross table of TMCs with all 24 hours for each TMC
SELECT
	tmc.tmc,
	tmc.road,
	tmc.f_system,
	tmc.nhs,
	eh.hod as hour_of_day,
	eh.poss_epochs_hod,
	@DataYear AS data_year
INTO #tmc_timeprd_xjoin
FROM npmrds_2020_alltmc_txt tmc
	CROSS JOIN #epochs_x_hod eh

--compare, for each TMC, total observed epochs vs. total possible epochs for the year
SELECT
	xj.tmc,
	xj.road,
	xj.f_system,
	xj.data_year,
	xj.hour_of_day,
	xj.poss_epochs_hod,
	COUNT(tt.measurement_tstamp) AS obs_epochs,
	COUNT(tt.measurement_tstamp) * 1.0 / xj.poss_epochs_hod AS data_compl_pct
INTO #data_to_pivot
FROM #tmc_timeprd_xjoin xj
	LEFT JOIN npmrds_2020_alltmc_paxtruck_comb tt
		ON xj.tmc = tt.tmc_code
			AND xj.hour_of_day = DATEPART(hh, tt.measurement_tstamp)
	--JOIN #epochs_x_hod eh
	--	ON eh.hod = DATEPART(hh, tt.measurement_tstamp)
WHERE xj.nhs = 1
	AND DATEPART(mm, tt.measurement_tstamp) = '1'
GROUP BY xj.tmc,
	xj.road,
	xj.f_system,
	xj.data_year,
	xj.hour_of_day,
	xj.poss_epochs_hod
ORDER BY
	xj.tmc, xj.hour_of_day



--make pivot table showing data completness pct by hour of day
SELECT * FROM (
	SELECT
		--tmc,
		--road,
		f_system,	
		data_year,
		hour_of_day,
		ISNULL(data_compl_pct, 0) AS data_compl_pct
	FROM #data_to_pivot
	) src
PIVOT (
	AVG(data_compl_pct) FOR hour_of_day
	IN (
		[0] ,
		[1] ,
		[2] ,
		[3] ,
		[4] ,
		[5] ,
		[6] ,
		[7] ,
		[8] ,
		[9] ,
		[10] ,
		[11] ,
		[12] ,
		[13] ,
		[14] ,
		[15] ,
		[16] ,
		[17] ,
		[18] ,
		[19] ,
		[20] ,
		[21] ,
		[22] ,
		[23] 
		)
	) piv

--select * from #data_to_pivot

SELECT
	f_system,	
	data_year,
	hour_of_day,
	AVG(ISNULL(data_compl_pct, 0)) AS avg_data_compl_pct
FROM #data_to_pivot
GROUP BY f_system, data_year, hour_of_day

/*
DROP TABLE #calendar_tbl
DROP TABLE #epochs_x_hod
DROP TABLE #data_to_pivot
DROP TABLE #tmc_timeprd_xjoin
*/





