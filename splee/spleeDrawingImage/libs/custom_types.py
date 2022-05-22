import re
class Coord(tuple):
    """Represent a coordinate to a point with x and y axis attributes"""
    def __new__(cls, *args, **kwargs):
        """A coordinate with a 'x' and 'y' value.

        Exemples of initializations:

        Args:
            x  (int)       : The `x` coordinate, needs to be set with `y`.
                             N.B. :If `xy` is present, this one is ignored.
            y  (int)       : The `y` coordinate, needs to be set with `x`.
                             N.B. :If `xy` is present, this one is ignored.
            xy (tuple[int]): The tuple forming the `xy` coordinates `(x, y)`
                             N.B. :If present, all others are ignored.
        """
        if kwargs and not args:
            args = tuple(kwargs.get('xy') or [kwargs.get(x) for x in ['x','y']])
        if (isinstance(args[0],(list,tuple))):
            args = args[0]
        if len(args) != 2:
            raise Exception("Not enough arguments, need a `x` and a `y` values, got %s" % args)
        return super(Coord, cls).__new__(cls, tuple(args))
    @property
    def x(self):
        return self[0]
    @property
    def y(self):
        return self[1]

class Size(tuple):
    """Represent the size of a rectangle with a width and a height attributes"""
    def __new__(cls, *args, **kwargs):
        """A size with a 'width' and 'height' value.

        Exemples of initializations:

        Args:
            width  (int)     : The `width` of the object, needs to be set with
                               `height`.
                               N.B. :If `xy` is present, this one is ignored.
            width  (int)     : The `height`of the object, needs to be set with
                               `width`.
                               N.B. :If `xy` is present, this one is ignored.
            size (tuple[int]): The tuple forming the `size` of the object, it
                               takes the following form `(width, height)`.
                               N.B. :If present, all others are ignored.
        """
        if kwargs and not args:
            args = tuple(kwargs.get('size') or [kwargs.get(x)
                                                    for x in ['width','height']])
        if (isinstance(args[0],(list, tuple))):
            args = args[0]
        if len(args) != 2:
            raise Exception("Both `width` and `height` values are needed.")
        return super(Size, cls).__new__(cls, tuple(args))
    @property
    def width(self):
        return self[0]
    @property
    def height(self):
        return self[1]
    @property
    def center(self):
        """Returns a relative coordinate of the center for this element"""
        return Coord(self.hcenter, self.vcenter) if None not in self else None
    @property
    def hcenter(self):
        return self.width//2 if self.width else None
    @property
    def vcenter(self):
        return self.height//2 if self.height else None
    def grow_by(self, value):
        return (self.width+value, self.height+value)


class Color(tuple):
    def __new__(cls, *color):
        # If the color is in the hex format (i.e.:'#33ffdd'), convert it in
        ## the decimal format (i.e.:'(0,233,255)
        if len(color) == 1:
            color = color[0]
            if isinstance(color, str) and len(color) == 7:
                # cut it into 3 val tuple in decimal
                color = color[1:] # remove the '#' at the begining
                # the actual conversion, re.split to separate each couple
                color = tuple(int(i,16) for i in filter(lambda c: c != '',
                                                        re.split('(..)', color)))
            # if we got a 'RGB' add a 4th value at 255 to make it 'RGBA but opaque
        if len(color) == 3:
            color = color + (255,)
        return super(Color, cls).__new__(cls, tuple(color))
    def __to_hex(self, val):
        return hex(val)[-2]
    def lightness(self, percent, way=None):
        """ don't use it, it's in development
        Return a new Color object with different lightness

        The new Color object will have its lightness changed accordint to the
        `percent` and `way` provided. 

        i.e.: if the `percent` is '5' and `way` is '-1', then the returned 
              Color will be 5% darker than the original.
        Args:
            percent (float): The difference of lightness in percentage.
                             Minimum is 0 and maximum 100.
            way     (int)  : A value to tell if we want lighter or darker color.
                             A negative value makes a darker color this a
                             positive value makes a ligher color.
                             Logically you want this to be -1 or 1.
        """
        percent = max(min(percent,100),0)
        score = sum(self.RGB)
        score_diff = percent*765//100
        way = percent if way is None else way
        way = way//abs(way) if way != 0 else 0
        return tuple([max(v-v*score_diff//score,0) for v in self.RGB]) + (self.A,)
    @property
    def R(self):
        """Returns the decimal value for the red (R) part."""
        return self[0]
    @property
    def G(self):
        """Returns the decimal value for the green (G) part."""
        return self[1]
    @property
    def B(self):
        """Returns the decimal value for the blue (B) part."""
        return self[2]
    @property
    def A(self):
        """Returns the decimal value for the transparency (A) part."""
        return self[3]
    @property
    def RGB(self):
        """Returns a tuple of decimal values for RGB like (<red>,<green>,<blue>)."""
        return self[:3]
    @property
    def hex_R(self):
        """Returns a string containing the hex value for the red (R) part"""
        return self.__to_hex(self.R)
    @property
    def hex_G(self):
        """Returns a string containing the hex value for the green (G) part"""
        return self.__to_hex(self.G)
    @property
    def hex_B(self):
        """Returns a string containing the hex value for the blue (B) part"""
        return self.__to_hex(self.B)
    @property
    def hex_RGB(self):
        """Returns a string hex values for RGB like '#RRGGBB'."""
        return "#%s%s%s" % (self.hex_R, self.hex_G, self.hex_B)
    def trans(self, percent=50):
        """Returns a new Color object with a new value for the transparency.

        Args:
            percent (float): The value of the new transparency, 100 = invisible
        """
        percent = max(min(percent,100), 0)
        return Color(self.RGB+(255-(percent*255//100),))
    @property
    def opaque(self):
        """Returns a new Color object but completly opaque"""
        return self.trans(0)
    def darker(self, percent=5):
        """Returns a new Color object darker by the value provided.

        Args:
            percent (float) : The percentage by which the color will be darker."""
        return self.lightness(percent,-1)
    def lighter(self, percent=5):
        """Returns a new Color object lighter by the value provided.

        Args:
            percent (float) : The percentage by which the color will be lighter."""
        return self.lightness(percent, 1)

class Padding(list):
    def __init__(self, *args, **kwargs):

        if kwargs and not args:
            args = list(kwargs.get('padding') or
                   [kwargs.get(x) for x in ['top','right', 'bottom','left']])
        if isinstance(args[0], (list,tuple)):
            args = args[0]
        while len(args) < 4:
            args[len(args)] = None
        super(Padding, self).__init__(list(args))

    @property
    def top(self):
        return self[0]
    @top.setter
    def top(self, value):
        self[0] = value

    @property
    def right(self):
        return self[1]
    @right.setter
    def right(self, value):
        self[1] = value

    @property
    def bottom(self):
        return self[2]
    @bottom.setter
    def bottom(self, value):
        self[2] = value

    @property
    def left(self):
        return self[3]
    @left.setter
    def left(self, value):
        self[3] = value

class RegionCoords(list):
    """Represent a rectangular retion with upper left and lower right corners"""
    def __init__(self, coord_list):
        for corner in coord_list:
            if corner is not None and len(corner) !=2:
                raise TypeError('RegionCoord must be initialized with [(x,y),(x,y)] format, got %s' % coord_list)
        super(RegionCoords, self).__init__(coord_list)
    @property
    def left_x(self):
        return min(self[0][0],self[1][0])
    @property
    def left(self):
        return min(self[0][0],self[1][0])
    @property
    def right_x(self):
        return max(self[0][0],self[1][0])
    @property
    def right(self):
        return max(self[0][0],self[1][0])
    @property
    def upper_y(self):
        return min(self[0][1],self[1][1])
    @property
    def lower_y(self):
        return max(self[0][1],self[1][1])
    @property
    def top(self):
        return self.upper_y
    @property
    def bottom(self):
        return self.lower_y
    @property
    def hcenter(self):
        return self.left + (self.right - self.left)//2
    @property
    def vcenter(self):
        return self.top + (self.bottom - self.top)//2
    @property
    def bottom_center(self):
        return (self.hcenter, self.bottom)
    @property
    def upper_center(self):
        return (self.hcenter, self.top)
    @property
    def left_center(self):
        return (self.left_x, self.vcenter)
    @property
    def right_center(self):
        return (self.right_x, self.vcenter)
    @property
    def upper_left(self):
        return (self.left_x, self.upper_y)
    @property
    def upper_right(self):
        return (self.right_x, self.upper_y)
    @property
    def lower_left(self):
        return (self.left_x, self.lower_y)
    @property
    def lower_right(self):
        return (self.right_x, self.lower_y)
    @property
    def width(self):
        return self.right - self.left
    def text_at_top_left(self, vert_offset=2, hor_offset=2):
        return (self.left+hor_offset, self.top+vert_offset)
    def text_at_mid_left(self, fontsize, vert_offset=0, hor_offset=2):
        return (self.left+hor_offset, self.vcenter-fontsize//2 + vert_offset)
    def text_at_bottom_left(self, fontsize, vert_offset=-2, hor_offset=2):
        return (self.left+hor_offset, self.bottom-fontsize+vert_offset)
    # NOTE: Those need some adjustment, the could take the lenghtof the text
    ##      in pixels or the text and the font to evaluate it themselve
    ##      Anyway, for now it stays like that, so they actually give the right
    ##      of the text
    def text_at_top_right(self, vert_offset=2, hor_offset=-2):
        return (self.right+hor_offset, self.top+vert_offset)

    def text_at_mid_right(self, fontsize, vert_offset=0, hor_offset=-2):
        return (self.right+hor_offset, self.vcenter-fontsize//2 + vert_offset)
    def text_at_bottom_right(self, fontsize, vert_offset=-2, hor_offset=-2):
        return (self.right+hor_offset, self.bottom-fontsize+vert_offset)
    @property
    def top_bottom_limits(self):
        return [self.top, self.bottom]
    @property
    def height(self):
        return self.lower_y - self.upper_y
    def shrink(self, by_px=1):
        return RegionCoords([(self.left_x+by_px,  self.top+by_px),
                             (self.right_x-by_px, self.bottom-by_px)])
    def anchor(self, for_region):
        x = self.hcenter+randint(-self.width//4,self.width//4)
        if for_region == 'upper':
            return (x, self.bottom)
        else:
            return (x, self.top)

class LinkCoords(RegionCoords):
    """It's the coordinates that join two points in a graphic"""
    pass
