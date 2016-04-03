"""
Serbian specific form helpers.
"""

from __future__ import unicode_literals

import datetime
import re

from django.core.validators import EMPTY_VALUES
from django.forms import ValidationError
from django.forms.fields import CharField, Select, ChoiceField
from django.utils.translation import ugettext_lazy as _

from .rs_postalcodes import RS_POSTALCODES_CHOICES


class RSJMBGField(CharField):
    """
    A form for validating Serbian personal identification number.

    Additionally stores gender, nationality and birthday to self.info dictionary.
    """

    default_error_messages = {
        'invalid': _('This field should contain exactly 13 digits.'),
        'date': _('The first 7 digits of the JMBG must represent a valid past date.'),
        'checksum': _('The JMBG is not valid.'),
    }
    jmbg = re.compile('^(\d{2})(\d{2})(\d{3})(\d{2})(\d{3})(\d)$')

    def clean(self, value):
        super(RSJMBGField, self).clean(value)
        if value in EMPTY_VALUES:
            return ''

        value = value.strip()

        m = self.jmbg.match(value)
        if m is None:
            raise ValidationError(self.error_messages['invalid'])

        # Validate EMSO
        s = 0
        int_values = [int(i) for i in value]
        for a, b in zip(int_values, list(range(7, 1, -1)) * 2):
            s += a * b
        chk = s % 11
        if chk == 0:
            K = 0
        else:
            K = 11 - chk

        if K == 10 or int_values[-1] != K:
            raise ValidationError(self.error_messages['checksum'])

        # Extract extra info in the identification number
        day, month, year, nationality, gender, chksum = [int(i) for i in m.groups()]

        if year < 890:
            year += 2000
        else:
            year += 1000

        # validate birthday
        try:
            birthday = datetime.date(year, month, day)
        except ValueError:
            raise ValidationError(self.error_messages['date'])
        if datetime.date.today() < birthday:
            raise ValidationError(self.error_messages['date'])

        self.info = {
            'gender': gender < 500 and 'male' or 'female',
            'birthdate': birthday,
            'nationality': nationality,
        }
        return value


class RSTaxNumberField(RSJMBGField):
    """
    In Serbia, taxes number and personal identification number are the same.
    """
    pass


class RSPostalCodeField(ChoiceField):
    """
    Serbian post codes field.
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('choices', RS_POSTALCODES_CHOICES)
        super(RSPostalCodeField, self).__init__(*args, **kwargs)


class RSPostalCodeSelect(Select):
    """
    A Select widget that uses Serbian postal codes as its choices.
    """
    def __init__(self, attrs=None):
        super(RSPostalCodeSelect, self).__init__(attrs,
                                                 choices=RS_POSTALCODES_CHOICES)


class RSPhoneNumberField(CharField):
    """
    Serbian phone number field.

    Phone number must contain at least local area code.
    Country code can be present.

    Examples:

    * +38111XXXXXX
    * 0038111XXXXXX
    * 011XXXXXX
    * 013XXXXXX
    * 0630XXXXX

    """

    default_error_messages = {
        'invalid': _('Enter phone number in form +381XXXXXXXX or 0XXXXXXXX.'),
    }
    phone_regex = re.compile('^(?:(?:00|\+)381|0)(\d{7,8})$')

    def clean(self, value):
        super(RSPhoneNumberField, self).clean(value)
        if value in EMPTY_VALUES:
            return ''

        value = value.replace(' ', '').replace('-', '').replace('/', '')
        m = self.phone_regex.match(value)

        if m is None:
            raise ValidationError(self.error_messages['invalid'])
        return m.groups()[0]
