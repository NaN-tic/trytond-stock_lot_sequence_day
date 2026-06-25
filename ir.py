# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import datetime

from trytond.i18n import gettext
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval
from trytond.tools import timezone as tz
from trytond.transaction import Transaction, without_check_access
from trytond.ir.sequence import MissingError, sql_sequence


class Sequence(metaclass=PoolMeta):
    __name__ = 'ir.sequence'

    day_change_time = fields.Time('Day Change Time',
        help='Time from which the next day is used for the sequence.',
        states={
            'invisible': ~Eval('type').in_(['yymmdd', 'yyyymmdd']),
            'required': Eval('type').in_(['yymmdd', 'yyyymmdd']),
            }, depends=['type'])

    @classmethod
    def __setup__(cls):
        super(Sequence, cls).__setup__()
        yymmdd = ('yymmdd', 'YYMMDD (2-digit year)')
        yyyymmdd = ('yyyymmdd', 'YYYYMMDD (4-digit year)')
        if yymmdd not in cls.type.selection:
            cls.type.selection.append(yymmdd)
        if yyyymmdd not in cls.type.selection:
            cls.type.selection.append(yyyymmdd)

    @fields.depends('type')
    def on_change_type(self):
        if self.type in {'yymmdd', 'yyyymmdd'}:
            self.padding = 0
            self.number_increment = 0

    @staticmethod
    def default_day_change_time():
        return datetime.time(22, 0)

    @classmethod
    def _effective_date(cls, sequence, date=None):
        pool = Pool()
        Date = pool.get('ir.date')
        Company = pool.get('company.company')
        context = Transaction().context
        if date is None:
            date = context.get('date') or Date.today()
        if sequence.type not in {'yymmdd', 'yyyymmdd'}:
            return date
        company_id = context.get('company')
        timezone = tz.SERVER
        if company_id:
            company = Company(company_id)
            if company.timezone:
                timezone = tz.get_tzinfo(company.timezone)
        if sequence.day_change_time and datetime.datetime.now(
                timezone).time() >= sequence.day_change_time:
            date += datetime.timedelta(days=1)
        return date

    @classmethod
    def _day_value(cls, sequence):
        date = cls._effective_date(sequence)
        if sequence.type == 'yyyymmdd':
            return date.strftime('%Y%m%d')
        return date.strftime('%y%m%d')

    @classmethod
    def _get_sequence(cls, sequence):
        if sequence.type in {'yymmdd', 'yyyymmdd'}:
            return cls._day_value(sequence)
        if sequence.type == 'incremental':
            transaction = Transaction()
            if sql_sequence and not cls._strict:
                cursor = transaction.connection.cursor()
                cursor.execute('SELECT nextval(\'"%s"\')'
                    % sequence._sql_sequence_name)
                number_next, = cursor.fetchone()
                transaction.counter += 1
                sequence._local_cache.pop(sequence.id, None)
            else:
                number_next = sequence.number_next_internal
                cls.write([sequence], {
                        'number_next_internal': (number_next
                            + sequence.number_increment),
                        })
            return f'{number_next:0>{sequence.padding}d}'
        return super(Sequence, cls)._get_sequence(sequence)

    @fields.depends('type', 'padding', 'number_next', methods=['_timestamp'])
    def _get_preview_sequence(self):
        if self.type in {'yymmdd', 'yyyymmdd'}:
            return self._day_value(self)
        if self.type == 'incremental':
            number_next = self.number_next or 0
            padding = self.padding or 0
            return f'{number_next:0>{padding}d}'
        return super()._get_preview_sequence()

    @without_check_access
    def get(self, _lock=False):
        '''
        Return the next sequence value
        '''
        cls = self.__class__
        try:
            sequence = cls(self.id)
        except TypeError:
            raise MissingError(gettext('ir.msg_sequence_missing'))
        if _lock:
            sequence.lock()
        if sequence.type in {'yymmdd', 'yyyymmdd'}:
            return cls._day_value(sequence)
        date = cls._effective_date(sequence)
        return '%s%s%s' % (
            cls._process(sequence.prefix, date),
            cls._get_sequence(sequence),
            cls._process(sequence.suffix, date),
            )

    @fields.depends('prefix', 'suffix', 'type', 'day_change_time',
        methods=['_get_preview_sequence'])
    def on_change_with_preview(self, name=None):
        if self.type in {'yymmdd', 'yyyymmdd'}:
            return self._day_value(self)
        date = self._effective_date(self)
        return '%s%s%s' % (
            self._process(self.prefix, date),
            self._get_preview_sequence(),
            self._process(self.suffix, date),
            )
