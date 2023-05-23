
--drop staging table if exists
IF OBJECT_ID('{0}', 'U') IS NOT NULL 
DROP TABLE {0};


--drop final table if exists
IF OBJECT_ID('{1}', 'U') IS NOT NULL 
DROP TABLE {1};

CREATE TABLE {0} ( --name of staging table
	tmc varchar(9) NULL,
	road varchar(max) NULL,
	direction varchar(max) NULL,
	intersection varchar(max) NULL,
	state char(2) NULL,
	county varchar(10) NULL,
	zip int NULL,
	start_latitude real NULL,
	start_longitude real NULL,
	end_latitude real NULL,
	end_longitude real NULL,
	miles real NULL,
	road_order real NULL,
	timezone_name varchar(max) NULL,
	type varchar(5) NULL,
	country varchar(3) NULL,
	tmclinear int NULL,
	frc smallint NULL,
	border_set varchar(1) NULL,
	f_system smallint NULL,
	urban_code int NULL,
	faciltype smallint NULL,
	structype smallint NULL,
	thrulanes smallint NULL,
	route_numb smallint NULL,
	route_sign smallint NULL,
	route_qual smallint NULL,
	altrtename varchar(max) NULL,
	aadt int NULL,
	aadt_singl smallint NULL,
	aadt_combi smallint NULL,
	nhs smallint NULL,
	nhs_pct smallint NULL,
	strhnt_typ smallint NULL,
	strhnt_pct smallint NULL,
	truck smallint NULL,
	isprimary smallint NULL,
	active_start_date varchar(max) NULL,
	active_end_date varchar(max) NULL,
	thrulanes_unidir smallint NULL,
	aadt_unidir int NULL,
	aadt_singl_unidir int NULL,
	aadt_combi_unidir int NULL
)

CREATE TABLE {1} ( --name of final table
	tmc varchar(9) NULL,
	road varchar(max) NULL,
	direction varchar(max) NULL,
	intersection varchar(max) NULL,
	state char(2) NULL,
	county varchar(10) NULL,
	zip int NULL,
	start_latitude real NULL,
	start_longitude real NULL,
	end_latitude real NULL,
	end_longitude real NULL,
	miles real NULL,
	road_order real NULL,
	timezone_name varchar(max) NULL,
	type varchar(5) NULL,
	country varchar(3) NULL,
	tmclinear int NULL,
	frc smallint NULL,
	border_set varchar(1) NULL,
	f_system smallint NULL,
	urban_code int NULL,
	faciltype smallint NULL,
	structype smallint NULL,
	thrulanes smallint NULL,
	route_numb smallint NULL,
	route_sign smallint NULL,
	route_qual smallint NULL,
	altrtename varchar(max) NULL,
	aadt int NULL,
	aadt_singl smallint NULL,
	aadt_combi smallint NULL,
	nhs smallint NULL,
	nhs_pct smallint NULL,
	strhnt_typ smallint NULL,
	strhnt_pct smallint NULL,
	truck smallint NULL,
	isprimary smallint NULL,
	active_start_date datetime NULL,
	active_end_date datetime NULL
)


