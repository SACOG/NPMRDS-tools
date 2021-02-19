# -*- coding: utf-8 -*-
"""
Created on Sun Feb 10 10:31:03 2019

@author: dconly

Purpose: Get cardinal angle of TMCs based on their endpoints. Note that this
will not factor in curves between the TMC's endpoints
"""

import datetime as dt
import math
import arcpy


arcpy.env.overwriteOutput = True
arcpy.env.qualifiedFieldNames = False


def field_exists(fc, fieldname):
    fieldList = arcpy.ListFields(fc, fieldname)
    fieldCount = len(fieldList)
    if (fieldCount >= 1):  # If there is one or more of this field return true
        return True
    else:
        return False

def get_card_dir(dir_angle, fc_in, dir_field): #0 degrees is straight east, not north
    print("adding field indicating N/S/E/W direction name...")
    
    #if N/S/E/W field already exists, just overwrite it.
    if field_exists(fc_in,dir_field):
        print("field {} already exists. Overwriting...".format(dir_field))
    else:
        arcpy.AddField_management(fc_in, dir_field, "TEXT")
    
    with arcpy.da.UpdateCursor(fc_in, [dir_angle, dir_field]) as cur:
        for row in cur:
            dir_angle = row[0]
        
            if dir_angle >= -45 and dir_angle < 45:
                dir_name = "E"
            elif dir_angle >= 45 and dir_angle < 135:
                dir_name = "N"
            elif dir_angle >= 135 or dir_angle < -135:
                dir_name = "W"
            elif dir_angle >= -135 and dir_angle < -45:
                dir_name = "S"
            else:
                dir_name = "unknown"
            
            row[1] = dir_name
            
            fc_in.updateRow(row)


#add angle and direction fields to input links
def add_angle_data(tmc_fc_in, lat_start_field, lat_end_field, 
                   lon_start_field, lon_end_field, angle_field):
    
    start_time = str(dt.datetime.now().strftime('%m%d%Y_%H%M'))
    
    tmc_fc_out = "{}_w_angle{}".format(tmc_fc_in,start_time)
    
    #don't overwrite original TMC layer--make new one
    arcpy.CopyFeatures_management(tmc_fc_in, tmc_fc_out)
    
    if field_exists(tmc_fc_out,angle_field):
        print("field {} already exists. Overwriting...".format(angle_field))
    else:
        arcpy.AddField_management(tmc_fc_out, angle_field, "FLOAT")
        
    fields = [field.name for field in arcpy.ListFields(tmc_fc_out)]  
    
    counter = 0
    print("adding angle field to TMCs...")
    with arcpy.da.UpdateCursor(tmc_fc_out,fields) as tmc_uc:
        for row in tmc_uc:
            counter += 1
            start_lat = row[fields.index(lat_start_field)]
            start_lon = row[fields.index(lon_start_field)]
            end_lat = row[fields.index(lat_end_field)]
            end_lon = row[fields.index(lon_end_field)]
            
            xdiff = end_lon - start_lon
            ydiff = end_lat - start_lat
            link_angle = math.degrees(math.atan2(ydiff,xdiff))

            row[fields.index(angle_field)] = link_angle
            
            tmc_uc.updateRow(row)
    
    print("Added cardinal angle data to {} TMCs.\n".format(counter))


if __name__ == '__main__':
    workspace = r'P:\NPMRDS data\NPMRDS_GIS\scratch.gdb'
    
    tmc_in = 'TMCs_2017'
    lat_start_field = 'StartLat'
    lat_end_field = 'EndLat'
    lon_start_field = 'StartLong'
    lon_end_field = 'EndLong'
    
    angle_field = 'c_angle' #field that will have cardinal angle data added to it
      
    #start program
    start_time = dt.datetime.now().strftime("%m%d%Y_%H%M")
    
    arcpy.env.workspace = workspace
    
    add_angle_data(tmc_in, lat_start_field, lat_end_field, 
                   lon_start_field, lon_end_field, angle_field)
    
    
