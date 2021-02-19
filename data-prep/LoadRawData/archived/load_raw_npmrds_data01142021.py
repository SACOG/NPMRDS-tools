"""
Name: load_raw_npmrds_data.py
Purpose: 
    Load raw CSV data for NPMRDS into SQL Server, ensuring consistent naming
        conventions and data types
    <FUTURE FEATURES>
        -tag whether the TMC is in SACOG region or the Tahoe basin
        
        
          
Author: Darren Conly
Last Updated: Jan 2021
Updated by: <name>
Copyright:   (c) SACOG
Python Version: 3.x
"""

import os

from bcp_loader_test3 import BCP


class RawTTCSV():
    def __init__(self, data_dir, data_year, vehtype, tmc_extent='alltmc', tbl_name_addl=''):
        '''
        Parameters
        ----------
        data_dir : TYPE
            DESCRIPTION. Folder where data are stored
        data_year : TYPE
            DESCRIPTION. Year of speed data
        vehtype : TYPE
            DESCRIPTION.
        tmc_extent : TYPE  
            DESCRIPTION. whether TMCs cover whole region or just NHS
        tbl_name_addl : TYPE, optional
            DESCRIPTION. Additional text you want in table name (e.g. specific months of data, etc.)
                        The default is ''.
                        
        Returns: object with all information needed to load CSV into SQL Server

        '''
        # file path for data to load
        self.data_dir = data_dir
        self.csv_name = f"{os.path.basename(self.data_dir)}.csv"
        self.csv_path = os.path.join(self.data_dir, self.csv_name)
        
        # build a table name for SQL server
        self.vehtype_dict = {'all': 'paxtruck_comb', 'passenger': 'paxveh',
                             'truck': 'trucks'}
        self.vehtype_tblname = self.vehtype_dict[vehtype]
        self.table_year = data_year
        self.tmc_extent = tmc_extent
        
        if len(tbl_name_addl) > 0:
            self.other_tblname_info = tbl_name_addl[:10] if len(tbl_name_addl) > 10 else tbl_name_addl
            self.other_tblname_info= f"_{self.other_tblname_info}"
        else:
            self.other_tblname_info = ''
        
        self.sql_server_table_name = f"npmrds_{self.table_year}_{self.tmc_extent}_" \
            f"{self.vehtype_tblname}{self.other_tblname_info}"
            

class DataSet():
    # define where the data are, file names, etc.
    def __init__(self, data_year, truck_data_dir=None, pax_data_dir=None, comb_data_dir=None):
        '''
        Parameters
        ----------
        data_year :
            Data year
        truck_tt_data : TYPE, optional
            DESCRIPTION. directory of the truck travel time data
        pax_tt_data : TYPE, optional
            DESCRIPTION. directory of the passenger vehicle travel time data
        comb_tt_data : TYPE, optional
            DESCRIPTION. directory of the combiend truck + pax vehicle travel time data
        tmc_spec : TYPE, optional
            DESCRIPTION. CSV of unique TMCs and all TMC-level attributes

        Returns
        -------
        None.

        '''
        #db connection info
        self.server = 'SQL-SVR'
        self.database = 'NPMRDS'
        self.BCP_conn = BCP(self.server, self.database)
        
        # queries to run
        self.script_dir = os.path.dirname(os.path.realpath(__file__))
        self.qry_dir = os.path.join(self.script_dir, "qry")
        
        self.sql_create_tmcspec_tbls = "create_tmc_spec_tables.sql"
        self.sql_tmcspec_load2final = "tmc_spec_load2final.sql"
        self.sql_create_tt_tbls = 'create_tt_table_2ph.sql'
        self.sql_tt_load2final = 'tt_tbl_load2final.sql'
        
        
        self.tmc_extent = 'alltmc'
        
        
        self.data_dir_list = []
        if truck_data_dir:
            self.data_truck = RawTTCSV(truck_data_dir, data_year, 'truck', tmc_extent=self.tmc_extent, tbl_name_addl='')
            self.data_dir_list.append(self.data_truck)
        if pax_data_dir:
            self.data_pax = RawTTCSV(pax_data_dir, data_year, 'passenger', tmc_extent=self.tmc_extent, tbl_name_addl='')
            self.data_dir_list.append(self.data_pax)
        if comb_data_dir:
            self.data_comb = RawTTCSV(comb_data_dir, data_year, 'all', tmc_extent=self.tmc_extent, tbl_name_addl='')
            self.data_dir_list.append(self.data_comb)
        
        # get TMC specification CSV
        first_data_dir = self.data_dir_list[0].data_dir
        self.tmc_spec_csv = os.path.join(first_data_dir, "TMC_Identification.csv")
        self.tmc_spec_tblname = f"npmrds_{data_year}_{self.tmc_extent}_txt"
        self.speccol_startdate = 'active_start_date'
        self.speccol_enddate = 'active_end_date'
        
        # columns
        self.col_timestamp = 'measurement_tstamp'
    
    def sql_str_from_file(self, in_sql_file, *formatter_args):
        '''PARAMETERS:
            in_sql = sql file that string will be generated from.
            *formatter_args = values to populate formatter placeholders
            in sql string, e.g. table names, column names, etc.'''
        with open(in_sql_file, 'r') as f_in:
            f_str = f_in.read()
        
        if formatter_args:
            f_str = f_str.format(*formatter_args)
        
        return f_str
    
    def load_tmc_spectbl(self, dt_columns=None):
        print("loading tmc specification CSV...")
        
        spectbl_qry_file = os.path.join(self.qry_dir, self.sql_create_tmcspec_tbls)
        spectbl_load2final_qry_file = os.path.join(self.qry_dir, self.sql_tmcspec_load2final)
        
        sqlstr_maketbls = self.sql_str_from_file(spectbl_qry_file) # self.sql_str_from_file(spectbl_qry_file, spectbl_staging, self.tmc_spec_tblname)
        sqlstr_load2final = self.sql_str_from_file(spectbl_load2final_qry_file) # self.sql_str_from_file(spectbl_load2final, spectbl_staging, self.tmc_spec_tblname)

        self.BCP_conn.create_sql_table_from_file(file_in=self.tmc_spec_csv, 
                                                 str_create_table_sql=sqlstr_maketbls,
                                                 tbl_name=self.tmc_spec_tblname,
                                                 dt_cols=dt_columns,
                                                 str_load2final_sql=sqlstr_load2final,
                                                 re_dt_format='(\d+-\d+-\d+\s\d+:\d+:\d+).*')
        
    
    #load specified tables to SQL server
    def load_to_sql(self, load_tmc_spectable=True):
        qry_load2svr = os.path.join(self.qry_dir, 'create_tt_table_2ph.sql')
        qry_load2final = os.path.join(self.qry_dir, 'tt_tbl_load2final.sql')

        for data in self.data_dir_list:
            print(f"loading {data.csv_name} to {data.sql_server_table_name}...")
            str_sql_load2svr = self.sql_str_from_file(qry_load2svr)
            str_sql_load2final = self.sql_str_from_file(qry_load2final)
          
            self.BCP_conn.create_sql_table_from_file(file_in=data.csv_path, 
                                                     str_create_table_sql=str_sql_load2svr,
                                                     tbl_name=data.sql_server_table_name,
                                                     dt_cols=self.col_timestamp,
                                                     str_load2final_sql=str_sql_load2final)
            
        if load_tmc_spectable:
            self.load_tmc_spectbl(dt_columns=[self.speccol_startdate, self.speccol_enddate])
                


if __name__ == '__main__':
    parent_dir = r"P:\NPMRDS data\Raw Downloads\DynamicData_15Min\2020"
    datayear = 2020

    truckdir = os.path.join(parent_dir, 'NPMRDS2020_Trucks')
    paxdir = os.path.join(parent_dir, 'NPMRDS2020_Pax')
    combdir = os.path.join(parent_dir, 'NPMRDS2020_TruckPaxComb')
    
    
    
    # test_obj = DataSet(data_year=datayear, truck_data_dir=truckdir,
    #                 pax_data_dir=paxdir, comb_data_dir=combdir)
    
    loader = DataSet(data_year=datayear, truck_data_dir=truckdir,
                       pax_data_dir=paxdir, comb_data_dir=combdir)
    
    # loader.load_to_sql(load_tmc_spectable=False)
    loader.load_tmc_spectbl(dt_columns=['active_start_date', 'active_end_date'])