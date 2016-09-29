from openerp import models, fields, api, exceptions
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar
import time
import datetime
from openerp import tools


class VehicleOilLog(models.Model):

    _name="estate.vehicle.log.oil"
    _inherits = {'fleet.vehicle.cost':'cost_id'}
    _description = "Inherit view fuel log"

    def on_change_vehicle(self, cr, uid, ids, vehicle_id, context=None):
        if not vehicle_id:
            return {}
        vehicle = self.pool.get('fleet.vehicle').browse(cr, uid, vehicle_id, context=context)
        odometer_unit = vehicle.odometer_unit
        driver = vehicle.driver_id.id
        cr.execute('select max(value) as value_odometer from fleet_vehicle_odometer where vehicle_id = %d' %(vehicle.id))
        odometer = cr.fetchone()[0]
        return {
            'value': {
                'odometer_unit': odometer_unit,
                'odometer': odometer,
                'purchaser_id': driver,
            }
        }

    def on_change_liter(self, cr, uid, ids, liter, price_per_liter, amount, context=None):
        #need to cast in float because the value receveid from web client maybe an integer (Javascript and JSON do not
        #make any difference between 3.0 and 3). This cause a problem if you encode, for example, 2 liters at 1.5 per
        #liter => total is computed as 3.0, then trigger an onchange that recomputes price_per_liter as 3/2=1 (instead
        #of 3.0/2=1.5)
        #If there is no change in the result, we return an empty dict to prevent an infinite loop due to the 3 intertwine
        #onchange. And in order to verify that there is no change in the result, we have to limit the precision of the
        #computation to 2 decimal
        liter = float(liter)
        price_per_liter = float(price_per_liter)
        amount = float(amount)
        if liter > 0 and price_per_liter > 0 and round(liter*price_per_liter,2) != amount:
            return {'value' : {'amount' : round(liter * price_per_liter,2),}}
        elif amount > 0 and liter > 0 and round(amount/liter,2) != price_per_liter:
            return {'value' : {'price_per_liter' : round(amount / liter,2),}}
        elif amount > 0 and price_per_liter > 0 and round(amount/price_per_liter,2) != liter:
            return {'value' : {'liter' : round(amount / price_per_liter,2),}}
        else :
            return {}

    def on_change_amount(self, cr, uid, ids, liter, price_per_liter, amount, context=None):
        #need to cast in float because the value receveid from web client maybe an integer (Javascript and JSON do not
        #make any difference between 3.0 and 3). This cause a problem if you encode, for example, 2 liters at 1.5 per
        #liter => total is computed as 3.0, then trigger an onchange that recomputes price_per_liter as 3/2=1 (instead
        #of 3.0/2=1.5)
        #If there is no change in the result, we return an empty dict to prevent an infinite loop due to the 3 intertwine
        #onchange. And in order to verify that there is no change in the result, we have to limit the precision of the
        #computation to 2 decimal
        liter = float(liter)
        price_per_liter = float(price_per_liter)
        amount = float(amount)
        if amount > 0 and liter > 0 and round(amount/liter,2) != price_per_liter:
            return {'value': {'price_per_liter': round(amount / liter,2),}}
        elif amount > 0 and price_per_liter > 0 and round(amount/price_per_liter,2) != liter:
            return {'value': {'liter': round(amount / price_per_liter,2),}}
        elif liter > 0 and price_per_liter > 0 and round(liter*price_per_liter,2) != amount:
            return {'value': {'amount': round(liter * price_per_liter,2),}}
        else :
            return {}

    def _get_default_service_type(self, cr, uid, context):
        try:
            model, model_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'fleet', 'type_service_refueling')
        except ValueError:
            model_id = False
        return model_id

    cost_id = fields.Many2one('fleet.vehicle.cost',ondelete='cascade',required=True)
    cost_type_id = fields.Many2one('fleet.service.type')
    purchaser_id = fields.Many2one('res.partner',domain="['|',('customer','=',True),('employee','=',True)]")
    inv_ref = fields.Char('Invoice Reference')
    vendor_id = fields.Many2one('res.partner')
    cost_amount = fields.Float(related='cost_id.amount',store=True)
    notes = fields.Text('notes')
    liter = fields.Float('Liter',store=True)
    price_per_liter = fields.Float('Price Per Liter',related='product_id.standard_price',store=True)
    product_id = fields.Many2one('product.product','Product',domain="[('type','=','consu'),('uom_id','=',11)]")

    _defaults = {
        'cost_subtype_id': _get_default_service_type,
        'cost_type': 'fuel',
    }

class NurseryVehicle(models.Model):

    _inherit="fleet.vehicle"
    _description = "inherit information detail to fleet management"

    def return_action_to_open_oil(self, cr, uid, ids, context=None):
        """ This opens the xml view specified in xml_id for the current vehicle """
        if context is None:
            context = {}
        if context.get('xml_id'):
            res = self.pool.get('ir.actions.act_window').for_xml_id(cr, uid ,'fleet', context['xml_id'], context=context)
            res['context'] = context
            res['context'].update({'default_vehicle_id': ids[0]})
            res['domain'] = [('vehicle_id','=', ids[0])]
            return res
        return False

    @api.multi
    @api.depends('oil_log_count')
    def _count_all_service(self):
             if self:
                 count = self.env['estate.vehicle.log.oil'].search([('vehicle_id.id','=',self.id)])
                 self.oil_log_count = len(count)

    oil_log_count = fields.Integer('Oil Log Count',compute='_count_all_service')
    other_service_log_count = fields.Integer('Other Service Log Count')
    sparepart_log_count = fields.Integer('Sparepart Log Count')
    category_unit_id = fields.Many2one('master.category.unit',domain=[('type','=','1')])
    no_vehicle=fields.Char('No Vehicle')
    # vehicle_type=fields.Selection([('1','Vehicle Internal'), ('2','Vehicle External')])
    # employee_driver_id=fields.Many2one('hr.employee')
    capacity_vehicle = fields.Integer('Capacity')
    # status_vehicle = fields.Selection([('1','Available'), ('2','Breakdown'),('3','Stand By')])




class InheritActivity(models.Model):

    _inherit = 'estate.activity'
    _description = 'inherit status'

    status = fields.Selection([('1','Available'), ('2','Breakdown'),('3','Stand By')])

class InheritFuel(models.Model):

    _inherit ='fleet.vehicle.log.fuel'
    _description = 'inherit product_id in fuel'

    product_id = fields.Many2one('product.product',domain="[('type','=','consu'),('uom_id','=',11)]")


class VehicleSparepartLog(models.Model):

    _name="estate.vehicle.log.sparepart"
    _inherits = {'fleet.vehicle.cost':'cost_id'}
    _description = "Inherit view cost"

    def on_change_vehicle(self, cr, uid, ids, vehicle_id, context=None):
        if not vehicle_id:
            return {}
        vehicle = self.pool.get('fleet.vehicle').browse(cr, uid, vehicle_id, context=context)
        odometer_unit = vehicle.odometer_unit
        driver = vehicle.driver_id.id
        return {
            'value': {
                'odometer_unit': odometer_unit,
                'purchaser_id': driver,
            }
        }

    def _get_default_service_type(self, cr, uid, context):
        try:
            model, model_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'fleet', 'type_service_service_8')
        except ValueError:
            model_id = False
        return model_id

    name=fields.Char()
    cost_id = fields.Many2one('fleet.vehicle.cost',ondelete='cascade',required=True)
    unit = fields.Integer('Unit Sparepart')
    product_id = fields.Many2one('product.product','Product',domain="[('type_vehicle','=',True),('type','=','product'),('uom_id','=',1)]",store=True)
    cost_amount = fields.Float(related='cost_id.amount',store=True)
    purchaser_id = fields.Many2one('res.partner',domain="['|',('customer','=',True),('employee','=',True)]")
    inv_ref = fields.Char('Invoice Reference')
    vendor_id = fields.Many2one('res.partner')
    price_per_unit = fields.Float('Price unit',readonly=1,related='product_id.standard_price',store=True)
    total_amount = fields.Float('Total Amount',compute="_compute_total_sparepart",store=True)
    notes = fields.Text('notes')

    #computed
    @api.depends('price_per_unit','unit','total_amount')
    def _compute_total_sparepart(self):
        if self.price_per_unit and self.unit:
            self.total_amount = self.price_per_unit * self.unit
        return True

    #onchange

    _defaults = {
        'cost_subtype_id': _get_default_service_type,
        'cost_type': 'services'
    }

class VehicleOtherServiceLog(models.Model):

    _name="estate.vehicle.log.otherservice"
    _inherits = {'fleet.vehicle.cost':'cost_id'}
    _description = "Inherit view cost"

    def on_change_vehicle(self, cr, uid, ids, vehicle_id, context=None):
        if not vehicle_id:
            return {}
        vehicle = self.pool.get('fleet.vehicle').browse(cr, uid, vehicle_id, context=context)
        odometer_unit = vehicle.odometer_unit
        driver = vehicle.driver_id.id
        return {
            'value': {
                'odometer_unit': odometer_unit,
                'purchaser_id': driver,
            }
        }

    def _get_default_service_type(self, cr, uid, context):
        try:
            model, model_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'fleet', 'type_service_service_8')
        except ValueError:
            model_id = False
        return model_id


    name=fields.Char()
    cost_id = fields.Many2one('fleet.vehicle.cost',ondelete='cascade',required=True)
    unit = fields.Integer('Unit Service')
    product_id = fields.Many2one('product.product','Product',domain="[('type_vehicle','=',True),('type','=','service'),('uom_id','=',1)]",store=True)
    cost_amount = fields.Float(related='cost_id.amount')
    purchaser_id = fields.Many2one('res.partner',domain="['|',('customer','=',True),('employee','=',True)]")
    inv_ref = fields.Char('Invoice Reference')
    vendor_id = fields.Many2one('res.partner')
    price_per_service = fields.Float('Price Service',store=True,related='product_id.standard_price')
    total_amount = fields.Float('Total Amount',compute="_compute_total_otherservice",)
    notes = fields.Text('notes')

    #computed
    @api.depends('price_per_service','unit','total_amount')
    def _compute_total_otherservice(self):
        if self.price_per_service and self.unit:
            self.total_amount = self.price_per_service * self.unit
        return True

    _defaults = {
        'cost_subtype_id': _get_default_service_type,
        'cost_type': 'other'
    }

class InheritProduct(models.Model):

    _inherit ='product.template'

    type_vehicle = fields.Boolean('Type Vehicle',default=False)

class MasterCategoryUnit(models.Model):

    _name= 'master.category.unit'

    name=fields.Char()
    type=fields.Selection([('1','Vehicle'), ('2','Unit ALL')])

class FleetVehicleTimesheet(models.Model):

    _name = 'fleet.vehicle.timesheet'

    name = fields.Char()
    vehicle_timesheet_code = fields.Char("VTS",store=True)
    date_timesheet = fields.Date('Date',store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done')], string="State",store=True)
    timesheet_ids = fields.One2many('inherits.fleet.vehicle.timesheet','owner_id','Timesheet Vehicle')

    #sequence
    def create(self, cr, uid,vals, context=None):
        vals['vehicle_timesheet_code']=self.pool.get('ir.sequence').get(cr, uid,'fleet.vehicle.timesheet')
        res=super(FleetVehicleTimesheet, self).create(cr, uid,vals)
        return res

    @api.one
    def action_draft(self):
        """Set Timesheet State to Draft."""
        self.state = 'draft'

    @api.one
    def action_confirmed(self):
        """Set Timesheet state to Confirmed."""
        self.state = 'confirmed'

    @api.one
    def action_approved(self):
        """Approved  Timesheet"""
        name = self.name
        self.write({'name':"Vehicle Timesheet %s " %(name)})
        self.do_create_vehicle_date()
        self.do_create_vehicle_odometer_log()
        self.state = 'done'

    @api.multi
    def do_create_vehicle_date(self):
        date = False
        fleet = self.env['fleet.vehicle.timesheet'].search([('id','=',self.id)])
        for date in fleet:
            date_data = {
                'date_activity_transport': date.date_timesheet,
            }
            self.env['inherits.fleet.vehicle.timesheet'].search([('owner_id','=',fleet.id)]).write(date_data)
        return True

    @api.multi
    def do_create_vehicle_odometer_log(self):
        odometer = False
        for odometer in self.env['inherits.fleet.vehicle.timesheet'].search([('owner_id','=',self.id)]):
            odometer_data = {
                'name':'Odometer',
                'date': odometer.date_activity_transport,
                'vehicle_id': odometer.vehicle_id.id,
                'value': odometer.end_km,
            }
            self.env['fleet.vehicle.odometer'].create(odometer_data)
        return True

    #todo constraint timesheet
    # @api.multi
    # @api.constrains('timesheet_ids','date_timesheet')
    # def _constraint_date_timesheet_vehicle(self):
    #     #constraint date in timesheet vehicle must be same in time sheet ids
    #     for item in self:
    #         if item.date_timesheet:
    #             if item.timesheet_ids:
    #                 for vehicletimesheet in item.timesheet_ids:
    #                     date = vehicletimesheet.date_activity_transport
    #                     if date > item.date_timesheet:
    #                         error_msg = "Date Timesheet Line not more than \"%s\" in Date Form" % self.date_timesheet
    #                         raise exceptions.ValidationError(error_msg)
    #                     elif date < item.date_timesheet:
    #                         error_msg = "Date Timesheet Line must be same \"%s\" in Date Form" % self.date_timesheet
    #                         raise exceptions.ValidationError(error_msg)

    @api.multi
    @api.constrains('date_timesheet')
    def _constraint_date_timesheet(self):
        tempdate = []
        for item in self:
            date = item.env['fleet.vehicle.timesheet'].search([('state','=','done')])
            for date in date:
                tempdate.append(date.date_timesheet)
            if item.date_timesheet in tempdate:
                error_msg = "Date Timesheet %s Not Use More Than One" %item.date_timesheet
                raise exceptions.ValidationError(error_msg)


class FleetVehicleTimesheetInherits(models.Model):

    _name = 'inherits.fleet.vehicle.timesheet'
    _inherits = {'estate.timesheet.activity.transport':'timesheet_id'}

    timesheet_id = fields.Many2one('estate.timesheet.activity.transport',ondelete='cascade',required=True)

    @api.multi
    @api.onchange('dc_type')
    def _onchange_dc_type(self):
        if self:
            self.dc_type = 5

    @api.multi
    @api.onchange('employee_id')
    def _onchange_driver(self):
        arrDriver = []
        if self:
            hrjob = self.env['hr.job'].search([('name','=','Driver')],limit = 1).id
            driver = self.env['hr.employee'].search([('job_id.id','=',hrjob)])
            for d in driver:
                arrDriver.append(d.id)
        return {
                'domain':{
                    'employee_id':[('id','in',arrDriver)]
                }
        }

    @api.multi
    @api.onchange('vehicle_id')
    def onchange_vehicle(self):
        arrVehicletransport =[]
        if self:
            if self.dc_type == '1':# dc type 1 refer to seed do
                dotransportir = self.env['estate.nursery.dotransportir'].search([('seeddo_id.id','=',self.owner_id)])
                for vehicle in dotransportir:
                    arrVehicletransport.append(vehicle.estate_vehicle_id.id)
                return {
                    'domain':{
                        'vehicle_id':[('id','in',arrVehicletransport)]
                        }
                    }
            else :
                vehicle=self.env['fleet.vehicle'].search([('maintenance_state_id.id','=',21)])
                for v in vehicle:
                    arrVehicletransport.append(v.id)
                return {
                    'domain':{
                        'vehicle_id':[('id','in',arrVehicletransport)]
                        }
                    }












