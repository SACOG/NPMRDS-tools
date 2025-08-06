"""
Name: esri_file_to_dataframe.py
Purpose: Converts ESRI file (File GDB table, SHP, or feature class) to either pandas dataframe
    or geopandas geodataframe (if it is spatial data)

    NOTE - in the past geopandas has had a read_file method that enabled users to specify
        ESRI file gdb feature class, but it's been unreliable and subject to issues with version
        updates. This formula aims to use common ESRI and GeoPandas functions to maximize long-term reliability.


Author: Darren Conly
Last Updated: Dec 2023
Updated by: 
Copyright:   (c) SACOG
Python Version: 3.x
"""

import pandas as pd
import arcpy
from shapely import wkt, LineString

def esri_to_df(esri_obj_path, include_geom, field_list=None, index_field=None, 
               crs_val=None, dissolve=False):
    """
    Converts ESRI file (File GDB table, SHP, or feature class) to either pandas dataframe
    or geopandas geodataframe (if it is spatial data)
    esri_obj_path = path to ESRI file
    include_geom = True/False on whether you want resulting table to have spatial data (only possible if
        input file is spatial)
    field_list = list of fields you want to load. No need to specify geometry field name as will be added automatically
        if you select include_geom. Optional. By default all fields load.
    index_field = if you want to choose a pre-existing field for the dataframe index. Optional.
    crs_val = crs, in geopandas CRS string format, that you want to apply to the resulting geodataframe. Optional.
    dissolve = True/False indicating if you want the resulting GDF to be dissolved to single feature.
    """

    fields = field_list # should not be necessary, but was having issues where class properties were getting changed with this formula
    if not field_list:
        fields = [f.name for f in arcpy.ListFields(esri_obj_path)]

    if include_geom:
        import geopandas as gpd
        # by convention, geopandas uses 'geometry' instead of 'SHAPE@' for geom field
        f_esrishp = 'SHAPE@'
        f_gpdshape = 'geometry'
        fields = fields + [f_esrishp]

    data_rows = []
    with arcpy.da.SearchCursor(esri_obj_path, fields) as cur:
        for row in cur:
            rowlist = [i for i in row]
            if include_geom:
                try:
                    geom_wkt = wkt.loads(rowlist[fields.index(f_esrishp)].WKT)
                except:
                    print(f"\tWARNING: not loading link {rowlist} because it has no geometry")
                    continue
                rowlist[fields.index(f_esrishp)] = geom_wkt
            out_row = rowlist
            data_rows.append(out_row)  

    if include_geom:
        fields_gpd = [f for f in fields]
        fields_gpd[fields_gpd.index(f_esrishp)] = f_gpdshape
        
        out_df = gpd.GeoDataFrame(data_rows, columns=fields_gpd, geometry=f_gpdshape)

        # only set if the input file has no CRS--this is not same thing as .to_crs(), which merely projects to a CRS
        if crs_val: out_df.crs = crs_val

        # dissolve to single zone so that, during spatial join, points don't erroneously tag to 2 overlapping zones.
        if dissolve and out_df.shape[0] > 1: 
            out_df = out_df.dissolve() 
    else:
        out_df = pd.DataFrame(data_rows, index=index_field, columns=field_list)

    return out_df

def pts_to_linestring(row, f_startpt, f_endpt):
    # creates line feature given a start and end point
    startx = row[f_startpt].x
    starty = row[f_startpt].y
    endx = row[f_endpt].x
    endy = row[f_endpt].y
    
    return LineString([[startx, starty], [endx, endy]])