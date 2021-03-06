# -*- coding: utf-8 -*-
{
    'name': "Estate",

    'summary': """
        Palm Oil Plantation.""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Cayadi Sutanto <cayadi.sutanto@palmagroup.co.id>, Probo Sukmohadi <probo.sukmohadi@palmagroup.co.id>",
    'website': "http://www.palmagroup.co.id",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Agriculture',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock', 'hr_indonesia', 'account', 'mail', 'base_autoreset_sequence'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'templates.xml',
        'views/estate.xml',
        'views/estate_activity_view.xml',
        'views/estate_upkeep.xml',
        'views/estate_hr_view.xml',
        'views/inherited_product_category_view.xml',
        'views/inherited_hr_indonesia_view.xml',
        'res_config_view.xml',
        'data/config_data.xml',
        'data/estate_uom_data.xml',
        'data/hr_data.xml',
        'views/report_estate_division.xml',
        'views/report_assistant_daily.xml',
        'estate_report.xml',
        'data/ir_sequence_data.xml',
    ],
    # only loaded in demonstration mode (prerequisite data should be processed first)
    'demo': [
        'data/demo.xml',
        'data/account_analytic_demo.xml',
        'data/estate_demo.xml',
        'data/stock.location.csv',
        'data/estate.block.template.csv',
        'data/hr_employee_demo.xml',
        'data/estate.parameter.csv',
        'data/estate.parameter.value.csv',
        'data/estate.stand.hectare.csv',
        'data/product.template.csv',
        'data/hr_contract_demo.xml',
        'data/estate_hr_team_demo.xml',
        'data/inherited_product_demo.xml',
        'data/estate.activity.csv',
        'data/activity_material_demo.xml',
        'data/upkeep_demo.xml',
    ],
}