from odoo import http, fields
import time
import json
from . import routine
import logging

_logger = logging.getLogger(__name__)

factory_settings = [
  "firmwareAtShipment",
  "productName",
  "productionDate",
  "productionLocation",
  "productionNumber",
  "qualityInspector",
  "SSIDreset",
  "hashed_machine_id"]

defined_on_ack_from_odoo = [
  #"terminalIDinOdoo",
  #"RASxxx",
  "routefromDeviceToOdoo",
  "routefromOdooToDevice",
  "version_things_module_in_Odoo",
  "ownIpAddress"]

defined_on_ack_from_device = [
  #"installedPythonModules",
  "firmwareVersion",
  "lastFirmwareUpdateTime",
  "lastTimeTerminalStarted",
  "updateFailedCount"]

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
  "lastConnectionOdooTerminal"]

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
            _logger.info(f'data: {data}') ##############

            question = data.get('question', None)
            if "Please" in question:
                answer["version"]= "12.0.2" # version of this things module as in __manifest__.py
            else:
                answer["error"]="Wrong question"
                answer["version"]= None
                _logger.error('someone is asking the wrong question (Get Module Version of ThingsRasGate Class)')
        except Exception as e:
            _logger.info(f'Get Module Version of ThingsRasGate Class - Exception {e}')
            answer["error"] = e
        _logger.info(f'answer to Get Module Version of ThingsRasGate Class: {answer}') ################
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
                _logger.info(f'get data to transfer - key {o}')
                data_to_transfer[o] = data.get(o)
            data_to_transfer['lastConnectionOdooTerminal'] = str(fields.Datetime.now())
            _logger.info(f'data to transfer {data_to_transfer}')        
            return data_to_transfer


        answer = {"error": None}
        try:
            data = http.request.jsonrequest
            #_logger.info(f'data: {data}')
            hashed_machine_id = data.get('hashed_machine_id', None)
            _logger.info(f'hashed_machine_id: {hashed_machine_id}')

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
                _logger.info(f'key {p}')
                answer[p] = ras2_Dict.get(p)

            answer["terminalIDinOdoo"] = str(ras2_to_be_acknowledged.id)

        except Exception as e:
            _logger.info(f'the new gate request could not be dispatched - Exception {e}')
            answer["error"] = e
        _logger.info(f'answer to request to acknowledge RAS: {answer} ')
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
                _logger.info(f'resetSettings RAS - Error: {answer["error"]} ')
        except Exception as e:
            _logger.info(f'resetSettings RAS - Exception {e}')
            answer["error"] = e

        _logger.info(f'resetSettings RAS: {answer} ')
        return answer

    @http.route('/things/gates/ras/incoming/<routeFrom>',
            type = 'json',
            auth = 'public',
            methods=['POST'],
            csrf = False)
    def messageFromGate(self, routeFrom, **kwargs):
        answer = {"error": None}
        try:
            data = http.request.jsonrequest
            productName = data.get('productName', None)
            question = data.get('question', None)

            if productName == "RAS2" and question == "Reset":
                answer = self.resetSettings(routeFrom, answer)
        except Exception as e:
            _logger.info(f'Message from Odoo To Gate could not be dispatched - Exception {e}')
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
            data = http.request.jsonrequest
            productName = data.get('productName', None)
            question = data.get('question', None)
            _logger.info(f'productName {productName} - question {question}')
            if productName == "RAS2.1" and question == "Routine":
                answer = routine.answerRas2routineQuestion(routeTo, data, answer)
        except Exception as e:
            _logger.info(f'Message from Odoo To Gate could not be dispatched - Exception {e}')
            answer["error"] = e
        _logger.info(f'Answer from Odoo To Gate  {answer}')
        return answer
