# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool, PoolMeta


class ConfigurationDefaultLotSequence(metaclass=PoolMeta):
    __name__ = 'product.configuration.default_lot_sequence'

    @classmethod
    def default_default_lot_sequence(cls):
        pool = Pool()
        ModelData = pool.get('ir.model.data')
        try:
            return ModelData.get_id(
                'stock_lot_sequence_day', 'sequence_lot_day')
        except KeyError:
            return super().default_default_lot_sequence()
