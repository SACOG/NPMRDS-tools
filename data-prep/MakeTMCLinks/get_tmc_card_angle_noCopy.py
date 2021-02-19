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

def get_card_dir(dir_angle): #0 degrees is straight east, not north
        
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
    
    return dir_name


#add angle and direction fields to input links
def add_angle_data(tmc_fc_in, lat_start_field, lat_end_field, 
                   lon_start_field, lon_end_field):
    
    angle_field = "c_angle"
    fld_dir_name = "DirName"
    
    dict_new_flds = {angle_field:"FLOAT", fld_dir_name:"TEXT"}
    
    for field, dtype in dict_new_flds.items():
        if field_exists(tmc_fc_in, field):
            print("field {} already exists. Overwriting...".format(angle_field))
        else:
            arcpy.AddField_management(tmc_fc_in, field, dtype)
        
    fields = [field.name for field in arcpy.ListFields(tmc_fc_in)]  
    
    counter = 0
    print("adding angle field to TMCs...")
    with arcpy.da.UpdateCursor(tmc_fc_in,fields) as tmc_uc:
        for row in tmc_uc:
            counter += 1
            start_lat = row[fields.index(lat_start_field)]
            start_lon = row[fields.index(lon_start_field)]
            end_lat = row[fields.index(lat_end_field)]
            end_lon = row[fields.index(lon_end_field)]
            
            xdiff = end_lon - start_lon
            ydiff = end_lat - start_lat
            link_angle = math.degrees(math.atan2(ydiff,xdiff))
            dir_name = get_card_dir(link_angle)
            
            row[fields.index(angle_field)] = link_angle
            row[fields.index(fld_dir_name)] = dir_name
            
            tmc_uc.updateRow(row)
    
    print("Added cardinal angle data to {} TMCs.\n".format(counter))


if __name__ == '__main__':
    workspace = r'P:\NPMRDS data\NPMRDS_GIS\scratch.gdb'
    
    tmc_in = 'TMCs_2017'
    lat_start_field = 'StartLat'
    lat_end_field = 'EndLat'
    lon_start_field = 'StartLong'
    lon_end_field = 'EndLong'
      
    #start program
    start_time = dt.datetime.now().strftime("%m%d%Y_%H%M")
    
    arcpy.env.workspace = workspace
    
    add_angle_data(tmc_in, lat_start_field, lat_end_field, 
                   lon_start_field, lon_end_field)
    
    
