'''
#--------------------------------
# Name: npmrds_project_conflation_invspeed.py
# Purpose: Get distance-weighted average speed from NPMRDS data for PPA project,
#          compared to original script, this gets distance-weighted speed by inverting into hours/mile.
#           Is better than just simple distance-weighted miles per hour, esp. if significant spped variatin across TMCs.
# Author: Darren Conly
# Last Updated: May 2020
# Updated by: <name>
# Copyright:   (c) SACOG
# Python Version: 3.x
#--------------------------------

INSTRUCTIONS:
    1 - Specify workspace (usually an ESRI file geodatabase) under the "if __name__ == '__main__'" section
    2 - in the projectTMCConflation class defintion, under the __init__ function,
            a) go through and update all column names as applicable. If you are using different
            metrics than those shown (e.g., not using LOTTR), you should probably rename the variable
            as well to avoid confusion, or delete all references to the variable if you are not using it.
            
            b) if you want to, adjust the parameters for tmc search distance and buffering distance.
'''
import os
import re
import datetime as dt
import pdb

import arcpy
import pandas as pd


arcpy.env.overwriteOutput = True

dateSuffix = str(dt.date.today().strftime('%m%d%Y'))



# ====================FUNCTIONS==========================================

def trace():
    import sys, traceback, inspect
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]
    # script name + line number
    line = tbinfo.split(", ")[1]
    filename = inspect.getfile(inspect.currentframe())
    # Get Python syntax error
    synerror = traceback.format_exc().splitlines()[-1]
    return line, filename, synerror 

class projectTMCConflation(object):
    def __init__(self, fc_speed_data, fc_project_line, str_project_type):
        self.fc_speed_data = fc_speed_data
        self.fc_projline = fc_project_line
        self.str_project_type = str_project_type
        
        self.projtyp_fwy = "Freeway"
        self.ft2mile = 5280
        
        # speed data attributes
        self.col_ff_speed = "ff_speed"
        self.col_congest_speed = "havg_spd_worst4hrs"
        self.col_reliab_ampk = "lottr_ampk"
        self.col_reliab_md = "lottr_midday"
        self.col_reliab_pmpk = "lottr_pmpk"
        self.col_reliab_wknd = "lottr_wknd"
        self.col_tmcdir = "direction_signd"
        self.col_roadtype = "f_system"  # indicates if road is freeway or not, so that data from freeways doesn't affect data on surface streets, and vice-versa
        
        # if you want the attribute to actually be calculated, include it in this list
        self.flds_speed_data = [self.col_ff_speed, self.col_congest_speed]
        
        self.flds_rel_data = [self.col_reliab_ampk, self.col_reliab_md, self.col_reliab_pmpk, 
                                self.col_reliab_wknd]
        
        
        self.roadtypes_fwy = (1, 2)  # road type values corresponding to freeways (F_system field in raw NPMRDS data as of April 2020)
        self.directions_tmc = ["NORTHBOUND", "SOUTHBOUND", "EASTBOUND", "WESTBOUND"]
        
        self.tmc_select_srchdist = 300 # units in feet. will select TMCs within this distance of project line for analysis.
        self.tmc_buff_dist_ft = 90  # buffer distance, in feet, around the TMCs
        
        self.msg_ok = "OK"
        self.msg_fail = "Failed to complete."  
 
    def get_wtd_speed(self, in_df, in_field, direction, fld_pc_len_ft):
        fielddir = "{}{}".format(direction, in_field)
        
        fld_invspd = "spdinv_hpm"
        fld_pc_tt = "projpc_tt"
        fld_len_mi = "pc_len_mi"
        
        in_df[fld_invspd] = 1/in_df[in_field]  # calculate each piece's "hours per mile", or inverted speed, as 1/speed
            
        # get each piece's travel time, in hours as inverted speed (hrs per mi) * piece distance (mi)
        in_df[fld_len_mi] = in_df[fld_pc_len_ft]/self.ft2mile
        in_df[fld_pc_tt] = in_df[fld_invspd] * in_df[fld_len_mi]
            
        # get total travel time, in hours, for all pieces, then divide total distance, in miles, for all pieces by the total tt
        # to get average MPH for the project
        proj_mph = in_df[fld_len_mi].sum() / in_df[fld_pc_tt].sum()
        
        return {fielddir: proj_mph}
   
 
    def conflate_tmc2projline(self, fl_proj, fl_tmcs_buffd):
    
        out_row_dict = {}
        
        # get length of project
        fld_shp_len = "SHAPE@LENGTH"
        fld_totprojlen = "proj_length_ft"
        
        with arcpy.da.SearchCursor(fl_proj, fld_shp_len) as cur:
            for row in cur:
                out_row_dict[fld_totprojlen] = row[0]
        
        for direcn in self.directions_tmc:
            # https://support.esri.com/en/technical-article/000012699
            
            # temporary files
            scratch_gdb = arcpy.env.scratchGDB
            
            temp_intersctpts = os.path.join(scratch_gdb, "temp_intersectpoints")   # r"{}\temp_intersectpoints".format(scratch_gdb)
            temp_intrsctpt_singlpt = os.path.join(scratch_gdb, "temp_intrsctpt_singlpt") # converted from multipoint to single point (1 pt per feature)
            temp_splitprojlines = os.path.join(scratch_gdb, "temp_splitprojlines") # fc of project line split up to match TMC buffer extents
            temp_splitproj_w_tmcdata = os.path.join(scratch_gdb, "temp_splitproj_w_tmcdata") # fc of split project lines with TMC data on them
            
            fl_splitprojlines = "fl_splitprojlines"
            fl_splitproj_w_tmcdata = "fl_splitproj_w_tmcdata"
            
            # get TMCs whose buffers intersect the project line
            arcpy.SelectLayerByLocation_management(fl_tmcs_buffd, "INTERSECT", fl_proj)
            
            # select TMCs that intersect the project and are in indicated direction
            sql_sel_tmcxdir = "{} = '{}'".format(self.col_tmcdir, direcn)
            arcpy.SelectLayerByAttribute_management(fl_tmcs_buffd, "SUBSET_SELECTION", sql_sel_tmcxdir)
            
            # split the project line at the boundaries of the TMC buffer, creating points where project line intersects TMC buffer boundaries
            arcpy.Intersect_analysis([fl_proj, fl_tmcs_buffd],temp_intersctpts,"","","POINT")
            arcpy.MultipartToSinglepart_management (temp_intersctpts, temp_intrsctpt_singlpt)
            
            # split project line into pieces at points where it intersects buffer, with 10ft tolerance
            # (not sure why 10ft tolerance needed but it is, zero tolerance results in some not splitting)
            arcpy.SplitLineAtPoint_management(fl_proj, temp_intrsctpt_singlpt,
                                              temp_splitprojlines, "10 Feet")
            arcpy.MakeFeatureLayer_management(temp_splitprojlines, fl_splitprojlines)
            
            # get TMC speeds onto each piece of the split project line via spatial join
            arcpy.SpatialJoin_analysis(temp_splitprojlines, fl_tmcs_buffd, temp_splitproj_w_tmcdata,
                                       "JOIN_ONE_TO_ONE", "KEEP_ALL", "#", "HAVE_THEIR_CENTER_IN", "30 Feet")
                                       
            # convert to fl and select records where "check field" col val is not none
            arcpy.MakeFeatureLayer_management(temp_splitproj_w_tmcdata, fl_splitproj_w_tmcdata)
            
            check_field = self.flds_speed_data[0]  # choose first speed value field for checking--if it's null, then don't include those rows in aggregation
            sql_notnull = "{} IS NOT NULL".format(check_field)
            arcpy.SelectLayerByAttribute_management(fl_splitproj_w_tmcdata, "NEW_SELECTION", sql_notnull)
            
            # convert the selected records into a numpy array then a pandas dataframe
            flds_df = [fld_shp_len] + self.flds_speed_data + self.flds_rel_data
            df_spddata = self.esri_object_to_df(fl_splitproj_w_tmcdata, flds_df)
    
            # remove project pieces with no speed data so their distance isn't included in weighting
            df_spddata = df_spddata.loc[pd.notnull(df_spddata[self.flds_speed_data[0]])].astype(float)
            
            # remove rows where there wasn't enough NPMRDS data to get a valid speed or reliability reading
            df_spddata = df_spddata.loc[df_spddata[flds_df].min(axis=1) > 0]
            
            # pdb.set_trace()
            df_to_print = df_spddata[["SHAPE@LENGTH", "ff_speed", "havg_spd_worst4hrs"]]
            
            dir_len = df_spddata[fld_shp_len].sum() #sum of lengths of project segments that intersect TMCs in the specified direction
            out_row_dict["{}_calc_len".format(direcn)] = dir_len #"calc" length because it may not be same as project length
            
            # calculate average speeds for each link--this would be good opportunity for adding travel time too
            for field in self.flds_speed_data:
                sd_dict = self.get_wtd_speed(df_spddata, field, direcn, fld_shp_len)
                out_row_dict.update(sd_dict)
            
            #get distance-weighted average value for each speed/congestion field
            #for PHED or hours of delay, will want to get dist-weighted SUM; for speed/reliability, want dist-weighted AVG
            #ideally this would be a dict of {<field>:<aggregation method>}
            for field in self.flds_rel_data:
                arcpy.AddMessage(field)
                fielddir = "{}{}".format(direcn, field)  # add direction tag to field names
                # if there's speed data, get weighted average value.
                linklen_w_speed_data = df_spddata[fld_shp_len].sum()
                if linklen_w_speed_data > 0: #wgtd avg = sum(piece's data * piece's len)/(sum of all piece lengths)
                    avg_data_val = (df_spddata[field]*df_spddata[fld_shp_len]).sum() \
                                    / df_spddata[fld_shp_len].sum()
    
                    out_row_dict[fielddir] = avg_data_val
                else:
                    out_row_dict[fielddir] = df_spddata[field].mean() #if no length, just return mean speed? Maybe instead just return 'no data avaialble'? Or -1 to keep as int?
                    continue
    
        #cleanup
        fcs_to_delete = [temp_intersctpts, temp_intrsctpt_singlpt, temp_splitprojlines, temp_splitproj_w_tmcdata]
        for fc in fcs_to_delete:
            arcpy.Delete_management(fc)
        return pd.DataFrame([out_row_dict])
        
        
    def simplify_outputs(self, in_df, proj_len_col):
        dirlen_suffix = '_calc_len'
        
        proj_len = in_df[proj_len_col][0]
        
        re_lendir_col = '.*{}'.format(dirlen_suffix)
        lendir_cols = [i for i in in_df.columns if re.search(re_lendir_col, i)]
        df_lencols = in_df[lendir_cols]    
        
        max_dir_len = df_lencols.max(axis = 1)[0] # direction for which project has longest intersect with TMC. assumes just one record in the output
        
        #if there's less than 10% overlap in the 'highest overlap' direction, then say that the project is not on any TMCs (and any TMC data is from cross streets or is insufficient to represent the segment)
        if (max_dir_len / proj_len) < 0.1:
            out_df = pd.DataFrame([-1], columns=['SegmentSpeedData'])
            return out_df.to_dict('records')
        else:
            max_len_col = df_lencols.idxmax(axis = 1)[0] #return column name of direction with greatest overlap
            df_lencols2 = df_lencols.drop(max_len_col, axis = 1)
            secndmax_col = df_lencols2.idxmax(axis = 1)[0] #return col name of direction with second-most overlap (should be reverse of direction with most overlap)
    
            maxdir = max_len_col[:max_len_col.find(dirlen_suffix)] #direction name without '_calc_len' suffix
            secdir = secndmax_col[:secndmax_col.find(dirlen_suffix)]
    
            outcols_max = [c for c in in_df.columns if re.match(maxdir, c)]
            outcols_sec = [c for c in in_df.columns if re.match(secdir, c)]
    
            outcols = outcols_max + outcols_sec
    
            return in_df[outcols].to_dict('records')
        
    def esri_object_to_df(self, in_esri_obj, esri_obj_fields, index_field=None):
        '''converts esri gdb table, feature class, feature layer, or SHP to pandas dataframe'''
        data_rows = []
        with arcpy.da.SearchCursor(in_esri_obj, esri_obj_fields) as cur:
            for row in cur:
                out_row = list(row)
                data_rows.append(out_row)
    
        out_df = pd.DataFrame(data_rows, index=index_field, columns=esri_obj_fields)
        return out_df
        
    def make_df(self, in_dict):
        re_dirn = re.compile("(.*BOUND).*") # retrieve direction
        re_metric = re.compile(".*BOUND(.*)") # retrieve name of metric
        
        df = pd.DataFrame.from_dict(in_dict, orient='index')
        
        col_metric = 'metric'
        col_direction = 'direction'
        
        df[col_direction] = df.index.map(lambda x: re.match(re_dirn, x).group(1))
        df[col_metric] = df.index.map(lambda x: re.match(re_metric, x).group(1))
        
        df_out = df.pivot(index=col_metric, columns=col_direction, values=0 )
        
        return df_out
    
    
    def get_npmrds_data(self):
        try:
            arcpy.AddMessage("Calculating congestion and reliability metrics...")
            arcpy.OverwriteOutput = True
        
            fl_projline = "fl_project"
            arcpy.MakeFeatureLayer_management(self.fc_projline, fl_projline)
        
            # make feature layer from speed data feature class
            fl_speed_data = "fl_speed_data"
            arcpy.MakeFeatureLayer_management(self.fc_speed_data, fl_speed_data)
        
            # make flat-ended buffers around TMCs that intersect project
            arcpy.SelectLayerByLocation_management(fl_speed_data, "WITHIN_A_DISTANCE", fl_projline, self.tmc_select_srchdist, "NEW_SELECTION")
            if self.str_project_type == self.projtyp_fwy:
                sql = "{} IN {}".format(self.col_roadtype, self.roadtypes_fwy)
                arcpy.SelectLayerByAttribute_management(fl_speed_data, "SUBSET_SELECTION", sql)
            else:
                sql = "{} NOT IN {}".format(self.col_roadtype, self.roadtypes_fwy)
                arcpy.SelectLayerByAttribute_management(fl_speed_data, "SUBSET_SELECTION", sql)
        
            # create temporar buffer layer, flat-tipped, around TMCs; will be used to split project lines
            temp_tmcbuff = os.path.join(arcpy.env.scratchGDB, "TEMP_tmcbuff_4projsplit")
            fl_tmc_buff = "fl_tmc_buff"
            arcpy.Buffer_analysis(fl_speed_data, temp_tmcbuff, self.tmc_buff_dist_ft, "FULL", "FLAT")
            arcpy.MakeFeatureLayer_management(temp_tmcbuff, fl_tmc_buff)
        
            # get "full" table with data for all directions
            projdata_df = self.conflate_tmc2projline(fl_projline, fl_tmc_buff)
        
            # trim down table to only include outputs for directions that are "on the segment",
            # i.e., that have most overlap with segment
            out_dict = self.simplify_outputs(projdata_df, 'proj_length_ft')[0]
            
            # pdb.set_trace()
            
            out_df = self.make_df(out_dict)
        
            #cleanup
            arcpy.Delete_management(temp_tmcbuff)
        
            tup_returns = (self.msg_ok, out_df)
        except:
            msg_tb = trace()
            tup_returns = (self.msg_fail, msg_tb)
            
        return tup_returns


# =====================RUN SCRIPT===========================
    

if __name__ == '__main__':
    time_start = dt.datetime.now()
    
    workspace = r'\\arcserver-svr\D\PPA_v2_SVR\PPA_V2.gdb'
    arcpy.env.workspace = workspace

    project_line = arcpy.GetParameterAsText(0)  # r"I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb\Polylines" # arcpy.GetParameterAsText(0) # "NPMRDS_confl_testseg_seconn"
    speed_data_set = arcpy.GetParameterAsText(1)  # r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb\npmrds_metrics_v8' # arcpy.GetParameterAsText(1) # TMC feature class with NPMRDS speed data attached
    proj_type = arcpy.GetParameterAsText(2)  # "Arterial" # arcpy.GetParameterAsText(2) #

    project_obj = projectTMCConflation(speed_data_set, project_line, proj_type)
        
    output_tup = project_obj.get_npmrds_data()
    arcpy.AddMessage(output_tup[1])

    arcpy.SetParameterAsText(3, output_tup[1])
    
    time_elapsed = str(dt.datetime.now() - time_start)
    arcpy.AddMessage("Script completed in {}".format(time_elapsed))
   
    


    

