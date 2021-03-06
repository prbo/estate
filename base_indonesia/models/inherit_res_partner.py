from openerp import models, fields, api, exceptions
from psycopg2 import OperationalError

from openerp import SUPERUSER_ID
import openerp
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare, float_is_zero
from datetime import datetime, date,time
from openerp.tools.translate import _
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar
from openerp import tools
import re
import threading


class InheritResPartner(models.Model):

    @api.multi
    def purchase_procurement_staff(self):
        return self.env.ref('purchase_request.group_purchase_request_procstaff', False).id

    @api.multi
    def _get_user(self):
        #find User
        user= self.env['res.users'].browse(self.env.uid)

        return user

    @api.multi
    def _get_employee_request(self):
        #find User Employee

        employee = self.env['hr.employee'].search([('user_id','=',self._get_user().id)])

        return employee

    _inherit = 'res.partner'

    _description = 'Inherit Res Partner'

    # product_category_ids = fields.Many2many('product.category',string='Category Product')
    partner_product = fields.Char('Partner Product')
    state = fields.Selection([('draft','Draft'),('done','Done'),('confirm','Confirm'),
                       ('reject','Reject')],string='Status',default='draft')
    confirmed_by = fields.Many2one('res.users','Confirmed By')
    approved_by = fields.Many2one('res.users','Approved By')
    assign_to = fields.Many2one('res.users','Assign To')
    partner_code = fields.Char('Partner Code')
    partner_running_number = fields.Char('Partner Running Number',compute='_generate_running_number_vendor')
    businesspermit_ids = fields.One2many('base.indonesia.vendor.business.permit','partner_id')
    businessteaxes_ids = fields.One2many('base.indonesia.taxes','partner_id')
    street = fields.Char('Street')
    street2 = fields.Char('Street2')
    zip = fields.Char('Zip',size=24, change_default=True)
    city =fields.Char('City')
    state_id =fields.Many2one("res.country.state", 'State')
    country_id = fields.Many2one('res.country', 'Country')
    email = fields.Char('Email')
    phone = fields.Char('Phone')
    mobile = fields.Char('Mobile')
    type = fields.Selection(selection_add=[
                                           ('identity', 'Identity'),
                                           ('mailing', 'Mailing'),
                                           ('work', 'Work')
                                           ])


    @api.multi
    @api.depends('partner_code')
    def _generate_running_number_vendor(self):
        for item in self:

            name_substring = '' if not item.name else item.name
            substring_first_caracter = name_substring[:1]
            if item.partner_code:

                vendor_code = substring_first_caracter.upper() + ' - ' + item.partner_code
                item.partner_running_number = vendor_code

    @api.multi
    def _get_requestedby_manager(self):
        #search Employee

        user= self.env['res.users']
        user_id = user.search([('id','=',self._get_user().id)])

        #searching Employee Manager

        employeemanager = self.env['hr.employee'].search([('user_id','=',user_id.id)]).parent_id.id
        requested_manager = self.env['hr.employee'].search([('id','=',employeemanager)]).user_id.id
        manager_user = user.search([('id','=',requested_manager)])

        return manager_user

    @api.multi
    def action_confirm(self):
        for item in self:
            check_employee = 0
            arrEmployee = []
            arrParent = []
            hr_employee  = item._get_employee_request()
            employee = item.env['hr.employee']
            for hr in hr_employee:
                arrEmployee.append(hr.id)
            #searching id in parent id employee
            employee_parent_id = employee.search([('parent_id','in',arrEmployee)])

            for parent in employee_parent_id:
                arrParent.append(parent.id)

            if arrParent == []:
                check_employee = check_employee + 1
            item.write(
                {
                 'confirmed_by':item._get_user().id,
                 'assign_to':item._get_requestedby_manager().id if check_employee > 0 else item._get_user().id ,
                 'state':'confirm'}
            )
            item.send_mail_template()

    @api.multi
    def action_approved(self):
        for item in self:
            if item.assign_to.id != item._get_user().id:
                raise exceptions.ValidationError('User not Match with Field Assign To')
            else:
                item.write(
                    {
                     'partner_code':item.env['ir.sequence'].next_by_code('sequence.vendor'),
                     'approved_by':item._get_user().id,
                     'state':'done'
                    }
                )

    @api.multi
    def action_set_to_draft(self):
        for item in self:
            if item.assign_to.id != item._get_user().id:
                raise exceptions.ValidationError('User not Match with Field Assign To')
            else:
                item.write(
                    {'assign_to':item.confirmed_by.id,
                     'state':'draft'}
                )

    @api.multi
    def action_nonactive(self):
        for item in self:
            item.write({'active':False})

    #Email Template Code Starts Here

    @api.one
    def send_mail_template(self):
            # Find the e-mail template
            template = self.env.ref('purchase_indonesia.email_template_res_partner_vendor')
            # You can also find the e-mail template like this:
            # template = self.env['ir.model.data'].get_object('mail_template_demo', 'example_email_template')
            # Send out the e-mail template to the user
            self.env['mail.template'].browse(template.id).send_mail(self.id,force_send=True)

    @api.multi
    def database(self):
        for item in self:
            db = item.env.cr.dbname

            return db

    @api.multi
    def web_url(self):
        for item in self:
            web = item.env['ir.config_parameter'].sudo().get_param('web.base.url')
            return web

    @api.multi
    def email_model(self):
        for item in self:
            model = item._name
            return model
        
    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            name = record.name or ''
            if record.parent_id and not record.is_company:
                if not name and record.type in ['invoice', 'delivery', 'other', 'identity', 'mailing', 'work']:
                    name = dict(self.fields_get(cr, uid, ['type'], context=context)['type']['selection'])[record.type]
                name = "%s, %s" % (record.parent_name, name)
            if context.get('show_address_only'):
                name = self._display_address(cr, uid, record, without_company=True, context=context)
            if context.get('show_address'):
                name = name + "\n" + self._display_address(cr, uid, record, without_company=True, context=context)
            name = name.replace('\n\n','\n')
            name = name.replace('\n\n','\n')
            if context.get('show_email') and record.email:
                name = "%s <%s>" % (name, record.email)
            if context.get('html_format'):
                name = name.replace('\n', '<br/>')
            res.append((record.id, name))
        return res
    
    @api.model
    def _get_default_image(self, is_company, colorize=False):
        if getattr(threading.currentThread(), 'testing', False) or self.env.context.get('install_mode'):
            return False
 
        if self.env.context.get('partner_type') == 'delivery':
            img_path = openerp.modules.get_module_resource('base', 'static/src/img', 'truck.png')
        elif self.env.context.get('partner_type') == 'invoice':
            img_path = openerp.modules.get_module_resource('base', 'static/src/img', 'money.png')
        elif self.env.context.get('partner_type') == 'identity':
            img_path = openerp.modules.get_module_resource('base_indonesia', 'static/src/img', 'identity.png')
        elif self.env.context.get('partner_type') == 'mailing':
            img_path = openerp.modules.get_module_resource('base_indonesia', 'static/src/img', 'mailing.png')
        elif self.env.context.get('partner_type') == 'work':
            img_path = openerp.modules.get_module_resource('base_indonesia', 'static/src/img', 'work.png')
        else:
            img_path = openerp.modules.get_module_resource(
                'base', 'static/src/img', 'company_image.png' if is_company else 'avatar.png')
        with open(img_path, 'rb') as f:
            image = f.read()
 
        # colorize user avatars
        if not is_company and colorize:
            image = tools.image_colorize(image)
 
        return tools.image_resize_image_big(image.encode('base64'))
 
    @api.model
    def create(self, vals):
        try:
            vals['image'] = self.with_context(partner_type=vals['type'])._get_default_image(False, False)
        finally:
            partner = super(InheritResPartner, self).create(vals)
            return partner
    
    def _get_res_partner_by_type(self, partner_type):
        res = self.env['res.partner'].search([('parent_id','=',self.id),('type','=',partner_type)], order='id desc')
        return res[0] if res else False
        
class ResPartnerVendorBusinessPermit(models.Model):

    _name = 'base.indonesia.vendor.business.permit'
    _description = 'Vendor Business Permit and Certificate of Company Registration'

    partner_id = fields.Many2one('res.partner','Res Partner')
    no_identity_business = fields.Char('No SIUP/SIUJK/SIUPAL')
    due_date_business_permit = fields.Date('Due Date Business Permit')
    published_by_business_permit = fields.Char('Published By')
    no_certificate_of_company_registration = fields.Char('No Certificate of Company Registration')
    due_date_certificate_of_company_cegistration = fields.Date('Due Date Certificate of Company Registration')
    published_by_certificate_of_company_cegistration = fields.Char('Published By Certificate of Company Registration')

class ResPartnerTaxes(models.Model):

    _name = 'base.indonesia.taxes'
    _description = 'Partner Taxes'

    partner_id = fields.Many2one('res.partner','Res Partner')
    npwp_no = fields.Char('NPWP No')
    nppkp_no = fields.Char('NPPKP No')




