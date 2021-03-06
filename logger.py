"""Logging class. Handles records of a single simulation run. Can save and reload. """

import numpy as np
import pdb
import listify

LOG_DEFAULT = (
    'total_cash total_excess_capital total_profitslosses total_contracts '
    'total_operational total_reincash total_reinexcess_capital total_reinprofitslosses '
    'total_reincontracts total_reinoperational total_catbondsoperational market_premium '
    'market_reinpremium cumulative_bankruptcies cumulative_market_exits cumulative_unrecovered_claims '
    'cumulative_claims insurance_firms_cash reinsurance_firms_cash market_diffvar '
    'rc_event_schedule_initial rc_event_damage_initial number_riskmodels'
).split(' ')

class Logger():
    def __init__(self, no_riskmodels=None, rc_event_schedule_initial=None, rc_event_damage_initial=None):
        """Constructor. Prepares history_logs atribute as dict for the logs. Records initial event schedule of
           simulation run.
            Arguments
                no_categories: Type int. number of peril regions.
                rc_event_schedule_initial: list of lists of int. Times of risk events by category
                rc_event_damage_initial: list of arrays (or lists) of float. Damage by peril for each category
                                         as share of total possible damage (maximum insured or excess).
            Returns class instance."""        
        
        """Record number of riskmodels"""
        self.number_riskmodels = no_riskmodels
            
        """Record initial event schedule"""
        self.rc_event_schedule_initial = rc_event_schedule_initial
        self.rc_event_damage_initial = rc_event_damage_initial

        """Prepare history log dict"""
        self.history_logs = {}
        
        """Variables pertaining to insurance sector"""
        # TODO: should we not have `cumulative_bankruptcies` and
        # `cumulative_market_exits` for both insurance firms and reinsurance firms?
        # `cumulative_claims`: Here are stored the total cumulative claims received
        # by the whole insurance sector until a certain time.
        insurance_sector = ('total_cash total_excess_capital total_profitslosses '
                            'total_contracts total_operational cumulative_bankruptcies '
                            'cumulative_market_exits cumulative_claims cumulative_unrecovered_claims').split(' ')
        for _v in insurance_sector:
            self.history_logs[_v] = []
        
        """Variables pertaining to individual insurance firms"""
        self.history_logs['individual_contracts'] = []      # TODO: Should there not be a similar record for reinsurance
        self.history_logs['insurance_firms_cash'] = []
        
        """Variables pertaining to reinsurance sector"""
        self.history_logs['total_reincash'] = []
        self.history_logs['total_reinexcess_capital'] = []
        self.history_logs['total_reinprofitslosses'] = []
        self.history_logs['total_reincontracts'] = []
        self.history_logs['total_reinoperational'] = []

        """Variables pertaining to individual reinsurance firms"""
        self.history_logs['reinsurance_firms_cash'] = []

        """Variables pertaining to cat bonds"""
        self.history_logs['total_catbondsoperational'] = []

        """Variables pertaining to premiums"""
        self.history_logs['market_premium'] = []
        self.history_logs['market_reinpremium'] = []
        self.history_logs['market_diffvar'] = []
            
    def record_data(self, data_dict):
        """Method to record data for one period
            Arguments
                data_dict: Type dict. Data with the same keys as are used in self.history_log().
            Returns None."""        
        for key in data_dict.keys():
            if key != "individual_contracts":
                self.history_logs[key].append(data_dict[key])
            else:
                for i in range(len(data_dict["individual_contracts"])):
                    self.history_logs['individual_contracts'][i].append(data_dict["individual_contracts"][i])

    def obtain_log(self, requested_logs=LOG_DEFAULT):   #This function allows to return in a list all the data generated by the model. There is no other way to transfer it back from the cloud.
        """Method to transfer entire log (self.history_log as well as risk event schedule). This is
           used to transfer the log to master core from work cores in ensemble runs in the cloud.
            No arguments.
            Returns list (listified dict)."""
        
        """Include environment variables (number of risk models and risk event schedule)"""
        self.history_logs["number_riskmodels"] = self.number_riskmodels
        self.history_logs["rc_event_damage_initial"] = self.rc_event_damage_initial
        self.history_logs["rc_event_schedule_initial"] = self.rc_event_schedule_initial
        
        """Parse logs to be returned"""
        if requested_logs == None:
            requested_logs = LOG_DEFAULT
        log = {name: self.history_logs[name] for name in requested_logs}
        
        """Convert to list and return"""
        return listify.listify(log)
    
    def restore_logger_object(self, log):
        """Method to restore logger object. A log can be restored later. It can also be restored 
           on a different machine. This is useful in the case of ensemble runs to move the log to
           the master node from the computation nodes.
            Arguments:
                log - listified dict - The log. This must be a list of dict values plus the dict 
                                        keys in the last element. It should have been created by 
                                        listify.listify()
            Returns None."""

        """Restore dict"""
        log = listify.delistify(log)
        
        """Extract environment variables (number of risk models and risk event schedule)"""
        self.rc_event_schedule_initial = log["rc_event_schedule_initial"]
        self.rc_event_damage_initial = log["rc_event_damage_initial"]
        self.number_riskmodels = log["number_riskmodels"]
        del log["rc_event_schedule_initial"], log["rc_event_damage_initial"], log["number_riskmodels"]
        
        """Restore history log"""
        self.history_logs = log

    def save_log(self, background_run):
        """Method to save log to disk of local machine. Distinguishes single and ensemble runs.
           Is called at the end of the replication (if at all).
            Arguments:
                background_run: Type bool. Is this an ensemble run (true) or not (false).
            Returns None."""
        
        """Prepare writing tasks"""
        if background_run:
            to_log = self.replication_log_prepare()
        else:
            to_log = self.single_log_prepare()
        
        """Write to disk"""
        for filename, data, operation_character in to_log:
            with open(filename, operation_character) as wfile:
                wfile.write(str(data) + "\n")
    
    def replication_log_prepare(self):
        """Method to prepare writing tasks for ensemble run saving.
            No arguments
            Returns list of tuples with three elements each.
                    Element 1: filename
                    Element 2: data structure to save
                    Element 3: operation parameter (w-write or a-append)."""
        filename_prefix = {1: "one", 2: "two", 3: "three", 4: "four"}
        fpf = filename_prefix[self.number_riskmodels]
        to_log = []
        to_log.append(("data/" + fpf + "_history_logs.dat", self.history_logs, "a"))
        return to_log
      
    def single_log_prepare(self):
        """Method to prepare writing tasks for single run saving.
            No arguments
            Returns list of tuples with three elements each.
                    Element 1: filename
                    Element 2: data structure to save
                    Element 3: operation parameter (w-write or a-append)."""
        to_log = []
        to_log.append(("data/history_logs.dat", self.history_logs, "w"))
        return to_log
    
    def add_insurance_agent(self):           
        """Method for adding an additional insurer agent to the history log. This is necessary to keep the number 
           of individual insurance firm logs constant in time.
            No arguments.
            Returns None."""
        # TODO: should this not also be done for self.history_logs['insurance_firms_cash'] and 
        #                                        self.history_logs['reinsurance_firms_cash']
        if len(self.history_logs['individual_contracts']) > 0:
            zeroes_to_append = list(np.zeros(len(self.history_logs['individual_contracts'][0]), dtype=int))
        else:
            zeroes_to_append = []
        self.history_logs['individual_contracts'].append(zeroes_to_append)

