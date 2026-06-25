# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import ir
from . import product


def register():
    Pool.register(
        ir.Sequence,
        product.ConfigurationDefaultLotSequence,
        module='stock_lot_sequence_day', type_='model')
