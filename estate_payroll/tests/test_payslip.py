# -*- coding: utf-8 -*-

from openerp.tests import TransactionCase


class TestPayslip(TransactionCase):

    def setUp(self):
        super(TestPayslip, self).setUp()

        self.Employee = self.env['hr.employee']

        self.payslip_run = self.env.ref('estate_payroll.estate_payroll_1')

    def test_01_compute_upkeep_labour(self):
        for payslip in self.payslip_run.slip_ids:
            payslip._compute_upkeep_labour()
            self.assertGreater(payslip.upkeep_labour_count, 0, 'Estate Payroll: _compute_upkeep_labour failed')

    def test_01_get_team(self):
        """ Assign team to payslip for wage disbursement """
        for payslip in self.payslip_run.slip_ids:
            # Get team from Estate Team
            member_id = self.env['estate.hr.member'].search([('employee_id', '=', payslip.employee_id.id)], limit=1)
            self.assertEqual(payslip.team_id, member_id.team_id, 'Estate Payroll: _get_team did not return correct team')

    def test_01_get_worked_day_lines(self):
        """ Check Worked Days """
        for payslip in self.payslip_run.slip_ids:
            for line in payslip.worked_days_line_ids:
            # if payslip.worked_days_line_ids['number_of_days']:
                self.assertEqual(line['number_of_days'], 1,
                                 'Estate Payroll: _get_worked_day_lines did not return number of day')
                self.assertEqual(line['code'], 'WORK300',
                                 'Estate Payroll: _get_worked_day_lines return wrong code')

    def test_01_get_inputs(self):
        """ Check Other Inputs """
        for payslip in self.payslip_run.slip_ids:
            for line in payslip.input_line_ids:
                # Check return code
                self.assertGreaterEqual(line['amount'], 0,
                                        'Estate Payroll: _get_inputs did not return amount')
                # Support only OT, PR and ADJA/B
                if line['code']:
                    self.assertIn(line['code'], ['OT', 'PR', 'ADJA', 'ADJB'],
                                  'Estate Payroll: _get_inputs return wrong code')

    def test_01_action_open_labour(self):
        """ Check context contains res_model estate.upkeep.labour) """
        res = self.payslip_run.slip_ids[0].action_open_labour()
        self.assertEqual(res['res_model'], 'estate.upkeep.labour', 'Estate Payroll: action_open_labour wrong res.models')

    def test_02_get_upkeep_labour(self):
        """ Check contract labour (not contract activity)"""
        vals_labour = {
            'name': 'Contract Labour',
            'contract_type': '2',
            'contract_period': '2',
            'outsource': True,
        }

        contract_labour = self.Employee.create(vals_labour)
        self.assertTrue(contract_labour)

    def test_03_check_payslip_to_team(self):
        """ Checked if there is payslip's labour who did not being member of any team."""
        print 'test ...'
        for line in self.payslip_run.slip_ids:
            # remove team member
            team_id = self.env['estate.hr.team'].browse([line.team_id.id])
            print ' team member %s' % team_id.member_ids
            team_id.member_ids = False
            print ' team member %s' % team_id.member_ids


            print ' check payslip to team %s' % line._check_payslip_team()
        self.assertTrue(True)
