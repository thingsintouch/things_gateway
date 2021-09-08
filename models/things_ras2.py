from odoo import models, fields
from uuid import uuid4
from odoo.addons.base.res.res_partner import _tz_get
#from odoo.addons.base.models.res_partner import _tz_get # >= odoo 12.0
import logging
_logger = logging.getLogger(__name__)

class ThingsRAS2(models.Model):
    _name = 'things.ras2'
    _inherit = ['things.basis']
    _description = 'Model for the RFID Attendance Terminal'
    _rec_name = 'RASxxx'

  # Factory Settings ########################################################
    firmwareAtShipment = fields.Char(readonly = True)
    productName = fields.Char("Type", readonly = True)
    productionDate = fields.Char(readonly = True)
    productionLocation = fields.Char(readonly = True)
    productionNumber = fields.Char(readonly = True)
    qualityInspector = fields.Char(readonly = True)
    SSIDreset = fields.Char(readonly = True)

    # Machine ID identifies the linux machines (Gateway) uniquely
    hashed_machine_id = fields.Char(readonly = True)

    _sql_constraints = [ (  'hashed_machine_id_uniq',
                            'UNIQUE (hashed_machine_id)',
                            'Machine ID must be unique.') ]
# RAS2 Device Setup ##############################################################
    
    https = fields.Boolean(readonly = True)
    odoo_host = fields.Char(readonly = True)
    odoo_port = fields.Char(readonly = True)
    odooConnectedAtLeastOnce = fields.Boolean(readonly = True)
    odooUrlTemplate = fields.Char(readonly = True) ###################### to deprecate
    hasCompletedSetup =  fields.Boolean(readonly = True)

  # UPDATED_FROM_ODOO_ONLY_ON_START ###############################################

    RASxxx = fields.Char("Name",
        default= "not defined",
        required=True)

    def generate_route(self):
      return self.env['things.route'].create({}).route

    routefromOdooToDevice =fields.Char(
        string = 'route from Odoo To Device',
        help = 'route for outgoing data from the database to the thing/gate',
        default = generate_route,
        store = True,
        compute_sudo = False,
        readonly = True
        )
        
    routefromDeviceToOdoo =fields.Char(
        string = 'route from Device To Odoo',
        help = 'route for incoming data from the thing/gate to the database',
        default = generate_route,
        store = True,
        compute_sudo = False,
        readonly = True
        )

    version_things_module_in_Odoo = fields.Char(readonly = True)  

    ownIpAddress = fields.Char("Local IP Address", readonly = True)


  # UPDATED_FROM_ODOO_ON_ROUTINE_CALLS #####################################
    #  can be changed anytime when connected to Odoo through routine calls
    ssh =  fields.Boolean(string= 'ssh enabled?',
        required= True,
        default= True,
        help="ssh on Terminal enabled??")
    showEmployeeName = fields.Boolean(string= 'Show Employee Name?',
        required= True,
        default= True,
        help="Show Employee Name on the Terminal Display?")
    sshPassword = fields.Char()
    language = fields.Selection(
        [("ENGLISH","ENGLISH"),("ESPA\u00d1OL","ESPA\u00d1OL"),("FRAN\u00c7AIS","FRAN\u00c7AIS")],
        string='Display Messages Language',
        required=True,
        default= "ENGLISH",
        help="In which language should the terminal show the messages?")
    tz = fields.Selection(
        _tz_get, string='Timezone', required=True,
        default=lambda self: self._context.get('tz') or self.env.user.tz or 'Europe/Berlin',
        help="In which timezone the Device will display time.")
    time_format = fields.Selection(
        [("12 hour","12 hour"),("24 hour","24 hour")],
        string='12 or 24-hour',
        required=True,
        default= "12 hour",
        help="am/pm or 00:00 to 23:59")
    timeoutToCheckAttendance = fields.Float(string='Timeout to register Attendance [s]',
        required=True,
        default= 3.0,
        help="Timeout of request to register Attendance XMLRPC")  
    periodEvaluateReachability = fields.Float(string='Period Odoo Reachability [s]',
        required=True,
        default= 5.0,
        help="Time between checks if Odoo is reachable (connected)")  
    periodDisplayClock = fields.Float(string='Period Refresh Clock [s]',
        required=True,
        default= 10.0,
        help="Time between refreshes of the clock display [s]")   
    timeToDisplayResultAfterClocking = fields.Float(string='How Long Display Text shown [s]',
        required=True,
        default= 1.2,
        help="How Long will the Display show the Result after Clocking [s]")   
    location = fields.Char(string='Location',
        required=True,
        default= "to be defined",
        help="Where is the Terminal located?")
    shouldGetFirmwareUpdate = fields.Boolean("Update Firmware and Reboot (now)",
        required=True,
        default= False,
        help = "Update the firmware after rebooting")
    setRebootAt = fields.Datetime('Reboot once the Terminal at this Time',
        help = 'Time when the Terminal will be rebooted',
        default = None)
    shutdownTerminal = fields.Boolean("Shutdown (Turn Off the Terminal)",
        help = "Shutdown the Terminal immediately",
        default = False)
    isRemoteOdooControlAvailable = fields.Boolean(readonly = True)  
    gitBranch = fields.Char()
    gitCommit = fields.Char()
    gitRemote = fields.Char()
    updateOTAcommand = fields.Char()
    doFactoryReset = fields.Boolean(string='Factory Reset',
        required=True,
        default= False,
        help="Factory Reset after Rebooting. The Terminal will have to be Setup again.")
    updateAvailable = fields.Boolean(string='Firmware Update Available',
        required=True,
        default= False,
        readonly = True)
    lastConnectionOdooTerminal = fields.Datetime('Last Connection',
        help = "Timestamp of the last successful connection between the Device and Odoo",
        default = None,
        readonly = True)
    minimumTimeBetweenClockings = fields.Integer(string='Minimum Time between Clockings [s]',
        required=True,
        default= 300,
        help="How long is clocking again blocked [s]")
    period_odoo_routine_check =  fields.Integer(string='Time between Routine checks [s]',
        required=True,
        default= 12,
        help="How long between every information exchange between Terminal RAS and Odoo [s]")

  # UPDATED_FROM_DEVICE: Updates are done through the Firmware #############################
    installedPythonModules = fields.Char("Installed Python Modules",
        readonly = True,
        help="Installed Python Modules in the Terminal")
    firmwareVersion = fields.Char("Firmware Version", readonly = True)  
    lastFirmwareUpdateTime = fields.Datetime('Last Firmware Update',
        help = 'Last Update of the Firmware of the Terminal',
        default = None,
        readonly = True)
    lastTimeTerminalStarted = fields.Datetime('Last Time Device Started',
        default = None,
        readonly = True)
    updateFailedCount = fields.Integer("How Many Times the last Firmware Update Failed",
        readonly = True)

    incrementalLog = fields.Text('Last Log Entries', readonly = True)
    lastLogMessage = fields.Integer('Last Log Line Received', default = 0, readonly = True)

    # messages for display

    card_registered = fields.Char("Text Display for 'clocking registered'",
        default = "Registered",
        help = "Text to show on Display when card is registered for async clocking")
    too_little_time_between_clockings = fields.Char("Text Display for 'too little time between clockings'",
        default = "Too Soon",
        help = "Text to show on Display when card is not registered for async clocking because there was too little time between card swipes")

    setup_password = fields.Char("Setup Password (Terminal)",
        help = "Password needed to introduce new Parameters (SSID, Odoo URL) during the Setup of the Terminal")

    
