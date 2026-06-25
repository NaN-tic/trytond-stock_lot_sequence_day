import datetime
from unittest.mock import patch

from decimal import Decimal

from trytond.modules.company.tests import (CompanyTestMixin, create_company,
    set_company)
from trytond.pool import Pool
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.transaction import Transaction

from trytond.modules.stock_lot_sequence_day import ir as day_ir

RealDateTime = datetime.datetime


class StockLotSequenceDayTestCase(CompanyTestMixin, ModuleTestCase):
    'Test StockLotSequenceDay module'
    module = 'stock_lot_sequence_day'

    @with_transaction()
    def test_lot_sequence_day_cutover(self):
        pool = Pool()
        Template = pool.get('product.template')
        Product = pool.get('product.product')
        Uom = pool.get('product.uom')
        Sequence = pool.get('ir.sequence')
        Lot = pool.get('stock.lot')
        ModelData = pool.get('ir.model.data')
        SequenceType = pool.get('ir.sequence.type')

        company = create_company()
        with set_company(company):
            unit, = Uom.search([
                    ('name', '=', 'Unit'),
                    ])

            sequence_type = SequenceType(ModelData.get_id(
                    'stock_lot', 'sequence_type_stock_lot'))
            sequence, = Sequence.create([{
                    'name': 'Test Lot Day Sequence',
                    'sequence_type': sequence_type.id,
                    'company': None,
                    'type': 'yymmdd',
                    'prefix': '${date_y_m_d}',
                    'padding': 4,
                    'day_change_time': datetime.time(22, 0),
                    }])
            sequence_no_prefix, = Sequence.create([{
                    'name': 'Test Lot Day Sequence No Prefix',
                    'sequence_type': sequence_type.id,
                    'company': None,
                    'type': 'yymmdd',
                    'padding': 4,
                    'number_increment': 1,
                    'day_change_time': datetime.time(22, 0),
                    }])
            sequence_no_prefix.padding = 4
            sequence_no_prefix.number_increment = 1
            sequence_no_prefix.type = 'yymmdd'
            sequence_no_prefix.on_change_type()
            self.assertEqual(sequence_no_prefix.padding, 0)
            self.assertEqual(sequence_no_prefix.number_increment, 0)
            sequence_long, = Sequence.create([{
                    'name': 'Test Lot Day Sequence Long',
                    'sequence_type': sequence_type.id,
                    'company': None,
                    'type': 'yyyymmdd',
                    'day_change_time': datetime.time(22, 0),
                    }])
            sequence_long.padding = 4
            sequence_long.number_increment = 1
            sequence_long.type = 'yyyymmdd'
            sequence_long.on_change_type()
            self.assertEqual(sequence_long.padding, 0)
            self.assertEqual(sequence_long.number_increment, 0)
            template = Template(
                name='Test Lot Sequence Day',
                list_price=Decimal(10),
                cost_price=Decimal(3),
                default_uom=unit,
                lot_sequence=sequence,
                )
            template.save()
            product = Product(template=template)
            product.save()

            with Transaction().set_context(date=datetime.date(2026, 6, 25)):
                with patch.object(day_ir.datetime, 'datetime') as mock_datetime:
                    mock_datetime.now.return_value = RealDateTime(
                        2026, 6, 25, 21, 59)
                    self.assertEqual(
                        sequence_no_prefix.on_change_with_preview(), '260625')
                    self.assertEqual(
                        sequence_long.on_change_with_preview(), '20260625')
                    self.assertEqual(sequence_long.get(), '20260625')
                    lot, = Lot.create([{'product': product.id}])
                    self.assertEqual(lot.number, '260625')

                with patch.object(day_ir.datetime, 'datetime') as mock_datetime:
                    mock_datetime.now.return_value = RealDateTime(
                        2026, 6, 25, 22, 0)
                    self.assertEqual(sequence_long.get(), '20260626')
                    lot, = Lot.create([{'product': product.id}])
                    self.assertEqual(lot.number, '260626')

                self.assertEqual(sequence.day_change_time,
                    datetime.time(22, 0))


del ModuleTestCase
