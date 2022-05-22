from __future__ import division
from .libs.peewee.peewee import *
from .libs.custom_types import *
from .libs.custom_fields import *
from PIL import ImageDraw, Image, ImageFont, ImageColor

from collections import OrderedDict as odict
from itertools import product, chain
from random import randint
import os
#from playhouse.fields import *

# GFF3 format
# seqid(number of the line) \t source_prgrm \t type(transcript,gene,exon) \t start \t end \t score \t strand \t phase(for CDS only, "not used here") \t attributes(see below)
#
# Attributes can be
# ID      : The unique id, it's used for relation with the Parent attribute
# Name    : A display name you want, optional
# Alias   : ...
# Parents : The ID of the parents
# Gap
# Derived_from
# Note
# Dbxref
# Ontology_term
# Is_circular


# Database connection
database = SqliteDatabase(":memory:", threadlocals=True)
# some tools
class ColorMap(object):
    """Available color for the automatic outlines"""
    def __init__(self):
        self.colors = ['#666699', '#663366', '#999999', '#ff66cc', '#ff6600',
                       '#000066', '#66cc33', '#993366', '#660066', '#996600',
                       '#ff3333', '#3333ff', '#cc3333', '#330099', '#9999ff',

                       '#9933ff', '#ff3300', '#ffcc00', '#ff9933', '#999933',
                       '#666633', '#663333', '#990033', '#9900cc', '#339933',
                       '#6600cc', '#cc33ff', '#9933cc', '#66cc00', '#ff0000',
                       '#ff9900', '#003300', '#330066', '#ff0099', '#ff6666',
                       '#cc66cc', '#6699cc', '#999900', '#9999cc', '#996633',
                    '#cccc33', '#990000', '#0033cc', '#cc99cc', '#003366',
                       #comment this to be pink#'#9966ff', '#99cc00', '#cc3300', '#cc0033', '#3333cc',
                       #comment this to be pink#'#cc99ff', '#cc33cc', '#669966', '#336633', '#ff3366',
                       #comment this to be pink #'#6666cc', '#663300', '#333300', '#99cc33', '#339900',
                       #comment this to be pink#'#333366', '#996699', '#000099', '#669999', '#333333',
                       #'#ff0033', '#ff6633', '#669900', '#cc6699', '#6600ff',
                       #comment this to be pink#'#ff0066', '#ff9966', '#6633ff', '#cccc66', '#006600',
                       #comment this to be pink + botom #'#3366ff', '#333399', '#cc9999', '#339966', '#cc6600',
                       '#663399', '#cc9900', '#330033', '#336666', '#99cc66',#do not commenth this to be pink
                       #'#003399', '#cc3366', '#3300cc', '#cc0000', '#666666',
                       #comment this to be green + purple#'#660033', '#660099', '#ff3399', '#660000', '#3300ff',
                       #comment this to be green + purple#'#cccc00', '#9900ff', '#993300', '#cc6666', '#993333',
                       #comment this to be green + purple#'#336699', '#6699ff', '#003333', '#ff00cc', '#999966',
                       #comment this to be green + purple# '#ffcc66', '#330000', '#0000cc', '#ff9999', '#ffcc33',
                       #comment this to be green + purple#'#cc0066', '#990099', '#ff00ff', '#6633cc', '#ff6699',
                       #comment this to be green + purple# '#666600', '#669933', '#336600', '#cc9966', '#ff99cc',
                       #comment this to be green + purple #comment this to be purple  #'#0033ff', '#cc0099', '#cc3399', '#993399', '#996666',
                       #comment this to be purple  #'#ff33cc', '#cc00cc', '#006633', '#cc66ff', '#ff33ff',
                       #comment this to be purple #'#cc00ff', '#0000ff', '#3366cc', '#cc9933', '#ff99ff',
                       '#9966cc', '#990066', '#ff66ff', '#cc6633', '#6666ff',

         ]
        pass
    def select_color(self, to_hash):
        return self.colors[hash(to_hash) % (len(self.colors)-1)]
    pass

class Params(object):
    # paddings

    #spadding_section = Padding(200,0,200,0)
    #padding_img     = Padding(0,25,0,25)

    # sizes (None are to be computed
    size_intron     = Size(20,5)
    height_min_exon = Size(None, 40)
    size_feature    = Size(None, 7)
    width_label     = Size(120, None)
    boxes_col_size  = Size(1750, None)
    title_col_size  = Size(170, None)
    line_thickness  = 2
    labels_space    = 2

    size_tick_region      = Size(None, 30)
    size_up_labels_region = Size(None,80)
    size_lo_labels_region = Size(None,80)

    color_bg = Color(238,238,238,255)


    color_intron        = Color(125,125,125,255)
    color_boxes_fill    = Color(255,255,255,255)
    color_boxes_outline = Color(0,0,0,255)
    color_coding_fill   = Color(131,210,252,128)


    color_label_outline = None

    color_label_fill    = Color(128,0,128,50)


    font_size_title     = 18
    font_size_label     = 26
    font_file_title     = "%s/assets/fonts/Noxchi_Arial.ttf" % os.path.dirname(__file__)
    font_file_label     = "%s/assets/fonts/Noxchi_Arial.ttf" % os.path.dirname(__file__)

    color_font_title    = Color(0,0,0,255)
    #color_font_label    = Color(0,0,0,255)
    color_font_label = Color(255,255,255,255)


    size_gene_strip     = Size(None, 10)#height_min_exon.height//2)
    color_gene_strip    = None
    colormap  = ColorMap()
    def __init__(self, **kwargs):
        self.title = None # WTF
        self.data = None
        self.width = None
        self.scale = None # will be computed later

    @property
    def font_title(self):
        return ImageFont.truetype(self.font_file_title, self.font_size_title)
    @property
    def font_label(self):
        return ImageFont.truetype(self.font_file_label, self.font_size_label)
    @property
    def img_width(self):
        return self.boxes_col_size.width + self.title_col_size.width
    @property
    def lbls_regions_height(self):
        return self.size_up_labels_region.height + \
               self.size_lo_labels_region.height

class RegionMatrix(object):
    """Separate the region as a matrix of cells.

    Separate the region as a matrix of cells identified with their position
    as (column, row), each one beeing a RegionCoords within the region
    covered by the region_coords attribute having a size as defined by the
    label_size attribute
    """
    def __init__(self, label_size, region_coord, region_pos, space=Params.labels_space):
        """Initialization of the matrix region

        Args:
            label_size (tuple[int]): width and height of the labels
            region_coord (list): coordinates of the region [(x1,y1),(x2,y2)]
            space (int): Space to have between labels
        """
        self.label_size = label_size
        self.space = space
        self.cell_size = (i+1 for i in label_size)
        self.coords = RegionCoords(region_coord)
        self.region_pos = region_pos #'upper' if self.coords.upper_left == (0,5) else 'lower'
        if not isinstance(self.coords, RegionCoords):
            self.coords = RegionCoords(self.coords)
        self.cells = odict()
        self._max_x = None
        self._max_y = None
        self._init_matrix()
        self.free_cells = self.all_cells

    def _init_matrix(self):
        """Create the actual matrix, allocating propper coordinates"""
        for x,y in self.all_cells:
            from_x_px = x*(self.label_size[0]+2*self.space)+self.coords.left_x
            to_x_px = from_x_px+self.label_size[0]+40*self.space
            from_y_px = y*(self.label_size[1]+2*self.space)+self.coords.upper_y
            to_y_px = from_y_px+self.label_size[1]+10*self.space
            cell = RegionCoords([(from_x_px+self.space, from_y_px+self.space),
                          (to_x_px-self.space,   to_y_px-self.space)])
            self.cells[(x,y)] = cell

    def __getitem__(self, slic):
        """Get one item from the matrix using a slice as [column:row]"""
        if isinstance(slic,slice):
            if slic.step is not None:
                raise Exception('Not implemented')
            return self.cells[(slic.start,slic.stop)]

    def get(self, column, row, default=None):
        """Get one item from the matrix using column, row.

        Get one item from the matrix using column, row position.

        Return `default` if it's not present which is default to `None`.

        Args:
            column  (int): The column position of the cell within the matrix.
            row     (int): The row position of the cell within the matrix.
            default (---): To return if not found, default to `None`.
        """
        try:
            return self[column:row]
        except :
            return default

    def cells_close_to(self, x_px, from_list=None):
        """Returns cells close from a 'x' position in the region.

        Returns a group of cells close from a 'x' coordinate in the region. It
        operates in as many pass as the result is empty, each pass making the 
        search wider.

        Args:
            x_px       (int): The 'x' coordinate to search cells around.
            from_list (list): A list of tuples with column and line coordinates of cells
        """
        res = []
        offset = 0
        while len(res) == 0:
            accepted = set(range(max(int(x_px)-(self.label_size[0]//2+offset),self.coords.left_x),
                                 min(int(x_px)+(self.label_size[0]//2+offset),self.coords.right_x-(self.label_size[0]+10))))
            if from_list is None:
                from_list = self.all_cells
            for cell_coord in from_list:
                cell = self.cells[cell_coord]
                span = set(range(cell.left_x, cell.right_x))
                if len(span & accepted):
                    res.append(cell_coord)
            offset += 1
        return res
    def free_cells_close_to(self, x_px):
        """Same as 'cells_close_to' but return only free cells"""
        return self.cells_close_to(x_px,from_list=self.free_cells)
    def free_cell_close_to(self, x_px):
        """Automatically returns a free cell to use from 'free_cells_close_to'"""
        closest_free_cells = self.cells_close_to(x_px,from_list=self.free_cells)
        closest_line       = closest_free_cells[randint(0,len(closest_free_cells)-1)][1]
        closest_free_cells = list(filter(lambda c: c[1] == closest_line, closest_free_cells))
        selected_cell      = closest_free_cells[0]
        self.free_cells.remove(selected_cell)
        return selected_cell
    def free_cell_coord_close_to(self, x_px):
        """Get the free cell as a RectangleCoord object """
        return self.to_coord(*self.free_cell_close_to(x_px))
    @property
    def maxx(self):
        """The biggest 'x' position from the cell matrix """
        if self._max_x is None:
            self._max_x = int(self.coords.width/(self.label_size[0]+self.space))-1
        return self._max_x
    @property
    def maxy(self):
        """The biggest 'y' position from the cell matrix """
        if self._max_y is None:
            self._max_y = int(self.coords.height/(self.label_size[1]+self.space))-1
        return self._max_y
    @property
    def maxxy(self):
        """The biggest '(x,y)' position from the cell matrix
        """
        return self.maxx,self.maxy
    @property
    def all_cells(self):
        """Return all cell position from the matrix
        """
        return list(product(range(self.maxx+1), range(self.maxy)))
    def to_coord(self, x,y):
        """Takes cell position and return the associated RectangleCoord object
        """
        cell = self[x:y]
        return RegionCoords([cell[0],cell[-1]])

class SpleeBaseModel(Model):
    params = Params
    class Meta:
        database = database
        validate_backrefs = True

    @staticmethod
    def _get_draw(imageordraw):
        if not isinstance(imageordraw, ImageDraw.ImageDraw):
             imageordraw = ImageDraw.Draw(imageordraw)
        return imageordraw

    @classmethod
    def update_or_create(cls, **kwargs):
        pk_names = (cls._meta.primary_key.name,)
        pk_args = dict()
        if pk_names[0] == '_composite_key':
            pk_names = cls._meta.primary_key.field_names
        for pk_name in pk_names:
            # exon primary key workaround
            if pk_name == 'transcript':
                pk_name += '_id'
            pk = kwargs.get(pk_name,None)
            if pk is None:
                raise TypeError("update_or_create() \
                        missing mandatory parameter, primary key '%s'" % pk_name)
            if isinstance(pk, str): pk = pk.strip()
            kwargs[pk_name] = pk
            pk_args[pk_name] = pk
        defaults = kwargs.pop('defaults',{})
        # Put default keys and values in kwargs (not as a sub dict)
        kwargs.update(defaults)
        ## workaround to be able to store tuple colors for RGBA
        try:
            # get the object with primary keys if exists
            obj = cls.select().filter(**pk_args).get()
            for k,v in kwargs.items():
                # set the values from arguments to update if needed
                setattr(obj, k,v)
            obj.save()
            return obj, False
        except cls.DoesNotExist:
            with cls._meta.database.atomic():
                #cls.create(**kwargs)
                return cls.create(**kwargs), True

## Actual models

# database models

class Bedcover(SpleeBaseModel):
    """Define the space that will hold all others

    This is a representation of the right section of the image, it holds the
    total width (probably in nucleotid), the scale to adjust it on the imgate
    then it also hold the scale for this part. More than one Bedcover can
    exists though usually only one will exists. If none are set, the method
    `prepare_database` will take the longuest children to set a default one,
    this is what will happens when generating a gene view. This entity is also
    used to draw the ticks.

    Fields:
        id          (int)          : The primary key, automatically incremented
                                     as we create new Bedcover. It's used to
                                     know the order of each section in the
                                     image.
        description (str[512],null): An optional description, if it's set, it
                                     will be draw on the top of each section.
        show        (bool,True)    : Make it possible to controle if a section
                                     will be shown, usuall you want this set at
                                     'True'.
        width       (int)          : The width in which all subelements will
                                     take place. This should be the same type
                                     of all subelements.
        img_width   (int,None)     : The size of the image part containing
                                     those elements, or in other words, the
                                     size of the right section of the image.
        scale       (float,None)   : The scale to adjust position and make it
                                     fit the image.
    """
    id          = CharField(primary_key=True, max_length=100)
    description = CharField(max_length = 512,
                            null       = True)
    show        = BooleanField(default=False)
    _start      = IntegerField(null=True)
    _end        = IntegerField(null=True)
    #_width       = IntegerField(null=True)
    _scale       = DoubleField(null=True)
    title_region = RegionCoordsField(null=True)
    graph_region = RegionCoordsField(null=True)
    total_height_pixels = IntegerField(null=True)
    class Meta:
        db_table = 'bedcovers'
    @property
    def start(self):
        self._start = self._start or min([c.start for c in self.chromosomes])
        self.save()
        return self._start
    @property
    def end(self):
        self._end = self._end or max([c.end for c in self.chromosomes])
        self.save()
        return self._end
    @property
    def width(self):
        return self.end-self.start+1
    @classmethod
    def _organize(cls):
        cur_height = 0
        for bedcover in cls.select().iterator():
            cur_height = bedcover._set_coords(cur_height)
    @classmethod
    def _draw_all(cls):
        cls._organize()
        img_width = cls.params.img_width
        img_height = cls.select(fn.Sum(Bedcover.total_height_pixels)).scalar()
        image = Image.new('RGBA', (img_width,img_height), cls.params.color_bg)
        for bedcover in cls.select().iterator():
            image = bedcover.draw(image)
        Label.draw_labels(image)
        return image
    @property
    def scale(self):
        return (self.params.boxes_col_size.width-self.params.padding_img.right)/self.width
    #def _set_scale(self):
    #    self.scale = self.params.boxes_col_size.width/self.width
    #    self.save()
    def _set_coords(self, cur_height):
        start_img = cur_height
        if self.show:
            #self._set_scale()
            self.title_region = RegionCoords([(0,cur_height),
                                              (self.params.title_col_size.width,
                                               cur_height+self.params.size_tick_region.height)])
            self.graph_region = RegionCoords([self.title_region.upper_right,
                                              (self.title_region.right_x+self.params.boxes_col_size.width,
                                               self.title_region.bottom)])
            cur_height = self.title_region.bottom
        for chromosome in self.chromosomes.iterator():
            cur_height = chromosome._set_coords(cur_height)
        self.total_height_pixels = cur_height - start_img + 1
        self.save()
    def draw(self, image):
        if self.show:
            self.__draw_title(image)
            self.__draw_legend(image)
            self.__draw_ticks(image)
        for chromosome in self.chromosomes.iterator():
            image = chromosome.draw(image)
        return image
    def __draw_title(self,image):
        draw = self._get_draw(image)
        raise Exception('NOT IMPLEMENTED - bedcover.__draw_title(image)')
    def __draw_ticks(self,image):
        draw = self._get_draw(image)
        raise Exception('NOT IMPLEMENTED - bedcover.__draw_ticks(image)')
    def __draw_legend(self,image):
        draw = self._get_draw(image)
        raise Exception('NOT IMPLEMENTED - bedcover.__draw_legend(image)')

class Label(SpleeBaseModel):
    id            = PrimaryKeyField()
    coords        = RegionCoordsField()
    region_coords = RegionCoordsField()
    link          = LinkCoordsField()
    line_thickness = IntegerField(default=Params.line_thickness)
    fill_color    = ColorField(default=Params.color_label_fill)
    outline_color = ColorField(null=True, default=Params.color_label_outline)
    font_color    = ColorField(default=Params.color_font_label)
    font_size     = IntegerField(default=Params.font_size_label)
    font_filepath = CharField(max_length=100, default=Params.font_file_label)
    display_text  = CharField(max_length=20, null=True)
#    drawn = BooleanField(null=True)
#    _links_drawn = False
    @classmethod
    def draw_labels(cls, image):
        for label in cls.select().iterator():
            label.draw_link(image)
        for label in cls.select().iterator():
            label.draw(image)
    def __draw_rectangle(self, image):
        draw = self._get_draw(image)
        for i in range(self.line_thickness-1):
            draw.rectangle(self.coords.shrink(i),
                           fill = self.fill_color,
                           outline = self.outline_color)
    def __draw_text(self, image):
        draw = self._get_draw(image)
        draw.text(self.coords.text_at_top_left(),
                  self.display_text,
                  font = ImageFont.truetype(self.font_filepath, self.font_size),
                  fill = self.font_color)
    def draw_link(self, image):
        draw = self._get_draw(image)
        draw.line(self.link, fill  = self.outline_color,
                             width = self.line_thickness)

    def draw(self, image):
        #Label._get_draw(image)
        self.__draw_rectangle(image)
        self.__draw_text(image)

    class Meta:
        db_table = 'labels'

class Chromosome(SpleeBaseModel):
    """A Chromosome"""
    id       = CharField(primary_key = True,
                         max_length  = 10)
    _start    = IntegerField(null=True)
    _end      = IntegerField(null=True)
#    width    = IntegerField(null=True)
    show     = BooleanField(default=False)

    title_area = RegionCoordsField(null=True)
    graph_area = RegionCoordsField(null=True)
    up_labels_region = RegionCoordsField(null=True)
    strands_region = RegionCoordsField(null=True)
    positive_strand_coords = RegionCoordsField(null=True)
    negative_strand_coords = RegionCoordsField(null=True)
    lo_labels_region = RegionCoordsField(null=True)
    verbose = CharField(max_length=250, null=True)
    bedcover = ForeignKeyField(db_column    = 'bedcover_id',
                               rel_model    = Bedcover,
                               to_field     = 'id',
                               related_name = 'chromosomes',
                               null         = True)
    total_height_pixels = IntegerField(null=True)
    class Meta:
        db_table = 'chromosomes'
    def __init__(self, *args, **kwargs):
        self.bedcover_id = kwargs.pop('bedcover_id', None)
        super(Chromosome, self).__init__(*args, **kwargs)
    def _set_coords(self, cur_height):
        start_img = cur_height
        if self.show:
            half_intron_height = int(self.params.size_intron.height//2)-1
            strands_separation = self.params.size_gene_strip.height+5
            total_height = self.params.size_up_labels_region.height+ \
                           self.params.size_lo_labels_region.height+ \
                           strands_separation+self.params.size_intron.height
            self.title_area = RegionCoords([(0, cur_height),
                                            (self.params.title_col_size.width,
                                             cur_height+total_height)])
            self.graph_area = RegionCoords([self.title_area.upper_right,
                                          (self.title_area.right_x+self.params.boxes_col_size.width,
                                           cur_height+total_height)])
            self.up_labels_region = RegionCoords([self.graph_area.upper_left,
                                                  (self.graph_area.right_x,
                                                   self.graph_area.top+self.params.size_up_labels_region.height)])
            self.strands_region = RegionCoords([self.up_labels_region.lower_left,
                                                (self.graph_area.left_x+int(self.width*self.scale),
                                                 self.up_labels_region.bottom+ \
                                                 strands_separation)])
            self.positive_strand_coords = RegionCoords([(self.strands_region.left,
                                                         self.strands_region.top-half_intron_height),
                                                        (self.strands_region.right,
                                                         self.strands_region.top+half_intron_height)])

            self.negative_strand_coords = RegionCoords([(self.strands_region.left,
                                                         self.strands_region.bottom-half_intron_height),
                                                        (self.strands_region.right,
                                                         self.strands_region.bottom+half_intron_height)])
            self.lo_labels_region = RegionCoords([self.negative_strand_coords.lower_left,
                                                  self.graph_area.lower_right])
            cur_height = self.graph_area.bottom
            self.save()
        for gene in self.genes:
            gene._set_subexons()
            if gene.transcripts.select().count():
                gene._set_scale()
            cur_height = gene._set_coords(cur_height)
        self.total_height_pixels = cur_height-start_img+1
        self.save()
        return cur_height
    @property
    def start(self):
        if self._start is None:
            min_gene = self.genes.select(fn.Min(Gene.start)).scalar()
            max_gene = self.genes.select(fn.Max(Gene.end)).scalar()
            extension = int((max_gene - min_gene+1)*.01)
            self._start = min_gene - extension
            self.save()
        return self._start
    @property
    def end(self):
        if self._end is None:
            min_gene = self.genes.select(fn.Min(Gene.start)).scalar()
            max_gene = self.genes.select(fn.Max(Gene.end)).scalar()
            extension = int((max_gene - min_gene+1)*.01)
            self._end = max_gene+extension
            self.save()
        return self._end
    @property
    def width(self):
        return self.end-self.start+1
    @property
    def scale(self):
        return self.bedcover.scale
    def __draw_title(self, image):
        if self.show:
            draw = self._get_draw(image)
            draw.text(self.title_area.text_at_mid_left(self.params.font_size_title),
                      self.verbose,
                      font = self.params.font_title,
                      fill = self.params.color_font_title)
    def __draw_strands(self, image):
        if self.show:
            draw = self._get_draw(image)
            # background of the region
            #draw.rectangle(self.strands_region,
            #               fill=self.params.color_intron)
            # positive
            ## positive sign on the left
            draw.text((self.positive_strand_coords.left-10,
                       self.positive_strand_coords.top-2),
                      "+",
                      font = self.params.font_label,
                      fill = self.params.color_font_label)
            ## positive sign on the right
            draw.text((self.positive_strand_coords.right+8,
                       self.positive_strand_coords.top-2),
                      "+",
                      font = self.params.font_label,
                      fill = self.params.color_font_label)
            ## the line representing the strand
            draw.rectangle(self.positive_strand_coords,
                           fill=self.params.color_intron)
                           #outline=self.params.color_boxes_outline)
            # negagtive
            ## negative sign on the left
            draw.text((self.negative_strand_coords.left-8,
                       self.negative_strand_coords.bottom-(self.params.font_size_label//2)-2),
                      "-",
                      font = self.params.font_label,
                      fill = self.params.color_font_label)
            ## negative sign on the right
            draw.text((self.negative_strand_coords.right+10,
                       self.negative_strand_coords.bottom-(self.params.font_size_label//2)-2),
                      "-",
                      font = self.params.font_label,
                      fill = self.params.color_font_label)
            ## the line representing the strand
            draw.rectangle(self.negative_strand_coords,
                           fill=self.params.color_intron)
            # negative
#        labels = list()
#            labels.append(gene.label)
#        for label in labels:
#            label.draw_link(image)
#        for label in lables:
#            label.draw(image)
#        raise Exception('NOT IMPLEMENTED - chromosome.__draw_box(image)')
        return image
    def __draw_separator(self, image):
        draw = self._get_draw(image)
        draw.line([(self.title_area.upper_left),(self.graph_area.upper_right)],
                  fill='black')
        draw.line([(self.title_area.left,self.title_area.bottom-1),
                   (self.graph_area.right,self.title_area.bottom-1)],
                  fill='black')
    def draw(self, image):
        if self.show:
            self.__draw_separator(image)
            self.__draw_title(image)
            self.__draw_strands(image)
        for gene in self.genes:
            image = gene.draw(image)
        return image
#        for gene in self.genes.iterators():
#            gene.draw(image)
    def save(self, force_insert=False, only=None):
        self.id = self.id.strip()
        self.verbose = self.verbose or "chr %s" % self.id
        if not self.bedcover:
            self.bedcover_id = self.bedcover_id or 'default'
            self.bedcover = Bedcover.get_or_create(id=self.bedcover_id)[0]
        super(Chromosome, self).save(force_insert=force_insert,only=only)
#    def __draw_title(self):
#        pass
#    def __draw_box(self):
#    def draw(self):
#        self.__draw_title()
#        self.__draw_box()

class Gene(SpleeBaseModel):
    """A Gene"""
    id         = CharField(primary_key = True,
                           max_length  = 150)
    chromosome = ForeignKeyField(db_column    = 'chromosome_id',
                                 rel_model    = Chromosome,
                                 to_field     = 'id',
#                                 null         = True,
                                 related_name = 'genes')
    strand = IntegerField() # 1 for pos, 0 UKN, -1 for neg
    start  = IntegerField()
    end    = IntegerField()

    show_ticks = BooleanField(default=True)
    show_strip = BooleanField(default=False)
    show_legend = BigIntegerField(default=False)
    strip_color = ColorField(null=True)
    title_region = RegionCoordsField(null=True)
    graph_region = RegionCoordsField(null=True)
    strip_coords = RegionCoordsField(null=True)
    legend_region = RegionCoordsField(null=True)

    verbose = CharField(max_length = 150,
                        null       = True)
    scale = FloatField(null=True)
    show_label = BooleanField(default=False)
    label      = ForeignKeyField(db_column    = 'label_id',
                                 rel_model    = Label,
                                 to_field     = 'id',
                                 related_name = 'genes',
                                 null         = True)
    total_height_pixels = IntegerField(null=True)

    class Meta:
        db_table = 'genes'
        order_by = ['start']
    def __init__(self, *args, **kwargs):
        self.chromosome_id = kwargs.pop('chromosome_id', None)
        super(Gene, self).__init__(*args, **kwargs)
    def save(self, force_insert=False, only=None):
        self.id = self.id.strip()
        self.verbose = self.verbose or self.id
        self.strip_color = self.params.color_gene_strip or self.params.colormap.select_color(self.verbose)
        if self.chromosome_id:
            self.chromosome_id = self.chromosome_id.strip()
            self.chromosome = Chromosome.get_or_create(id=self.chromosome_id)[0]
        super(Gene, self).save(force_insert=force_insert, only=only)
    def _set_coords(self, cur_height):
        start_img = cur_height
        if self.show_ticks:
            self.title_region = RegionCoords([(0, cur_height),
                                              (self.params.title_col_size.width,
                                               cur_height+self.params.size_tick_region.height)])
            if self.show_legend:
                pass
            self.graph_region = RegionCoords([self.title_region.upper_right,
                                              (self.title_region.right_x+self.params.boxes_col_size.width,
                                               self.title_region.bottom)])
            cur_height += self.title_region.height
            self.save()
            for subexon in self.subexons.iterator():
                subexon._set_coords(cur_height)
            for transcript in self.transcripts.iterator():
                cur_height = transcript._set_coords(cur_height)
        if self.show_strip and self.chromosome.show:
            strands_coords = { 1:self.chromosome.positive_strand_coords,
                              -1:self.chromosome.negative_strand_coords}
            strand_coords = strands_coords[self.strand]
            left = strand_coords.left+(self.start - self.chromosome.start)*self.chromosome.scale
            right = left+self.width*self.chromosome.scale
            top = strand_coords.vcenter-self.params.size_gene_strip.height//2
            bottom = strand_coords.vcenter+self.params.size_gene_strip.height//2
            self.strip_coords = RegionCoords([(left,top),(right,bottom)])
            # define position in the chromosome box
            pass
        self.total_height_pixels = cur_height - start_img + 1
        self.save()
        if self.transcripts.count():
            return cur_height
        return start_img
    @property
    def exons(self):
        return Exon.select().where(Exon.transcript.in_(self.transcripts))
    def _set_subexons(self):
        for exon in self.exons.iterator():
            try:
                # get the better candidate
                subexons = self.subexons.where((exon.start <= SubExon.end) &
                                               (exon.end >= SubExon.start))
                subexon = subexons.get()
                # check if the exon sit astride two subesons
                if subexons.count() > 1:
                    min_start = subexons.select(fn.Min(SubExon.start)).scalar()
                    max_end = subexons.select(fn.Max(SubExon.end)).scalar()
                    for s in subexons:
                        s.delete_instance()
                    subexon = SubExon.create(gene  = self,
                                             start = min_start,
                                             end   = max_end)
                # adjust its position if needed
                if subexon.end < exon.end:
                    subexon.end = exon.end
                elif subexon.start > exon.start:
                    subexon.start = exon.start
                subexon.save()
                exon.subexon = subexon
            except SubExon.DoesNotExist:
                # No candidate has been found, creating a new one
                exon.subexon = SubExon.create(gene  = self,
                                              start = exon.start,
                                              end   = exon.end)
            exon.save()
    def _set_scale(self):
        subexons_na_cnt = self.subexons.select(fn.Sum(SubExon.end-SubExon.start)).scalar()
        subintrons_px_cnt = self.subexons.count()*self.params.size_intron.width
        self.scale = (self.params.boxes_col_size.width-subintrons_px_cnt)/subexons_na_cnt
        self.save()

    @property
    def width(self):
        return self.end-self.start
    def __draw_title(self, image):
        if self.transcripts.select().count():
            draw = self._get_draw(image)
            dirs = {-1:' (-)',1:' (+)'}
            draw.text(self.title_region.text_at_mid_left(self.params.font_size_title),
                      self.verbose + dirs[self.strand],
                      font = ImageFont.truetype(self.params.font_file_title,
                                                self.params.font_size_title),
                      fill = self.params.color_font_title)
    def __draw_strip(self, image):
        layer = Image.new('RGBA', image.size)
        draw = self._get_draw(layer)
        draw.rectangle(self.strip_coords, fill=self.strip_color.trans(), outline=self.strip_color.opaque)
        return Image.alpha_composite(image,layer)
        #raise Exception('NOT IMPLEMENTED - gene.__draw_strip(image)')
    def __draw_ticks(self, image):
        draw = self._get_draw(image)
    def __draw_backgrounds(self, image):
        draw = self._get_draw(image)
        top = self.title_region.top
        bottom = top+self.title_region.height + sum([t.graph_area.height for t in self.transcripts])
        for subexon in self.subexons:
            left = subexon.coords.left
            right = subexon.coords.right
            draw.rectangle([(left,top),(right,bottom)],
                           fill=self.params.color_bg.darker())
    def __draw_legend(self, image):
        draw = self._get_draw(image)
        raise Exception('NOT IMPLEMENTED - gene.__draw_legend(image)')
    def draw(self, image):
        if self.show_ticks:
            self.__draw_title(image)
            self.__draw_ticks(image)
        if self.show_strip:
            image = self.__draw_strip(image)
            #self.__draw_label(image)
        if self.show_legend:
            self.__draw_legend(image)
        self.__draw_backgrounds(image)
        for transcript in self.transcripts.iterator():
            image = transcript.draw(image)
        return image
    @property
    def children(self):
        return self.subexons.order_by(SubExon.start)

class SubExon(SpleeBaseModel):
    id        = PrimaryKeyField()
    #pos       = IntegerField()
    gene      = ForeignKeyField(db_column    = 'gene_id',
                                rel_model    = Gene,
                                to_field     = 'id',
                                related_name = 'subexons')
    start = BigIntegerField()
    end   = BigIntegerField()
    coords = RegionCoordsField(null=True)
    class Meta:
        db_table = 'subexons'
        order_by = ['start']
    def _set_coords(self, cur_height):
        prev_coords = self.gene.title_region
        if not self.is_first:
            prev_coords = self.gene.subexons.where(SubExon.end < self.start).order_by(SubExon.start.desc()).get().coords
        cur_x = prev_coords.right_x+(not self.is_first)*self.params.size_intron.width
        length = int(self.length*self.gene.scale)
        self.coords = RegionCoords([(cur_x, prev_coords.top),
                                       (cur_x+length, prev_coords.bottom)])
        self.save()

    @property
    def exon_count(self):
        return self.exons.count()
    @property
    def length(self):
        return self.end - self.start + 1
    @property
    def is_first(self):
        return self == self.gene.subexons.first()

class Transcript(SpleeBaseModel):
    id = CharField(db_column   = 'id',
                   primary_key = True,
                   max_length  = 150)
    gene = ForeignKeyField(db_column = 'gene_id', rel_model    = Gene,
                           to_field  = 'id',      related_name = 'transcripts')
    start = BigIntegerField()
    end = BigIntegerField()
    show_label = BooleanField(default=False)
    verbose = CharField(max_length = 150,
                        null       = True)
    title_area = RegionCoordsField(null=True)
    graph_area = RegionCoordsField(null=True)
    up_labels_region = RegionCoordsField(null=True)
    boxes_region = RegionCoordsField(null=True)
    lo_labels_region = RegionCoordsField(null=True)
    label = ForeignKeyField(db_column    = 'label_id',
                             rel_model    = Label,
                             to_field     = 'id',
                             related_name = 'transcripts',
                             null         = True)
    class Meta:
        db_table = 'transcripts'
    def __init__(self, *args, **kwargs):
        self.gene_id = kwargs.pop('gene_id', None)
        super(Transcript, self).__init__(*args, **kwargs)
    def _reckon_label_sizes(self):
        draw = ImageDraw.Draw(Image.new('RGBA', (100,100)))
        label_size = Size(0,0)
        for ftr in self.features.iterator():
            size = draw.textsize(ftr.verbose)
            if label_size[0] < size[0] : label_size = Size(size[0],label_size[1])
            if label_size[1] < size[1] : label_size = Size(label_size[0],size[1])
        return label_size.grow_by(1)
    def _set_coords(self, cur_height):
        ftr_levels = self._ftr_levels()
        exn_height = max((len(ftr_levels)+1)*(self.params.size_feature.height+2),
                         self.params.height_min_exon.height)+self.params.size_intron.height
        label_size = self._reckon_label_sizes()
        total_height = self.params.lbls_regions_height + exn_height

        self.title_area = RegionCoords([(0, cur_height),
                                        (self.params.title_col_size.width,
                                         cur_height+total_height)])
        self.graph_area = RegionCoords([(self.title_area.right_x, cur_height),
                                        (self.title_area.right_x+self.params.boxes_col_size.width,
                                         cur_height+total_height)])
        self.up_labels_region = RegionCoords([self.graph_area.upper_left,
                                              (self.graph_area.right_x,
                                               cur_height+self.params.size_up_labels_region.height)])
        self.boxes_region = RegionCoords([self.up_labels_region.lower_left,
                                          (self.graph_area.right_x,
                                           self.up_labels_region.bottom+exn_height)])
        self.lo_labels_region = RegionCoords([self.boxes_region.lower_left,
                                                    self.graph_area.lower_right])
        self.save()
        for exon in self.exons.iterator():
            exon._set_coords(cur_height)

        regions_matrix = [RegionMatrix(label_size = label_size,
                                       region_coord = self.up_labels_region,
                                       region_pos = 'upper'),
                          RegionMatrix(label_size = label_size,
                                       region_coord = self.lo_labels_region,
                                       region_pos = 'lower')]
        box_lims = self.boxes_region.top_bottom_limits
        # Features
        level_indexes = range((len(ftr_levels)-1)//2,-(len(ftr_levels)+1)//2, -1)
        for i,ftrs_line in zip(level_indexes, ftr_levels):
            pos = i+(i<0)
            gap = ((i-pos) or 1)
            strip_lims = list()
            strip_lims.append((box_lims[i<0]+gap*2)+pos*(self.params.size_feature.height+gap))
            strip_lims.append(strip_lims[0] + (self.params.size_feature.height-1)*gap)
            strip_top, strip_bottom = sorted(strip_lims)
            region_matrix = regions_matrix[i<0]
            for feature in ftrs_line:
                feature._set_coords(strip_top, strip_bottom, region_matrix)
        return cur_height + total_height
    def __draw_title(self, image):
        draw = self._get_draw(image)
        draw.text(self.title_area.text_at_mid_left(self.params.font_size_title),
                  self.verbose,
                  font = ImageFont.truetype(self.params.font_file_title,
                                            self.params.font_size_title),
                  fill = self.params.color_font_title)
    def __draw_introns_line(self, image):
        draw = self._get_draw(image)
        left_x, vcenter = self.boxes_region.left_center
        if self.first_exon:
            left_x, vcenter = self.first_exon.coords.left_center
        right_x = self.boxes_region.right_x - 10
        if self.last_exon:
            right_x = self.last_exon.coords.right_x
        top = vcenter - self.params.size_intron.height//2
        bottom = top + self.params.size_intron.height
        coords = RegionCoords([(left_x,top),(right_x,bottom)])
        draw.rectangle(coords, fill=self.params.color_intron)
    def __draw_boxes_region(self, image):
        self.__draw_introns_line(image)
        for exon in self.exons.iterator():
            image = exon.draw(image)
        return image
    def __draw_features(self, image):
        #Label.draw_links(image)
        layer = Image.new('RGBA', image.size, (0,0,0,0))
        for feature in self.features.iterator():
            feature.draw(layer)
        return Image.alpha_composite(image,layer)
    def draw(self, image):
        self.__draw_title(image)
        image = self.__draw_boxes_region(image)
        return self.__draw_features(image)
    def _ftr_levels(self):
        features = sorted(self.features, key=lambda ftr: ftr.length)
        levels = list()
        while len(features) > 0:
            ftr_to_place = features.pop()
            done = False
            for level in levels:
                overlap = False
                for ftr in level:
                    if ftr.start <= ftr_to_place.start <= ftr.end or \
                       ftr.start <= ftr_to_place.end   <= ftr.end or \
                       ftr_to_place.start <= ftr.start <= ftr_to_place.end or \
                       ftr_to_place.start <= ftr.end <= ftr_to_place.end:
                        overlap = True
                        break
                if overlap is False:
                    level.append(ftr_to_place)
                    done = True
                    break
            if done is False:
                level = [ftr_to_place]
                levels.append(level)
        return levels

    @property
    def children(self):
        return self.exons
    @property
    def is_cdng(self):
        return any([i.is_cdng for i in self.children])
    @property
    def first_exon(self):
        return self.exons.first()
    @property
    def last_exon(self):
        if self.exons.count():
            return self.exons[self.exons.count()-1]
        return None
    def save(self, force_insert=False, only=None):
        self.id = self.id.strip()
        self.verbose = self.verbose or self.id
        if self.gene_id is not None:
            self.gene = Gene.get_or_create(id       = self.gene_id.strip(),
                                           defaults = {'chromosome':'UKN',
                                                       'strand'    :0,
                                                       'start' :-1,
                                                       'end'   :-1})[0]
        super(Transcript, self).save(force_insert=force_insert,only=only)
        pass

class Exon(SpleeBaseModel):
    id      = CharField(max_length=150)
    #rank    = IntegerField(null=True) # For exon, the position in the transcript, depend on the strand
    #pos     = IntegerField(null=True)
    start   = IntegerField()
    end     = IntegerField()
    cdstart = IntegerField(null=True)
    cdend   = IntegerField(null=True)
    subexon = ForeignKeyField(db_column    = 'subexon_id',
                              rel_model    = SubExon,
                              to_field     = 'id',
                              related_name = 'exons',
                              null         = True)
    transcript  = ForeignKeyField(db_column    = 'transcript_id',
                                  rel_model    = Transcript,
                                  to_field     = 'id',
                                  related_name = 'exons')
    coords = RegionCoordsField(null=True)
    cdcoords = RegionCoordsField(null=True)
#    img_start   = IntegerField(default=0)
#    img_end     = IntegerField(default=0)
#    img_cdstart = IntegerField(default=0)
#    img_cdend   = IntegerField(default=0)
#    intron_color    = (125,125,125,255)
#
#    inner_color     = (255,255,255,255) # pure 'white'
#    outter_color    = (0,0,0,255) # pure 'black'
##    inner_coding_color  = (41,155,216,128)
#    inner_coding_color  = (131,210,252,128)
#    outter_coding_color = (0,0,200,255)
    show_label = BooleanField(default = False)
    verbose = CharField(max_length = 150,
                        null       = True)
    label    = ForeignKeyField(db_column    = 'label_id',
                               rel_model    = Label,
                               to_field     = 'id',
                               related_name = 'exons',
                               null         = True)
    class Meta:
        db_table = 'exons'
        primary_key = CompositeKey('id', 'transcript')
        order_by = ['start']
    def _set_coords(self, cur_height):
#        scale = transcript.gene.scale
#        length = int(exon.length*scale)
#        offset = int((exon.start - exon.subexon.start)*scale)
#        bgn = exon.subexon.coords.left_x + offset
#        exon.coords = RegionCoords([(self.start_px, self.transcript.boxes_region.top),
#                                    (bgn +length,
#                                     transcript.boxes_region.bottom)])
        ref_px = self.subexon.coords.left_x
        top = self.transcript.boxes_region.top
        bottom = self.transcript.boxes_region.bottom
        start_px = ref_px + int((self.start - self.subexon.start)*self.scale)
        end_px = start_px + int(self.length*self.scale)

        cdstart_px = cdend_px = None
        if self.is_cdng:
            cdstart_px = start_px+int((self.cdstart-self.start)*self.scale)
            cdend_px = cdstart_px+int(self.cdlength*self.scale)

        self.coords = [(start_px,top),(end_px,bottom)]
        self.cdcoords = [(cdstart_px,top),(cdend_px,bottom)]
        self.save()
    def _get_region_cdcoords(self):
        if self.is_cdng:
            return RegionCoords([(self._cdstart_px(),self._top_px()),
                                 (self._cdend_px(),self._bottom_px())])
        else:
            return None
    def __draw_box(self, image):
        draw = self._get_draw(image)
        draw.rectangle(self.coords,
                       fill = self.params.color_boxes_fill,
                       outline = self.params.color_boxes_outline)
    def __draw_coding(self, image):
        if self.is_cdng:
            layer = Image.new('RGBA', image.size, (0,0,0,0))
            draw = self._get_draw(layer)
            draw.rectangle(self.cdcoords,
                           fill = self.params.color_coding_fill)
            return Image.alpha_composite(image,layer)
        return image
    def draw(self, image):
        self.__draw_box(image)
        return self.__draw_coding(image)
    @property
    def length(self):
        return self.end - self.start
    @property
    def offset(self):
        return self.start - self.subexon.start
    @property
    def cdoffset(self):
        return self.cdstart - self.subexon.start
    @property
    def cdlength(self):
        if None not in (self.cdend,self.cdstart):
            return self.cdend - self.cdstart
        else:
            return 0
    @property
    def is_cdng(self):
        return self.cdlength > 0
    @property
    def is_first(self):
        return self.rank == 1
    @property
    def gene(self):
        return self.transcript.gene
    @property
    def scale(self):
        return self.transcript.gene.scale
    def __init__(self, *args, **kwargs):
        self.transcript_id = kwargs.pop('transcript_id', None)
        super(Exon, self).__init__(*args, **kwargs)
    def save(self, force_insert=False, only=None):
        self.id = self.id.strip()
        self.verbose = self.verbose or self.id
        self.start = self.start or None
        self.end = self.end or None
        self.cdstart = self.cdstart or None
        self.cdend = self.cdend or None
        if self.transcript_id is not None:
            self.transcript, is_created = \
                    Transcript.get_or_create(id=self.transcript_id.strip(),
                                             defaults={'start':-1,
                                                       'end'  :-1})
        super(Exon, self).save(force_insert=force_insert,only=only)

class Feature(SpleeBaseModel):
    id = CharField(max_length=150)
    type = CharField(max_length=50)
    color      = ColorField(null=True)
    outline_color = ColorField(null=True) #if None then auto
    transcript = ForeignKeyField(db_column='transcript_id', rel_model=Transcript,
                           to_field='id', related_name='features')
    start  = BigIntegerField()
    end    = BigIntegerField()
    start_exn  = ForeignKeyField(db_column='start_exn_id', rel_model=Exon,
                                 to_field='id', related_name='features_starter',
                                 null=True)
    end_exn  = ForeignKeyField(db_column='end_exn_id', rel_model=Exon,
                               to_field='id', related_name='features_ender',
                               null=True)
    show_label = BooleanField(default=True)
    verbose = CharField(max_length = 150,
                        null       = True)
    coords = RegionCoordsField(null=True)
    label    = ForeignKeyField(db_column    = 'label_id',
                               rel_model    = Label,
                               to_field     = 'id',
                               related_name = 'features',
                               null         = True)
    coords = RegionCoordsField(null = True)
    class Meta:
        db_table = 'features'
        primary_key = CompositeKey('id','start','end','transcript')
    def __init__(self, *args, **kwargs):
        self.transcript_id = kwargs.pop('transcript_id',None)
        super(Feature, self).__init__(*args,**kwargs)
    def save(self, force_insert=False, only=None):
        self.id = self.id.strip()
        self.verbose = self.verbose or self.id
        self.color = self.color or self.params.colormap.select_color(self.type)
        if self.transcript_id is not None:
            self.transcript, is_created = \
                    Transcript.get_or_create(id=self.transcript_id.strip(),
                                             defaults={'start':-1,
                                                       'end'  :-1})
        super(Feature, self).save(force_insert=force_insert, only=only)
    def _set_start_end_exons(self):
        self.start_exn = self.transcript.exons.where((Exon.start <= self.start) &
                                                (Exon.end >= self.start)).get()
        self.end_exn = self.transcript.exons.where((Exon.start <= self.end) &
                                              (Exon.end >= self.end)).get()
        self.save()
    def _set_coords(self, top, bottom, region_matrix):
        self._set_start_end_exons()
        left_x = int(self.start_exn.coords.left_x +
                     (self.start-self.start_exn.start)*self.scale)
        right_x = int(self.end_exn.coords.left_x +
                      (self.end-self.end_exn.start)*self.scale)
        self.coords = RegionCoords([(left_x, top), (right_x, bottom)])
        self.outline_color = self.outline_color or self.params.colormap.select_color(self.id)


        label_coords = region_matrix.free_cell_coord_close_to(self.coords.hcenter)
        label_anchor = label_coords.bottom_center
        link_anchor = self.coords.upper_center
        if region_matrix.region_pos == 'lower':
            link_anchor = self.coords.bottom_center
            label_anchor = label_coords.upper_center

        self.label = Label.create(coords        =label_coords,
                                 region_coords  = region_matrix.coords,
                                 link           = sorted([link_anchor, label_anchor]),
                                 line_thickness = self.params.line_thickness,
                                 #fill_color     = self.color,
                                  #fill_color = '#FFFFFF',
                                 # fill_color = Color(255,255,255,0),
                                  fill_color = self.params.colormap.select_color(self.id),
                               outline_color  = self.outline_color,
                                 font_color     = self.params.color_font_label,
                                 font_size      = self.params.font_size_label,
                                 font_filepath  = self.params.font_file_label,
                                 display_text   = self.verbose)
        self.save()

    @property
    def scale(self):
        return self.transcript.gene.scale
    def draw(self, image):
        layer = Image.new('RGBA',image.size)
        draw = self._get_draw(image)
        draw.rectangle(self.coords,
                       #fill    = self.color.trans(),
                       #fill     = '#FFFFFF',
                       fill = Color(0,0,0,0),
                       outline = self.outline_color)
        self.label.draw(image)
        return Image.alpha_composite(image, layer)
    @property
    def length(self):
        return self.end - self.start
