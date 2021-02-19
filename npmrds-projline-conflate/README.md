# NPMRDS project conflation
NPMRDS scripts related to conflating Inrix-based NPMRDS speed data to a user-drawn project line 


SOFTWARE REQUIREMENTS:
-ESRI ArcGIS Pro (to open toolbox)
-Active ESRI license with arcpy python module
-Python 3.x
-Pandas python data analysis package


BASIC USER INSTRUCTIONS:
1 - Create a TMC shapefile or ESRI feature class containing the speed data you want to conflate
    to your project line.

2 - in the conflation python file, refer to instructions in the script file to update the script as needed
3 - Configure the toolbox in ArcGIS Pro to refer to the location of the python script
    **You may also run the tool by hard-coding in the values for all variables in the script that by default
    have the value "arcpy.GetParameterAsText()"
