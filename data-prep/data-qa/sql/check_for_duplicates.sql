/*
Name: check_for_duplicates.sql
Purpose: Check for duplicate time entries, where the same TMC during the same epoch appears in two
	distinct records, e.g., two records for TMC XYZ for 11/5/2016 at 1:00am.
           
Author: Darren Conly
Last Updated: Mar 2021
Updated by: <name>
Copyright:   (c) SACOG
SQL Flavor: SQL Server
*/

--detailed excerpt of duplicates during specific hour on specific date
select * from npmrds_2016_alltmc_paxtruck_comb
where tmc_code = '105+04687' 
	and datepart(hh, measurement_tstamp) = '1' 
	and datepart(mm, measurement_tstamp) = '11' 
	and datepart(dd, measurement_tstamp) = '6'
order by measurement_tstamp

--detailed excerpt of duplicates during specific hour on specific date
select * from npmrds_2017_alltmc_paxtruck_comb
where tmc_code = '105+04712' 
	and datepart(hh, measurement_tstamp) = '1' 
	and datepart(mm, measurement_tstamp) = '11' 
	and datepart(dd, measurement_tstamp) = '5'
order by measurement_tstamp


--summaries listing all TMCs with duplication in date-time-TMC code
SELECT
	tmc_code,
	measurement_tstamp,
	COUNT(*) AS epoch_cnt
FROM npmrds_2016_alltmc_paxtruck_comb
GROUP BY tmc_code,
	measurement_tstamp
HAVING COUNT(*) > 1

SELECT
	tmc_code,
	measurement_tstamp,
	COUNT(*) AS epoch_cnt
FROM npmrds_2020_alltmc_paxtruck_comb
GROUP BY tmc_code,
	measurement_tstamp
HAVING COUNT(*) > 1
