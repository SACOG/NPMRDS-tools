# -*- coding: utf-8 -*-
#--------------------------------
# Name: TMC_links_fromStartEndCoords.py
# Purpose: Make 'stick' links of TMCs based on start/end lat/long column values
#          After running:
#                -Join TMC_identification.csv to output
#                -Remove any duplicate fields
#                -Export as new feature class
#                -From exported feature class, delete all NHS links (e.g., f_system is not null)
#                -Merge with NHS true-shape version of TMCs, doing appropriate field mapping
#                -Do custom fixes as needed where true-shape TMCs needed but not available
                
                
#           
# Author: Darren Conly
# Last Updated: <date>
# Updated by: <name>
# Copyright:   (c) SACOG
# Python Version: 3.x
#--------------------------------

import datetime as dt
import arcpy
import pandas as pd
from GetLineDir import GetAngle

arcpy.env.overwriteOutput = True

start_time = str(dt.datetime.now().strftime('%m%d%Y_%H%M'))

arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb'
tmc_csv = r"P:\NPMRDS data\Raw Downloads\DynamicData_15Min\2018\TMC_Identification_removeDupes.csv"

output_fc = 'TMC_from_latlong_sacogRegn{}'.format(start_time)

fld_tmc = "tmc"
fld_start_lat = "start_latitude"
fld_start_lon = "start_longitude"
fld_end_lat = "end_latitude"
fld_end_lon = "end_longitude"
fld_dir = "Dir" #CARDINAL Direction based on lat/long

#define projections being used
sr_in = arcpy.SpatialReference(4326) #4326 = wgs84 projection
sr_sacog = arcpy.SpatialReference(2226) #2226 = sacog projection (CA state plane 1983 zone 2)

#create FC for links with specified fields
print("creating line FC {}...".format(output_fc))
arcpy.CreateFeatureclass_management(arcpy.env.workspace, output_fc, "POLYLINE",
                                    "", "", "", sr_sacog)

arcpy.AddField_management(output_fc, fld_tmc, "TEXT")
arcpy.AddField_management(output_fc, fld_start_lat, "FLOAT")
arcpy.AddField_management(output_fc, fld_start_lon, "FLOAT")
arcpy.AddField_management(output_fc, fld_end_lat, "FLOAT")
arcpy.AddField_management(output_fc, fld_end_lon, "FLOAT")

#set up insert cursor

cur_fields = ["SHAPE@", fld_tmc, fld_start_lat, fld_start_lon, fld_end_lat, fld_end_lon]
in_cur = arcpy.da.InsertCursor(output_fc, cur_fields)

df_tmcs = pd.read_csv(tmc_csv)

#for each TMC in CSV:
print("inserting new lines into {}...".format(output_fc))
for index, row in df_tmcs.iterrows():
    
    #retrieve lat/long values from TMC CSV
    start_lat = row[fld_start_lat]
    start_lon = row[fld_start_lon]
    end_lat = row[fld_end_lat]
    end_lon = row[fld_end_lon]
    
    #create points from lat/longs
    pt_start = arcpy.Point(start_lon, start_lat)
    pt_end = arcpy.Point(end_lon, end_lat)
    
    #create line from points
    seg_geom = arcpy.Polyline(arcpy.Array([pt_start, pt_end]), sr_in)
    
    #change the projectsion based on SACOG projection (2226)
    seg_geom = seg_geom.projectAs(sr_sacog)
    
    #get any other fields you want from TMC CSV
    tmc = row[fld_tmc]
    
    #insert into the new FC
    attribs = (seg_geom, tmc, start_lat, start_lon, end_lat, end_lon)
    in_cur.insertRow(attribs)

del in_cur


print("adding cardinal direction data...")

output_fc_wdirecn = f"{output_fc}_wdirn"
angle_builder = GetAngle(output_fc, angle_field='c_angle', text_dir_field='Link_Dir')
angle_builder.add_direction_data(output_fc_wdirecn)

#get_dir.get_card_dir("c_angle", output_fc, fld_dir)

print("sucess!")