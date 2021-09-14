# Copyright 2021 thingsintouch.com

from odoo import http, fields
import time
from datetime import datetime
import json
from . import routine
import logging

_logger = logging.getLogger(__name__)

display_messages = [
    "card_registered",
    "too_little_time_between_clockings"
  ]

factory_settings = [
  "firmwareAtShipment",
  "productName",
  "productionDate",
  "productionLocation",
  "productionNumber",
  "qualityInspector",
  "SSIDreset",
  "hashed_machine_id",
  "setup_password"]

defined_on_ack_from_odoo = [
  "routefromDeviceToOdoo",
  "routefromOdooToDevice",
  "version_things_module_in_Odoo",
  "setup_password"]

defined_on_ack_from_device = [
  "firmwareVersion",
  "lastFirmwareUpdateTime",
  "lastTimeTerminalStarted",
  "updateFailedCount",
  "ownIpAddress",
  "setup_password"]

keys_routine_calls = [
  "ssh",
  "showEmployeeName",
  "sshPassword",
  "language",
  "tz",
  "time_format",
  "timeoutToCheckAttendance",
  "periodEvaluateReachability",
  "periodDisplayClock",
  "timeToDisplayResultAfterClocking",
  "location",
  "shouldGetFirmwareUpdate",
  "setRebootAt",
  'shutdownTerminal',
  "gitBranch",
  "gitCommit",
  "gitRemote",
  "updateOTAcommand" ,
  "doFactoryReset",
  "updateAvailable",
  "lastConnectionOdooTerminal",
  "minimumTimeBetweenClockings", # in seconds
  "period_odoo_routine_check", # in seconds
  "setup_password"
  ]

defined_on_device_setup = [
  "https",
  "odoo_host",
  "odoo_port",
  "odooConnectedAtLeastOnce",
  "odooUrlTemplate",
  "hasCompletedSetup"]

all_keys = factory_settings + defined_on_device_setup + \
    defined_on_ack_from_device + keys_routine_calls + \
    defined_on_ack_from_odoo

keys_defined_in_device = factory_settings + \
    defined_on_device_setup + defined_on_ack_from_device

keys_ack = keys_defined_in_device + defined_on_ack_from_odoo

class ThingsRasGate(http.Controller):

    @http.route('/things/gates/ras/version',
            type = 'json',
            auth = 'public',
            methods=['POST'],
            csrf = False)
    def ModuleVersion(self, **kwargs):
        answer = {"error": None}
        try:
            data = http.request.jsonrequest
            _logger.info('#### MODULE VERSION : data: {}'.format(data)) ##############

            question = data.get('question', None)
            if "Please" in question:
                answer["version"]= "11.0.5.0.210910" # version of this things module as in __manifest__.py
            else:
                answer["error"]="Wrong question"
                answer["version"]= None
                _logger.error('someone is asking the wrong question (Get Module Version of ThingsRasGate Class)')
        except Exception as e:
            _logger.info('Get Module Version of ThingsRasGate Class - Exception {}'.format(e))
            answer["error"] = e
        _logger.info('answer to Get Module Version of ThingsRasGate Class: {}'.format(answer)) ################
        return answer

    @http.route('/things/gates/ras/ack',
            type = 'json',
            auth = 'public',
            methods=['POST'],
            csrf = False)
    def AcknowdledgeRasGate(self, **kwargs):
        # create a new record things.ras2
        # or return if existing
        def get_data_coming_from_terminal():
            data_to_transfer ={}
            for o in keys_defined_in_device:
                # _logger.info('get data to transfer - key {}'.format(o))
                data_to_transfer[o] = data.get(o)
            data_to_transfer['lastConnectionOdooTerminal'] = str(fields.Datetime.now())
            # _logger.info('data to transfer {}'.format(data_to_transfer))        
            return data_to_transfer

        def getRASxxx(RAS_id):
            RAS_id_str ="xxx"
            try:
                if RAS_id:
                    RAS_id_str = str(RAS_id)
                    if len(RAS_id_str)==1:
                        RAS_id_str = "00" + RAS_id_str
                    elif len(RAS_id_str)==2:
                        RAS_id_str = "0" + RAS_id_str
                    elif len(RAS_id_str)>3:
                        RAS_id_str = RAS_id_str[-3:]
                # _logger.info("RAS_id_str: {}".format(RAS_id_str))
            except Exception as e:
                _logger.info("Exception in getRASxxx: {}".format(e))
                
            return RAS_id_str

        answer = {"error": None}
        _logger.info('############### - ACK - ##############')
        try:
            data = http.request.jsonrequest
            _logger.info('ACK -- data: {}'.format(data))
            hashed_machine_id = data.get('hashed_machine_id', None)
            # _logger.info('hashed_machine_id: {}'.format(hashed_machine_id))

            Ras2Model = http.request.env['things.ras2']

            ras2_machine_in_database = Ras2Model.sudo().search(
                 [('hashed_machine_id', '=', hashed_machine_id)])

            data_to_transfer = get_data_coming_from_terminal()

            if ras2_machine_in_database:
                ras2_to_be_acknowledged = ras2_machine_in_database
                ras2_to_be_acknowledged.sudo().write(data_to_transfer)
            else:
                ras2_to_be_acknowledged = Ras2Model.sudo().create(data_to_transfer)

            ras2_Dict = ras2_to_be_acknowledged.sudo().read()[0]

            for p in all_keys:
                # _logger.info('----> key {}'.format(p))
                answer[p] = ras2_Dict.get(p)

            answer["terminalIDinOdoo"] = str(ras2_to_be_acknowledged.id)
            RASxxx = "RAS-"+getRASxxx(ras2_to_be_acknowledged.id)
            answer['RASxxx'] = RASxxx
            inc_log =  data.get('incrementalLog', '')
            ras2_to_be_acknowledged.sudo().write({
                'RASxxx': RASxxx,
                'incrementalLog': inc_log,
                "shouldGetFirmwareUpdate": False,
                "shutdownTerminal": False
                })

        except Exception as e:
            _logger.info('the new gate request could not be dispatched - Exception {}'.format(e))
            answer["error"] = e
        # _logger.info('answer to request to acknowledge RAS: {} '.format(answer))
        return answer

    def resetSettings(self,routeFrom, answer):
        try:
            Ras2Model = http.request.env['things.ras2']
            ras2_in_database = Ras2Model.sudo().search(
                [('routefromDeviceToOdoo', '=', routeFrom)])
            
            if ras2_in_database:
                ras2_in_database.sudo().write({
                    'setRebootAt' : None,
                    'shutdownTerminal' : False,
                    'shouldGetFirmwareUpdate': False                
                })
            else:
                answer["error"] = "This should never occur. Method resetSettings"
                # _logger.info('resetSettings RAS - Error: {} '.format(answer["error"]))
        except Exception as e:
            _logger.info('resetSettings RAS - Exception {}'.format(e))
            answer["error"] = e

        # _logger.info('resetSettings RAS: {}'.format(answer))
        return answer

    def registerSingleton(self, card, timestamp_str, source):

        def getEmployeeID(card):
            EmployeeModel = http.request.env['hr.employee']
            employee_id = EmployeeModel.sudo().search([('rfid_card_code', '=', card)], limit=1)
            if employee_id:
                #_logger.debug("employee with card {} found:".format(card))
                return employee_id
            else:
                #_logger.warning("No employee found with card {}".format(card))
                return None


        employee_id = getEmployeeID(card)

        if employee_id is None:
            return False
        else:
            attendanceModel = http.request.env['hr.attendance']

            result = attendanceModel.add_clocking(  employee_id,
                                                    timestamp_str,
                                                    #checkin_or_checkout="not_defined",
                                                    source=source)

            if result == "all OK":
                return True
            elif "Timestamp is already registered" in result:
                #_logger.warning("Could not add clocking, Timestamp is already registered")
                return True
            elif "days in the past" in result:
                #_logger.warning("Would not add clocking, Timestamp is too old")
                return False

        return False

    def registerClockings(self,routeFrom, data, answer):

        def getSource(routeFrom):
            Ras2Model = http.request.env['things.ras2']
            ras2_in_database = Ras2Model.sudo().search(
                [('routefromDeviceToOdoo', '=', routeFrom)])
            if ras2_in_database:
                return str(ras2_in_database.id)
            else:
                return "xxx"

        answer['processed_clockings']=[]
        try:
            source = getSource(routeFrom)
            #_logger.info('################# ---- register clockings ---- ##############')
            #_logger.info('################# ---- register clockings ---- ##############')
            # timestamp =  fields.Datetime.now() #.strftime("%Y-%m-%d %H:%M:%S")
            # tzNAME = "dede" #fields.Datetime.now().tzname()
            # _logger.info('timestamp_now {} . tz name {}'.format(timestamp, tzNAME))
            #_logger.info('registerClockings - data {}'.format(data))
            for c in data.get('clockings',[]):
                [card, timestamp_in_seconds] = c.split('-')
                timestamp_datetime = datetime.fromtimestamp(int(timestamp_in_seconds))
                timestamp_str = timestamp_datetime.isoformat(' ')
                #timestamp_localtime = time.localtime(int(timestamp_in_seconds))
                #_logger.info('registerClockings - card {} - timestamp_str {}'.format(card,timestamp_str))
                if self.registerSingleton(card, timestamp_str, source):
                    #_logger.info('SUCCESS ----')
                    answer['processed_clockings'].append(c)
                else:
                    #_logger.info('FAILED xxxxx')
                    pass             
            #_logger.info('################# ---- register clockings ---- ##############')
            #_logger.info('################# ---- register clockings ---- ##############')
        except Exception as e:
            _logger.info('registerClockings - Exception {}'.format(e))
            answer["error"] = e
        #_logger.info('registerClockings : {}'.format(answer))
        return answer

    def get_productCategory(self,data):
        productName = data.get('productName', None)
        #_logger.debug('productName {}'.format(productName))
        return productName[0:3]        

    @http.route('/things/gates/ras/incoming/<routeFrom>',
            type = 'json',
            auth = 'public',
            methods=['POST'],
            csrf = False)
    def messageFromGate(self, routeFrom, **kwargs):
        answer = {"error": None}
        try:
            data                = http.request.jsonrequest

            productCategory     = self.get_productCategory(data)
            question            = data.get('question', None)

            if  productCategory == "RAS"        and  \
                question        == "RegisterClockings":
                answer = self.registerClockings(routeFrom, data, answer)            

            if  productCategory == "RAS"        and  \
                question        == "Reset":
                answer = self.resetSettings(routeFrom, answer)
        except Exception as e:
            _logger.info('Message from Odoo To Gate could not be dispatched - Exception {}'.format(e))
            answer["error"] = e

        return answer

    @http.route('/things/gates/ras/outgoing/<routeTo>',
            type = 'json',
            auth = 'public',
            methods=['POST'],
            csrf = False)    
    def messageToGate(self, routeTo, **kwargs):
        answer = {"error": None}
        try:
            data                = http.request.jsonrequest

            productCategory     = self.get_productCategory(data)
            question            = data.get('question', None)

            if  productCategory == "RAS"        and  \
                question        == "Routine":
                answer = routine.answerRas2routineQuestion(routeTo, data, answer)

        except Exception as e:
            _logger.info('Message from Odoo To Gate could not be dispatched - Exception {}'.format(answer))
            answer["error"] = e
        #_logger.debug('Answer from Odoo To Gate  {answer}'.format(answer))
        return answer
