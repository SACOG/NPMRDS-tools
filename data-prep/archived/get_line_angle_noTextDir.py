# -*- coding: utf-8 -*-
"""
Created on Sun Feb 10 10:31:03 2019

@author: dconly

Purpose: Get cardinal angle of input lines based on their endpoints. Note that this
will not factor in curves between each line's endpoints
"""

from datetime import datetime as dt
import math
import arcpy


arcpy.env.overwriteOutput = True
arcpy.env.qualifiedFieldNames = False

class GetAngle(object):
    def __init__(self, line_fc_in, angle_field):
        self.line_fc_in = line_fc_in
        self.angle_field = angle_field
    
    def field_exists(self):
        fieldList = arcpy.ListFields(self.line_fc_in, self.angle_field)
        fieldCount = len(fieldList)
        if (fieldCount >= 1):  # If there is one or more of this field return true
            return True
        else:
            return False
    
    def get_card_dir(dir_angle): #0 degrees is straight east, not north
        if dir_angle >= -45 and dir_angle < 45:
            link_angle = "E"
        elif dir_angle >= 45 and dir_angle < 135:
            link_angle = "N"
        elif dir_angle >= 135 or dir_angle < -135:
            link_angle = "W"
        elif dir_angle >= -135 and dir_angle < -45:
            link_angle = "S"
        else:
            link_angle = "unknown"
        
        return link_angle
    
    
    #add angle and direction fields to input links
    def add_angle_data(self):
        
        tmc_fc_out = "{}_w_angle{}".format(self.line_fc_in,start_time)
        
        #don't overwrite original TMC layer--make new one
        arcpy.CopyFeatures_management(self.line_fc_in, tmc_fc_out)
        
        if self.field_exists():
            print("field {} already exists. Overwriting...".format(self.angle_field))
        else:
            arcpy.AddField_management(tmc_fc_out, self.angle_field, "FLOAT")
            
        fields = [field.name for field in arcpy.ListFields(tmc_fc_out)] 
        fields.append("SHAPE@")
        
        counter = 0
        print("adding angle field to TMCs...")
        with arcpy.da.UpdateCursor(tmc_fc_out,fields) as tmc_uc:
            for row in tmc_uc:
                counter += 1
                start_lat = row[fields.index("SHAPE@")].firstPoint.Y
                start_lon = row[fields.index("SHAPE@")].firstPoint.X
                end_lat = row[fields.index("SHAPE@")].lastPoint.Y
                end_lon = row[fields.index("SHAPE@")].lastPoint.X
                #print(start_lat, start_lon, end_lat, end_lon)
                
                xdiff = end_lon - start_lon
                ydiff = end_lat - start_lat
                link_angle = math.degrees(math.atan2(ydiff,xdiff))
    
                row[fields.index(self.angle_field)] = link_angle
                
                tmc_uc.updateRow(row)
        
        print("Added cardinal angle data to {} TMCs.\n".format(counter))


if __name__ == '__main__':
    workspace = r'P:\NPMRDS data\NPMRDS_GIS\scratch.gdb'
    
    line_fc_in = 'TMCs_2017'   
    angle_field = 'c_angle' #field that will have cardinal angle data added to it
      
    #start program
    start_time = dt.now().strftime("%m%d%Y_%H%M")
    
    arcpy.env.workspace = workspace
    
    add_to_tmc = GetAngle(line_fc_in, angle_field)
    
    add_to_tmc.add_angle_data()
    
    
