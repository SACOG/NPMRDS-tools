# -*- coding: utf-8 -*-
"""
# Name: GetLineDir.py
# Purpose: Get cardinal angle and direction (N/S/E/W) of input lines based on their endpoints. Note that this
will not factor in curves between each line's endpoints
#          
#           
# Author: Darren Conly
# Last Updated: 2/13/2019
# Updated by: DC
# Copyright:   (c) SACOG
# Python Version: 3.6
"""

from datetime import datetime as dt
import math
import arcpy


arcpy.env.overwriteOutput = True
arcpy.env.qualifiedFieldNames = False

class GetAngle(object):
    def __init__(self, line_fc_in, angle_field=None, text_dir_field=None):
        self.line_fc_in = line_fc_in
        self.angle_field = angle_field
        self.text_dir_field = text_dir_field
    
    def field_exists(self, field):
        fieldList = arcpy.ListFields(self.line_fc_in, field)
        fieldCount = len(fieldList)
        if (fieldCount >= 1):  # If there is one or more of this field return true
            return True
        else:
            return False
    
    def get_card_dir(self, dir_angle): #0 degrees is straight east, not north
        if dir_angle >= -45 and dir_angle < 45:
            link_dir = "E"
        elif dir_angle >= 45 and dir_angle < 135:
            link_dir = "N"
        elif dir_angle >= 135 or dir_angle < -135:
            link_dir = "W"
        elif dir_angle >= -135 and dir_angle < -45:
            link_dir = "S"
        else:
            link_dir = "unknown"
        
        return link_dir
    
    def get_card_angle(self, start_x, start_y, end_x, end_y):
        '''Based on start and end point coordinates, calculates direction in degrees
        for traveling in straight line between start and end point'''
        xdiff = end_x - start_x
        ydiff = end_y - start_y
        
        angle_degrees = math.degrees(math.atan2(ydiff,xdiff))
        
        return angle_degrees
    
    
    #add angle and direction fields to input links
    def add_direction_data(self, line_fc_out):
        
        #don't overwrite original TMC layer--make new one
        arcpy.CopyFeatures_management(self.line_fc_in, line_fc_out)
        
        #check if angle field exists, make one if no
        if self.field_exists(self.angle_field):
            print("field {} already exists. Overwriting...".format(self.angle_field))
        else:
            arcpy.AddField_management(line_fc_out, self.angle_field, "FLOAT")
        
        #check if text direction (N/S/E/W) field exists, make one if no
        if self.field_exists(self.text_dir_field):
            print("field {} already exists. Overwriting...".format(self.text_dir_field))
        else:
            arcpy.AddField_management(line_fc_out, self.text_dir_field, "TEXT")
            
        fields = [field.name for field in arcpy.ListFields(line_fc_out)] 
        fields.append("SHAPE@")
        
        counter = 0
        print("adding angle field to TMCs...")
        with arcpy.da.UpdateCursor(line_fc_out,fields) as tmc_uc:
            for row in tmc_uc:
                counter += 1
                start_lat = row[fields.index("SHAPE@")].firstPoint.Y
                start_lon = row[fields.index("SHAPE@")].firstPoint.X
                end_lat = row[fields.index("SHAPE@")].lastPoint.Y
                end_lon = row[fields.index("SHAPE@")].lastPoint.X
                #print(start_lat, start_lon, end_lat, end_lon)
                
                link_angle = self.get_card_angle(start_lon, start_lat, end_lon, end_lat)
                link_dir = self.get_card_dir(link_angle)
    
                row[fields.index(self.angle_field)] = link_angle
                row[fields.index(self.text_dir_field)] = link_dir
                
                tmc_uc.updateRow(row)
        
        print("Added cardinal angle data to {} links.\n".format(counter))


if __name__ == '__main__':
    workspace = r'Q:\Big_Data_Pilot_Project\TrafficCounts\GIS\Pro\Validation.gdb'
    
    line_fc_in = 'net_links12162019_1644_pjt'
    angle_field = 'c_angle' #field that will have cardinal angle data added to it
    text_dir_field = 'Link_Dir'
    
    
      
    #start program
    start_time = dt.now().strftime("%m%d%Y_%H%M")
    line_fc_out = "{}_w_angle{}".format(line_fc_in,start_time)
    
    arcpy.env.workspace = workspace
    
    add_to_tmc = GetAngle(line_fc_in, angle_field, text_dir_field)
    
    add_to_tmc.add_direction_data(line_fc_out)
    
    
