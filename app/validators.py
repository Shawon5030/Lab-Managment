import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class NumberSpecialCharValidator:

    def validate(self, password, user=None):
        if not re.search(r'[0-9@#$%^&+=]', password):
            raise ValidationError(
                _("Password must contain at least 8 digit."),
                code='password_no_number_special',
            )

    def get_help_text(self):
        return _("Your password must contain at least 8 digit.")
