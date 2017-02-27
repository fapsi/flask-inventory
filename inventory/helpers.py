from wtforms import ValidationError
from wtforms.validators import InputRequired


class ItemsRequiredExactly(InputRequired):
    """
    A version of the ``InputRequired`` validator that works with relations,
    to require a minimum number of related items.
    """

    def __init__(self, min=1, message=None):
        """

        :param min:
        :param message:
        """
        super(ItemsRequiredExactly, self).__init__(message=message)
        self.min = min

    def __call__(self, form, field):
        """

        :param form:
        :param field:
        """
        if len(field.data) < self.min or len(field.data) > self.min:
            if self.message is None:
                message = field.ngettext(
                    u"Only %d item is allowed!",
                    u"Only least %d items are allowed!",
                    self.min
                ) % self.min
            else:
                message = self.message

            raise ValidationError(message)
        if field.data[0]["networkname"] == None:
            raise ValidationError(str(field.data[0]["networkname"]))


