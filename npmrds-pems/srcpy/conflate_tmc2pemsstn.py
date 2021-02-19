"""
Name: conflate_tmc2pemsstn.py
Purpose: Conflate TMC code from NPMRDS data on to PeMS counter location points
        
          
Author: Darren Conly
Last Updated: <date>
Updated by: <name>
Copyright:   (c) SACOG
Python Version: 3.x
"""

import os
import datetime as dt
import pdb

import pandas as pd
import arcpy


def tmc2pems(fc_tmcs_in, csv_tmcs_in, csv_pems_stns, output_dir):
    '''Takes in a CSV of PeMS count stations and tags which NPMRDS TMC each PeMS station
    corresponds to. Returns an output CSV of PeMS stations with TMC field added.'''
    
    pems_hov = 'HV'
    pems_mainline = 'ML'
    
    col_pems_dir = 'Dir'
    col_pems_lanetype = 'Type'  # HOV, mainline, ramp, etc.
    col_pems_sid = 'ID'  # pems station id
    col_pems_hwynum = 'Fwy'
    col_pems_lat = 'Latitude'
    col_pems_lon = 'Longitude'
    
    col_tmc_tmcid = 'Tmc'
    col_tmc_hwynum = 'RoadNumber'
    col_tmc_signdir = 'direction'  # must be SIGNED direction from TMC text file, not the cardinal direction in TMC SHP file
    
    vals_direcn_tmc = ['NORTHBOUND', 'SOUTHBOUND', 'EASTBOUND', 'WESTBOUND']
    vals_direcn_pems = ['N','S','E','W']
    
    dict_dirvals_tmc_pems = dict(zip(vals_direcn_tmc, vals_direcn_pems))
    
    sref_tmcs = arcpy.Describe(fc_tmcs_in).spatialReference # set to whatever the TMC set spatial ref code is
    sref_pems_in = sref_tmcs

    # make temporary feature class and feature layer of PeMS stations from CSV
    temp_xy_lyr = "temp_pems_xyl"
    if arcpy.Exists(temp_xy_lyr):
        arcpy.Delete_management(temp_xy_lyr)
    arcpy.MakeXYEventLayer_management(csv_pems_stns, col_pems_lon, col_pems_lat, temp_xy_lyr,
                                      sref_pems_in)
    
    temp_pems_fc = "temp_pems_fc"
    fl_pems_in = "fl_pems_in"
    if arcpy.Exists(os.path.join(arcpy.env.scratchGDB, temp_pems_fc)):
        arcpy.Delete_management(os.path.join(arcpy.env.scratchGDB, temp_pems_fc))
    
    arcpy.FeatureClassToFeatureClass_conversion(temp_xy_lyr, arcpy.env.scratchGDB, 
                                           temp_pems_fc)
    
    arcpy.MakeFeatureLayer_management(os.path.join(arcpy.env.scratchGDB, temp_pems_fc), 
                                      fl_pems_in)
    
    # make separate temp fc with only selected lane types
    temp_pems_fc2 = "temp_pems_fc2"
    
    temp_pems_fc2_path = os.path.join(arcpy.env.scratchGDB, temp_pems_fc2)
    if arcpy.Exists(temp_pems_fc2_path):
        arcpy.Delete_management(temp_pems_fc2_path)
        
    sql_pems_filter = f"{col_pems_lanetype} IN ('{pems_mainline}', '{pems_hov}')"
    arcpy.SelectLayerByAttribute_management(fl_pems_in, "NEW_SELECTION", sql_pems_filter)
    
    arcpy.FeatureClassToFeatureClass_conversion(fl_pems_in, arcpy.env.scratchGDB, 
                                       temp_pems_fc2)
    
    fl_pems_in2 = "fl_pems_in2"
    if arcpy.Exists(fl_pems_in2):
        arcpy.Delete_management(fl_pems_in2)
    arcpy.MakeFeatureLayer_management(temp_pems_fc2_path, fl_pems_in2)
    
    # make feature layer of TMCs (hwy line features)
    fl_tmcs_in = "fl_tmcs_in"
    if arcpy.Exists(fl_tmcs_in):
        arcpy.Delete_management(fl_tmcs_in)
    arcpy.MakeFeatureLayer_management(fc_tmcs_in, fl_tmcs_in)
    
    # select only TMCs whose roadnumber not null and != ' ', i.e., state highways
    sql_tmc_initial = f"{col_tmc_hwynum} IS NOT NULL AND {col_tmc_hwynum} <> ' '"
    arcpy.SelectLayerByAttribute_management(fl_tmcs_in, "NEW_SELECTION", sql_tmc_initial)
    
    # select only pems stations with type in ('HV', 'ML'), or HOV and mainline types
    # df_pems_fwystn = df_pems_stns.loc[pd.isin({col_pems_lanetype: [pems_mainline, pems_hov]})]
    
    # create temp buffer around selected TMCs and a feature layer of that buffer
    fc_temp_buff = os.path.join(arcpy.env.scratchGDB, "fc_temp_tmc_buff")
    if arcpy.Exists(fc_temp_buff): arcpy.Delete_management(fc_temp_buff)
    arcpy.Buffer_analysis(fl_tmcs_in, fc_temp_buff, 50, line_end_type="FLAT")
    
    fl_tmc_buffer = "fl_tmc_buffer"
    arcpy.MakeFeatureLayer_management(fc_temp_buff, fl_tmc_buffer)
    
    # make dataframe then dict with {tmc: signed direction} from TMC spec CSV (not the TMC shapefile)
    dfd_tmc_signdir = pd.read_csv(csv_tmcs_in, usecols=[col_tmc_tmcid.lower(),
                                                       col_tmc_signdir]) \
                                                       .to_dict(orient='records')
                                                       
    dict_tmc_sdir = {row['tmc']: row['direction'] for row in dfd_tmc_signdir}
    
    # using search cursor, make list of all TMC buffer features.
    dict_tmcs_buffer = {} # {tmc:freeway number (I5, I80, etc.)}
    
    cur_fields = [col_tmc_tmcid, col_tmc_hwynum]
    with arcpy.da.SearchCursor(fc_temp_buff, cur_fields) as cur:
        for row in cur:
            tmc = row[cur_fields.index(col_tmc_tmcid)]
            hwynum = row[cur_fields.index(col_tmc_hwynum)]
            dict_tmcs_buffer[tmc] = hwynum
            
    dict_tmc_pemsstns = {}  # {tmc: list of pems station ids}
            
    #for each TMC in dict of {tmc:[hwynum, dir]}:
    print("getting lists of pems stations on each TMC")
    for tmc_id, hwynum in dict_tmcs_buffer.items():  # for tmc_id, hwynum in dict_tmcs_buffer.items()
        # select that TMC link
        sql_select_tmc = f"{col_tmc_tmcid} = '{tmc_id}'"
        arcpy.SelectLayerByAttribute_management(fl_tmcs_in, "NEW_SELECTION",
                                                sql_select_tmc)
        
        
        # select all pems stations near that selected TMC buffer whose direction match the TMC
        # direction and freeway ID match the TMC roadnumber
        arcpy.SelectLayerByLocation_management(fl_pems_in2, "WITHIN_A_DISTANCE", fl_tmcs_in, 
                                               "50 FEET", "NEW_SELECTION")
        
        tmc_sign_dir = dict_tmc_sdir[tmc_id] # "NORTHBOUND", "SOUTHBOUND", etc. from TMC spec CSV
        tmcdir_as_pemsdir = dict_dirvals_tmc_pems[tmc_sign_dir] # "NORTHBOUND" becomes "N", or as specified in dict
        
        # sql = select pems stations whose direction match the TMC direction and TMC highway number
        # alternat query - f"{col_pems_dir} = '{tmcdir_as_pemsdir}' AND {col_pems_hwynum} = '{hwynum}'"
        sql_pems_subsel = f"{col_pems_dir} = '{tmcdir_as_pemsdir}'"
        
        # run searchcursor on selected pems stations to return their IDs as a list
        # add, to the dict, the TMC as the key and the list of pems IDs as values
        list_tmc_stns = []
            
        arcpy.SelectLayerByAttribute_management(fl_pems_in2, "SUBSET_SELECTION",
                                                sql_pems_subsel)
        
        with arcpy.da.SearchCursor(fl_pems_in2, [col_pems_sid]) as cur:
            for row in cur:
                pems_sid = row[0]
                list_tmc_stns.append(pems_sid)
        
        # print(tmc_id, list_tmc_stns)
        dict_tmc_pemsstns[tmc_id] = list_tmc_stns
    
    # create empty reverse dict
    dict_tmc_pems = {}  # will be {pems_stn_id: tmc}
    # populate the reverse dict:
    # for all values (each of which is a list of pems station ids) in the initial dict:
    #     for id in the list, add it to the reverse dict with TMC as the value
    for tmc_code, pems_list in dict_tmc_pemsstns.items():
        for stn in pems_list:
            dict_tmc_pems[stn] = tmc_code
            
    return dict_tmc_pems


    # create dataframe of pems station data and export as CSV or df
    # the df could be input table for operations that aggregate pems data at TMC level
    
    # =======OPTIONAL - CREATE PEMS STATION GIS LAYER==========
    #     add TMC column to pems data
    # arcpy.AddField_management(temp_pems_fc, col_tmc_tmcid, "TEXT")

    # create insert cursor object for pems data, TMC field only
    

    # with searchcursor on pems data:
    #     get pems station id
    #     look up, in the reverse dict, the corresponding tmc
    #     insert row to set, in the pems station FC, the TMC value 


       
if __name__ == '__main__':
    tmc_fc = r'P:\NPMRDS data\NPMRDS_GIS\NPMRDS_GIS.gdb\TMCs_AllRegionNHS_2019'
    # tmc_year = int(input("what TMC year? "))
    tmc_year = 2019
    tmc_csv = r"P:\NPMRDS data\Raw Downloads\DynamicData_15Min\2019\TMC_identification.csv"
    pems_stn_csv = r"P:\NPMRDS data\Projects\PeMS Integration\Station_Data\d03_text_meta_2016_merge.csv"
    output_csv_dir = r"P:\NPMRDS data\Projects\PeMS Integration\Station_Data"
    
    # =========================RUN SCRIPT===============================
    time_sufx = str(dt.datetime.now().strftime('%Y%m%d_%H%M'))
    out_csv_name = f"pems_sid_w{tmc_year}TMC_{time_sufx}.csv"
    output_csv = os.path.join(output_csv_dir, out_csv_name)
    
    confldict = tmc2pems(tmc_fc, tmc_csv, pems_stn_csv, output_csv)
    
    df = pd.DataFrame.from_dict(confldict, orient='index')
    df = df.rename(columns={'index':'ID', 0:'TMC'})
    df.to_csv(output_csv, index=False)
    print(f"Success! Output file is {output_csv}\n")