'''
#--------------------------------
# Name:npmrds_data_conflation_cmp_batch.py
# Purpose: Get distance-weighted average speed from NPMRDS data for CMP deficient corridors,
#          make chart images. If multiple years of input data provided, then charts
#           showing year-year changes will be created.
# Author: Darren Conly
# Last Updated: Jul 2020
# Updated by: <name>
# Copyright:   (c) SACOG
# Python Version: 3.x
#--------------------------------

'''


import os
import re
import datetime as dt
import time
import pdb

import arcpy
import pandas as pd

import plotly
import plotly.express as px
from plotly.offline import plot
orca_path = r"C:\Users\dconly\AppData\Local\ESRI\conda\envs\arcgispro-py3-clone\orca_app\orca.exe"
plotly.io.orca.config.executable = orca_path 

# Esri start of added variables
g_ESRI_variable_1 = 'fl_splitprojlines'
g_ESRI_variable_2 = 'fl_splitproj_w_tmcdata'
g_ESRI_variable_3 = "{} = '{}'"
g_ESRI_variable_4 = '{} IS NOT NULL'
g_ESRI_variable_5 = os.path.join(arcpy.env.packageWorkspace,'index')
g_ESRI_variable_6 = 'fl_project'
g_ESRI_variable_7 = 'fl_speed_data'
g_ESRI_variable_8 = '{} IN {}'
g_ESRI_variable_9 = 'fl_tmc_buff'
# Esri end of added variables

arcpy.env.overwriteOutput = True

dateSuffix = str(dt.datetime.now().strftime('%Y%m%d_%H%M'))



# ====================FUNCTIONS==========================================
def esri_object_to_df(in_esri_obj, esri_obj_fields, index_field=None):
    '''converts esri gdb table, feature class, feature layer, or SHP to pandas dataframe'''
    data_rows = []
    with arcpy.da.SearchCursor(in_esri_obj, esri_obj_fields) as cur:
        for row in cur:
            out_row = list(row)
            data_rows.append(out_row)

    out_df = pd.DataFrame(data_rows, index=index_field, columns=esri_obj_fields)
    return out_df

class NPMRDS:
    def __init__(self, fc_speed_data):

        # speed data attributes
        self.fc_speed_data = fc_speed_data
        self.col_ff_speed = "ff_speed_art60thp"
        self.col_congest_speed = "havg_spd_worst4hrs"
        self.col_reliab_ampk = "lottr_ampk"
        self.col_reliab_md = "lottr_md"
        self.col_reliab_pmpk = "lottr_pmpk"
        self.col_reliab_wknd = "lottr_wknd"
        self.col_tmcdir = "direction_signd"
        self.col_roadtype = "f_system"  # indicates if road is freeway or not, so that data from freeways doesn't affect data on surface streets, and vice-versa
        
        # each item in this dict corresponds to a separate chart set 
        self.dict_perf_cats = {"speed": [self.col_ff_speed, self.col_congest_speed],
                               "lottr": [self.col_reliab_ampk, self.col_reliab_md,
                                         self.col_reliab_pmpk, self.col_reliab_wknd]
                               }
        
        # values used to indicate method for getting multi-TMC average values
        self.calc_distwt_avg = "distance_weighted_avg"
        self.calc_inv_avg = "inv_avg_spd"
        
        # specify the type of calculation for each field in order to aggregate to project line
        self.spd_data_calc_dict = {self.col_ff_speed: self.calc_inv_avg,
                              self.col_congest_speed: self.calc_inv_avg,
                              self.col_reliab_ampk: self.calc_distwt_avg,
                              self.col_reliab_md: self.calc_distwt_avg,
                              self.col_reliab_pmpk: self.calc_distwt_avg,
                              self.col_reliab_wknd: self.calc_distwt_avg}
        
        self.ptype_fwy = "Freeway"
        self.roadtypes_fwy = (1, 2)  # road type values corresponding to freeways
        self.directions_tmc = ["NORTHBOUND", "SOUTHBOUND", "EASTBOUND", "WESTBOUND"]
        
        self.tmc_select_srchdist = 300 # units in feet. will select TMCs within this distance of project line for analysis.
        self.tmc_buff_dist_ft = 90  # buffer distance, in feet, around the TMCs
        self.ft2mile = 5280
        
        # output dataframe added fields
        self.fld_projdesc = 'proj_desc'
        self.fld_proj_inum = 'proj_inum'
        self.fld_datayear = 'data_year'
        self.fld_dir_out = 'direction'
        self.fld_measure = 'measure_full'
        self.fld_measure_sep = 'measure'
        self.fld_value = 'value'
        
    def remove_forbidden_chars(self, in_str):
        '''Replaces forbidden characters with acceptable characters'''
        repldict = {"&":'And','%':'pct','/':'-', ':':'-'}
        
        out_str = ''
        for c in in_str:
            if c in repldict.keys():
                cfix = repldict[c]
                out_str = out_str + cfix
            else:
                out_str = out_str + c
        
        return out_str

    
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
        if in_df[fld_pc_tt].sum() > 0:
            proj_mph = in_df[fld_len_mi].sum() / in_df[fld_pc_tt].sum()
        else:
            proj_mph = 0
        
        return {fielddir: proj_mph}
    
    
    def conflate_tmc2projline(self, fl_proj, dirxn_list, tmc_dir_field,
                              fl_tmcs_buffd, fields_calc_dict):
    
        speed_data_fields = [k for k, v in fields_calc_dict.items()]
        out_row_dict = {}
        
        # get length of project
        fld_shp_len = "SHAPE@LENGTH"
        fld_totprojlen = "proj_length_ft"
        
        with arcpy.da.SearchCursor(fl_proj, fld_shp_len) as cur:
            for row in cur:
                out_row_dict[fld_totprojlen] = row[0]
        
        for direcn in dirxn_list:
            # https://support.esri.com/en/technical-article/000012699
            
            # temporary files
            scratch_gdb = arcpy.env.scratchGDB
            
            temp_intersctpts = os.path.join(scratch_gdb, "temp_intersectpoints")  # r"{}\temp_intersectpoints".format(scratch_gdb)
            temp_intrsctpt_singlpt = os.path.join(scratch_gdb, "temp_intrsctpt_singlpt") # converted from multipoint to single point (1 pt per feature)
            temp_splitprojlines = os.path.join(scratch_gdb, "temp_splitprojlines") # fc of project line split up to match TMC buffer extents
            temp_splitproj_w_tmcdata = os.path.join(scratch_gdb, "temp_splitproj_w_tmcdata") # fc of split project lines with TMC data on them
            
            fl_splitprojlines = g_ESRI_variable_1
            fl_splitproj_w_tmcdata = g_ESRI_variable_2
            
            # get TMCs whose buffers intersect the project line
            arcpy.SelectLayerByLocation_management(fl_tmcs_buffd, "INTERSECT", fl_proj)
            
            # select TMCs that intersect the project and are in indicated direction
            sql_sel_tmcxdir = g_ESRI_variable_3.format(tmc_dir_field, direcn)
            # pdb.set_trace()
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
            
            check_field = speed_data_fields[0]  # choose first speed value field for checking--if it's null, then don't include those rows in aggregation
            #pdb.set_trace()
            sql_notnull = g_ESRI_variable_4.format(check_field)
            arcpy.SelectLayerByAttribute_management(fl_splitproj_w_tmcdata, "NEW_SELECTION", sql_notnull)
            
            # convert the selected records into a numpy array then a pandas dataframe
            flds_df = [fld_shp_len] + speed_data_fields 
            df_spddata = esri_object_to_df(fl_splitproj_w_tmcdata, flds_df)
    
            # remove project pieces with no speed data so their distance isn't included in weighting
            df_spddata = df_spddata.loc[pd.notnull(df_spddata[speed_data_fields[0]])].astype(float)
            
            # remove rows where there wasn't enough NPMRDS data to get a valid speed or reliability reading
            df_spddata = df_spddata.loc[df_spddata[flds_df].min(axis=1) > 0]
            
            dir_len = df_spddata[fld_shp_len].sum() #sum of lengths of project segments that intersect TMCs in the specified direction
            out_row_dict["{}_calc_len".format(direcn)] = dir_len #"calc" length because it may not be same as project length
            
            
            # go through and do conflation calculation for each TMC-based data field based on correct method of aggregation
            for field, calcmthd in fields_calc_dict.items():
                if calcmthd == self.calc_inv_avg: # See PPA documentation on how to calculated "inverted speed average" method
                    sd_dict = self.get_wtd_speed(df_spddata, field, direcn, fld_shp_len)
                    out_row_dict.update(sd_dict)
                elif calcmthd == self.calc_distwt_avg:
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
                else:
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
            outcols_max = [c for c in in_df.columns if re.match(maxdir, c)]
            
            # if the "second-longest" direction is < 3/4 the length, then assume it's a one-way facility.
            max_len_val = in_df[max_len_col].sum()
            secnd_max_len_val = in_df[secndmax_col].sum()
            
            if secnd_max_len_val / max_len_val > 0.75:
                secdir = secndmax_col[:secndmax_col.find(dirlen_suffix)]
                outcols_sec = [c for c in in_df.columns if re.match(secdir, c)]
                outcols = outcols_max + outcols_sec
            else:
                outcols = outcols_max
            
            if len(outcols) > 14:
                pdb.set_trace()
    
            return in_df[outcols]
        
    def make_df(self, in_dict):
        re_dirn = re.compile("(.*BOUND).*") # retrieve direction
        re_metric = re.compile(".*BOUND(.*)") # retrieve name of metric
        
        df = pd.DataFrame.from_dict(in_dict, orient=g_ESRI_variable_5)
        
        col_metric = 'metric'
        col_direction = 'direction'
        
        df[col_direction] = df.index.map(lambda x: re.match(re_dirn, x).group(1))
        df[col_metric] = df.index.map(lambda x: re.match(re_metric, x).group(1))
        
        df_out = df.pivot(index=col_metric, columns=col_direction, values=0 )
        
        return df_out
    
    
    def get_npmrds_data_project(self, fc_projline, str_project_type):
        arcpy.AddMessage("Calculating congestion and reliability metrics...")
        arcpy.OverwriteOutput = True
    
        fl_projline = g_ESRI_variable_6
        arcpy.MakeFeatureLayer_management(fc_projline, fl_projline)
    
        # make feature layer from speed data feature class
        fl_speed_data = g_ESRI_variable_7
        arcpy.MakeFeatureLayer_management(self.fc_speed_data, fl_speed_data)
    
        # make flat-ended buffers around TMCs that intersect project
        arcpy.SelectLayerByLocation_management(fl_speed_data, "WITHIN_A_DISTANCE", fl_projline, self.tmc_select_srchdist, "NEW_SELECTION")
        if str_project_type == 'Freeway':
            sql = g_ESRI_variable_8.format(self.col_roadtype, self.roadtypes_fwy)
            arcpy.SelectLayerByAttribute_management(fl_speed_data, "SUBSET_SELECTION", sql)
        else:
            sql = "{} NOT IN {}".format(self.col_roadtype, self.roadtypes_fwy)
            arcpy.SelectLayerByAttribute_management(fl_speed_data, "SUBSET_SELECTION", sql)
    
        # create temporar buffer layer, flat-tipped, around TMCs; will be used to split project lines
        temp_tmcbuff = os.path.join(arcpy.env.scratchGDB, "TEMP_linkbuff_4projsplit")
        fl_tmc_buff = g_ESRI_variable_9
        arcpy.Buffer_analysis(fl_speed_data, temp_tmcbuff, self.tmc_buff_dist_ft, "FULL", "FLAT")
        arcpy.MakeFeatureLayer_management(temp_tmcbuff, fl_tmc_buff)
    
        # get "full" table with data for all directions
        projdata_df = self.conflate_tmc2projline(fl_projline, self.directions_tmc, self.col_tmcdir,
                                            fl_tmc_buff, self.spd_data_calc_dict)
    
        # trim down table to only include outputs for directions that are "on the segment",
        # i.e., that have most overlap with segment
        out_df = self.simplify_outputs(projdata_df, 'proj_length_ft')
        out_df = out_df.T
    
        #cleanup
        arcpy.Delete_management(temp_tmcbuff)
    
        return out_df
    
    
    def overwrite_df_to_xlsx(self, in_df, worksheet, start_row=0, start_col=0):  # why does there need to be an argument?
        '''Writes pandas dataframe <in_df_ to <tab_name> sheet of <xlsx_template> excel workbook.'''
        in_df = in_df.reset_index()
        df_records = in_df.to_records(index=False)
        
        # get header row for output
        out_header_list = [list(in_df.columns)]  # get header row for output
        
        out_data_list = [list(i) for i in df_records]  # get output data rows
    
        comb_out_list = out_header_list + out_data_list
    
        ws = worksheet
        for i, row in enumerate(comb_out_list):
            for j, val in enumerate(row):
                cell = ws.cell(row=(start_row + (i + 1)), column=(start_col + (j + 1)))
                if (cell):
                    cell.value = val
    
    
    def get_npmrds_data_batch(self, fc_projlines, fld_projid, fld_projname,
                              fld_projtype, speed_data_year):
        
        comb_df = pd.DataFrame() # set up empty data frame that will be appended to.
    
        fields = [fld_projid, fld_projname, fld_projtype]
        
        fl_projlines = "fl_projlines"
        
        arcpy.MakeFeatureLayer_management(fc_projlines, fl_projlines)
        with arcpy.da.SearchCursor(fl_projlines, fields)  as cur:
            # i = 0                       
            for i, row in enumerate(cur):
                i += 1 # create UID for project, add +1 so not starting at zero
                projid = row[fields.index(fld_projid)]
                projname = row[fields.index(fld_projname)]
                projname = self.remove_forbidden_chars(projname)
                
                projtype = row[fields.index(fld_projtype)]
                
                print("\trunning analysis for {}".format(projname))
                
                # select just project from fc of all projects
                sql_proj = f"{fld_projid} = {projid}"
                arcpy.SelectLayerByAttribute_management(fl_projlines, "NEW_SELECTION",
                                                        sql_proj)
                
                temp_proj_fc = "temp_proj_fc"
                arcpy.FeatureClassToFeatureClass_conversion(fl_projlines, arcpy.env.scratchGDB, 
                                                            temp_proj_fc)
                
                fp_temp_proj_fc = os.path.join(arcpy.env.scratchGDB, temp_proj_fc)
                
                proj_df = self.get_npmrds_data_project(fp_temp_proj_fc, projtype)
                proj_df = proj_df.reset_index() \
                        .rename(columns={0: self.fld_value, 'index': self.fld_measure})
                proj_df[self.fld_projdesc] = projname
                proj_df[self.fld_proj_inum] = i
                proj_df[self.fld_datayear] = speed_data_year
                
                re_dir_extract = '(.*BOUND).*'
                re_measure_extract = '.*BOUND(.*)'
                
                proj_df[self.fld_dir_out] = proj_df[self.fld_measure].str.extract(re_dir_extract)
                proj_df[self.fld_measure_sep] = proj_df[self.fld_measure].str.extract(re_measure_extract)
                
                comb_df = comb_df.append(proj_df)
        
        return comb_df
    
    #chart-making functions maybe could be packed into a subclass of NPMRDS superclass?
    # also would be best practice to combine these into a single "charting" function w more args
    def make_speed_chart(self, master_df, proj_id, imgdir):
        
        # prep df for use in chart: filter to specific project, include both years,
        # with columns for year, proj desc, directions, values, filtered for the 
        # desired metrics, in this case, just the columb for congested speed.
        cols_dfc = [self.fld_projdesc, self.fld_measure_sep, self.fld_datayear,
                    self.fld_value, self.fld_dir_out]
        dfc = master_df.loc[(master_df[self.fld_measure_sep] == self.col_congest_speed) \
                              & (master_df[self.fld_proj_inum] == proj_id)][cols_dfc]
            
        fld_year_str = f'{self.fld_datayear}_str'
        dfc[fld_year_str] = dfc[self.fld_datayear].astype(str)
        
        dict_rename = {self.fld_value: 'Congested Speed MPH'}
        dfc = dfc.rename(columns=dict_rename)
        
        chart_title = dfc[self.fld_projdesc].iloc[0]
        # bar chart with groups by direction, within each group show bar of avg speed
        # for first year and 2nd year speeds.
        fig = px.bar(dfc, x=self.fld_dir_out, y=dict_rename[self.fld_value], color=fld_year_str, 
                     barmode='group', title=chart_title, text=dict_rename[self.fld_value],
                     height=400)
        fig.update_traces(texttemplate='%{text:.1f}')
        
        # add in suffixes for year1, year2, project ID, 
        imgname = "congestedspeed{}_{}.jpeg".format(proj_id, int(time.clock()))
        fig.write_image(os.path.join(imgdir, imgname))
        
    def make_lottr_charts(self, master_df, proj_id, imgdir):
        cols_dfc = [self.fld_projdesc, self.fld_measure_sep, self.fld_datayear,
            self.fld_value, self.fld_dir_out]
        dfc = master_df.loc[(master_df[self.fld_measure_sep].str.contains('.*lottr.*')) \
                              & (master_df[self.fld_proj_inum] == proj_id)][cols_dfc]
        
        dict_rename = {self.fld_value: 'LOTTR'}
        dfc = dfc.rename(columns=dict_rename)
        
        fld_year_str = f'{self.fld_datayear}_str'
        dfc[fld_year_str] = dfc[self.fld_datayear].astype(str)
        
        chart_title = dfc[self.fld_projdesc].iloc[0]
        
        fig = px.bar(dfc, x=self.fld_measure_sep, y=dict_rename[self.fld_value], 
                     color=fld_year_str, barmode="group", facet_col=self.fld_dir_out,
                     title=chart_title, text=dict_rename[self.fld_value],
                     height=400)
        fig.update_traces(texttemplate='%{text:.2f}')
    
        imgname = "LOTTR{}_{}.jpeg".format(proj_id, int(time.clock()))
        fig.write_image(os.path.join(imgdir, imgname))
        
    def make_charts_gen(self, master_df, proj_id, imgdir):
        dateSuffix2 = str(dt.datetime.now().strftime('%Y%m%d_%H%M'))
        
        # fields needed to make chart: proj description, field with name of metric,
        # field indicating data year, field with value to be charted, field indicating
        # signed roadway direction
        cols_dfc = [self.fld_projdesc, self.fld_measure_sep, self.fld_datayear,
            self.fld_value, self.fld_dir_out]
        

        for categ, cat_measures in self.dict_perf_cats.items():
            # make dataframe for charts that has the correct project ID and value fields
            # required for the chart
            dfc = master_df.loc[(master_df[self.fld_measure_sep].isin(cat_measures)) \
                                  & (master_df[self.fld_proj_inum] == proj_id)][cols_dfc]
                
            # dict_rename = {self.fld_value: 'LOTTR'}
            # dfc = dfc.rename(columns=dict_rename)
            
            # convert year from int to str so it's treated as a category rather than metric variable
            fld_year_str = f'{self.fld_datayear}_str'
            dfc[fld_year_str] = dfc[self.fld_datayear].astype(str)
            
            chart_title = dfc[self.fld_projdesc].iloc[0]
            
            
            # make separate charts for each direction; 
            # each chart x axis values are the names of the metric
            # for each x value there are two bars, each bar representing a different year
            fig = px.bar(dfc, x=self.fld_measure_sep, y=self.fld_value, 
                         color=fld_year_str, barmode="group", facet_col=self.fld_dir_out,
                         title=chart_title, text=self.fld_value,
                         height=400)
            fig.update_traces(texttemplate='%{text:.2f}')
        
            imgname = "{}Charts{}_{}.jpeg".format(categ, proj_id, dateSuffix2)
            fig.write_image(os.path.join(imgdir, imgname))        

# =====================RUN SCRIPT===========================
    

if __name__ == '__main__':
    start_time = time.time()
    
    #===================INPUT PARAMETERS========================
    workspace = r'I:\Projects\Darren\CMPs\CMP2020\CMP_2020GIS\CMP_2020.gdb'
    root_img_dir = r'I:\Projects\Darren\CMPs\CMP2020\NPMRDS Data\IMG'
    arcpy.env.workspace = workspace

    corridors_fc = r'Deficient_Corridors_testsample'  # 'Deficient_Corridors_testsample'  # r'I:\Projects\Darren\CMPs\CMP2017\GDB\CMP Roads.gdb\Deficient_Corridors'
    
    speed_data_fc1 = 'TMCs_CMP_2017_w2016speeds'
    data_year1 = 2016
    
    speed_data_fc2 = 'TMCs_CMP_2019'
    data_year2 = 2019
    # =====================CREATE MASTER DATAFRAME OF ALL PROJECTS' DATA==============
    print(f"Running data for year {data_year1}")
    npmrds_obj_yr1 = NPMRDS(speed_data_fc1)
    combd_df_yr1 = npmrds_obj_yr1.get_npmrds_data_batch(corridors_fc, "Number", "Name", "roadtype",
                                     data_year1)
    
    print(f"Running data for year {data_year2}")
    npmrds_obj_yr2 = NPMRDS(speed_data_fc2)
    combd_df_yr2 = npmrds_obj_yr2.get_npmrds_data_batch(corridors_fc, "Number", "Name", "roadtype",
                                     data_year2)
    
    output_df = combd_df_yr1.append(combd_df_yr2)
    
    #====================CREATE OUTPUT CHARTS===================================
    # make folder for the output images
    
    out_img_dir = os.path.join(root_img_dir, "BatchProjectAnalyses{}".format(dateSuffix))
    print("\nCreating chart images in {}".format(out_img_dir))
    
    if os.path.exists(out_img_dir):
        os.rmdir(out_img_dir)
    os.mkdir(out_img_dir)
    
    output_obj = NPMRDS(speed_data_fc2)
    proj_ids = list(output_df['proj_inum'].unique())
    
    for pid in proj_ids:
        output_obj.make_charts_gen(output_df, pid, out_img_dir)
    
    elapsed_time = round((time.time() - start_time)/60, 1)
    print("Success! Time elapsed: {} minutes".format(elapsed_time))    
    


'''
df_speed1 = output_df.loc[(output_df.measure == 'havg_spd_worst4hrs') \
                          & (output_df.proj_inum == 1)][['measure', 'data_year',
                                                          'value', 'direction']]

fld_year_str = 'data_year_str'
df_speed1[fld_year_str] = df_speed1['data_year'].astype(str)

fig = px.bar(df_speed1, x='direction', y='value', color='data_year_str', barmode='group',
             text='value', ,title='test_chart')

fig.update_traces(texttemplate='%{text:.2f}')

plot(fig)

'''


    


