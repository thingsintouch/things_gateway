# Copyright 2021 thingsintouch.com

from odoo import http, fields
import time
import logging
import json

_logger = logging.getLogger(__name__)

display_messages = [
    "card_registered",
    "too_little_time_between_clockings"
    ]

keys_routine_call = [
    "setRebootAt",
    'shouldGetFirmwareUpdate',
    'location',
    'shutdownTerminal',
    'tz',
    'time_format',
    "minimumTimeBetweenClockings", # in seconds
    "period_odoo_routine_check", # in seconds
    "timeToDisplayResultAfterClocking",
    "setup_password"
    ]

def answerRas2routineQuestion(routeTo, data, answer):
    try:
        Ras2Model = http.request.env['things.ras2']
        EmployeeModel = http.request.env['hr.employee'] 
        ras2_in_database = Ras2Model.sudo().search(
            [('routefromOdooToDevice', '=', routeTo)])
        
        if ras2_in_database:
            ras2_Dict = ras2_in_database.sudo().read()[0]
            ras2_in_database.sudo().write({
                'lastConnectionOdooTerminal': fields.Datetime.now()
                })
            incrementalLog_received = data.get('incrementalLog', False)
            # _logger.info('incrementalLog_received_str {}'.format(incrementalLog_received))
            if incrementalLog_received:
                # incrementalLog_received += "\n"               
                incrementalLog_stored = ras2_Dict['incrementalLog'] or " "
                log_length = len(incrementalLog_stored)
                # _logger.info('Length of incremental log in storage {}'.format(log_length))
                if log_length > 50000:
                    incrementalLog_capped = incrementalLog_stored[:45000]
                else:
                    incrementalLog_capped = incrementalLog_stored

                new_inc_log = incrementalLog_received + incrementalLog_capped
                ras2_in_database.sudo().write({
                        'incrementalLog' : new_inc_log,               
                })

            params_in_answer = keys_routine_call + display_messages
            for p in params_in_answer:
                answer[p] = ras2_Dict.get(p)

            ras2_in_database.sudo().write({
                "shouldGetFirmwareUpdate": False,
                "shutdownTerminal": False               
                })            

            answer['rfid_codes_to_names'] = EmployeeModel.sudo().get_rfid_codes_with_names()['rfid_codes_to_names']
        else:
            answer["error"] = "This should never occur. Method answerRasroutineQuestion"
            _logger.info('Routine Question RAS - Error: {}'.format(answer["error"]))
    except Exception as e:
        _logger.info('Routine Question RAS - Exception {}'.format(e))
        answer["error"] = e

    _logger.debug('answer to routine Question RAS: {}'.format(answer))
    return answer
