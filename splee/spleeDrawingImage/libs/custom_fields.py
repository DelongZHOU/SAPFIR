from .peewee.peewee import CharField
import re
from .custom_types import *


class RegionCoordsField(CharField):
    def __init__(self, null      = False,
                       index     = False,
                       unique    = False,
                       db_column = None,
                       default   = None,
                       choices   = None):
        super(RegionCoordsField, self).__init__(null       = null,
                                                index      = index,
                                                unique     = unique,
                                                db_column  = db_column,
                                                default    = default,
                                                choices    = choices,
                                                max_length = 27)
    # conversion des donnees de la bd vers python
    def python_value(self, value):
        if value:
            return RegionCoords(eval(value.encode('ascii')))
        return super(RegionCoordsField, self).python_value(value)

    # conversion des donnees de python vers la bd
    def db_value(self, value):
        if value:
            value = str(RegionCoords(value))
        return super(RegionCoordsField, self).db_value(value)
class LinkCoordsField(RegionCoordsField):
    pass

class MisereCharField(CharField):
    # conversion des donnees de la bd vers python
    def python_value(self, value):
        return super(MisereCharField, self).python_value(value)
    # conversion des donnees de python vers la bd
    def db_value(self, value):
        return super(MisereCharField, self).db_value(value)

class CoordField(CharField):
    def __init__(self, null      = False,
                       index     = False,
                       unique    = False,
                       db_column = None,
                       default   = None,
                       choices   = None):
        super(CoordField, self).__init__(null       = null,
                                         index      = index,
                                         unique     = unique,
                                         db_column  = db_column,
                                         default    = default,
                                         choices    = choices,
                                         max_length = 11)
    # conversion des donnees de la bd vers python
    def python_value(self, value):
        if value:
            return Coord(eval(value.encode('ascii')))
        return super(CoordField, self).python_value(value)
    # conversion des donnees de python vers la bd
    def db_value(self, value):
        if value:
            value = str(Coord(value))
        return super(CoordField, self).db_value(value)

class SizeField(CharField):
    def __init__(self, null      = False,
                       index     = False,
                       unique    = False,
                       db_column = None,
                       default   = None,
                       choices   = None):
        super(CoordField, self).__init__(null       = null,
                                         index      = index,
                                         unique     = unique,
                                         db_column  = db_column,
                                         default    = default,
                                         choices    = choices,
                                         max_length = 11)
    def python_value(self, value):
        if value:
            return Size(eval(value.encode('ascii')))
        return super(SizeField, self).python_value(value)
    def db_value(self, value):
        if value:
            value = str(Size(value))
        return super(SizeField, self).db_value(value)

class ColorField(CharField):
    def __init__(self, null      = False,
                       index     = False,
                       unique    = False,
                       db_column = None,
                       default   = None,
                       choices   = None):
        super(ColorField, self).__init__(null       = null,
                                         index      = index,
                                         unique     = unique,
                                         db_column  = db_column,
                                         default    = default,
                                         choices    = choices,
                                         max_length = 17)
    def python_value(self, value):
        if value:
            return Color(eval(value.encode('ascii')))
        return super(ColorField, self).python_value(value)

    def db_value(self, value):
        if value:
            value = str(Color(value))
        return super(ColorField, self).db_value(value)
