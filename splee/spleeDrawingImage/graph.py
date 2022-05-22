from __future__ import division
from .models import *
from PIL import ImageFilter

# GFF3 format
# - seqid(number of the line)
# - source_prgrm
# - type(transcript,gene,exon)
# - start
# - end
# - score
# - strand
# - phase(for CDS only, "not used here")
# - attributes(see below)
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

class Graph(object):
    """The base class to interact with splee.

    It's basically the view which receive the data and pass them to the models.
    Afterward it'll use them to produce the image on a call to te ``graph()``
    function.

    Attributes:
        image_width (int): with of the image to produce.
    """
    __models = [Gene,    Chromosome, Bedcover,   Label,
                SubExon, Exon,    Transcript, Feature]
    _DEBUG = False
    def __init__(self, filename=None):
        """Initiate a new Graph object with base parameters.

        Args:
            filename (Optional[str]): A filename to output the result.
            image_width (int): The width of the image
                               (height is generated on the fly)
        """
        self.filename=filename
        self.params = Params()
        self.__init_database()
        SpleeBaseModel.params = self.params
    def __del__(self):
        self.__close_database()
    def __init_database(self):
        """Don't touch this"""
        SpleeBaseModel._meta.database.connect()
        SpleeBaseModel._meta.database.drop_tables(self.__models, safe=True)
        SpleeBaseModel._meta.database.create_tables(self.__models)
    def __close_database(self):
        """Don't touch this"""
        SpleeBaseModel._meta.database.close()
    def add_chromosome(self, id, start, end, show=True, verbose=None):
        """Add a new chromosome into the database or a slice of it

        Args:
            id      (str): A unique id for the chromosome
            start   (int): Start position for the slice of the chromosome
            end     (int): End position for the slice of the chromosome
            show   (bool): Weather to show it or not
                             -: default = True
            verbose (str): The text to display
                             -: default = id
        """
        return Chromosome.update_or_create(id      = id,
                                           _start  = start,
                                           _end    = end,
                                           show    = show,
                                           verbose = verbose)
    def add_gene(self, id, chromosome_id, strand_s, start, end,
                       verbose=None, show_label=False, show_strip=False):
        """Add a new gene into the database

        Args:
            id         (str): A unique id for the gene
            chromosome (str): The name of the chromosome
            strand_s     (str): + for positive strand, otherwise it's negative
            start  (int): Start position in the chromosome
            end    (int): End position in the chromosome
        """
        if strand_s=="+":
            strand=1
        else:
            strand=-1
        return Gene.update_or_create(id            = id,
                                     chromosome_id = chromosome_id,
                                     strand        = strand,
                                     start         = start,
                                     end           = end,
                                     verbose       = verbose,
                                     show_label    = show_label,
                                     show_strip    = show_strip)
    def add_transcript(self, id, gene_id, start, end):
        """Add a new transcript into the database

        Args:
            id        (str): A unique id for the gene
            gene_id   (str): The id of the gene in which the transcript is
                             within
            start (int): Start position in the chromosome
            end   (int): End position in the chromosome
        """
        #with Using(self.database, self.__models):
        return Transcript.update_or_create(id=id, gene_id=gene_id,
                                           start=start,
                                           end=end)
    def add_exon(self, id, transcript_id, start, end, cdstart=None,
                       cdend=None, verbose=None, show_label=False):
        """Add a new exon into the database

        Args:
            id            (str): (*) A name for the exon.
            transcript_id (str): (*) The id of the transcript parent.
            start         (int): Chromosomal start position.
            end           (int): Chromosomal end position.
            cdstart       (int): Chromosomal start position of the coding
                                 region.
                                   -: optional
            cdend         (int): Chromosomal end position of the coding region.
                                   -: optional
            verbose       (str): Verbose text to display on the label.
                                   -: default = id
            show_label   (bool): Whether to display or not the label.
                                   -: default = False

                * : 'id' and 'transcript_id' are unique together
        """
        #with Using(self.database, self.__models):
        return Exon.update_or_create(id            = id,
                                     type          = 'exon',
                                     transcript_id = transcript_id,
                                     start         = start,
                                     end           = end,
                                     cdstart       = cdstart,
                                     cdend         = cdend)
    def add_feature(self, id, transcript_id, start, end, greydegree=0,
                          outline=None, verbose=None, show_label=True):
        """Add a new feature into the database

        Args:
            id            (str): (*) A name for the feature
            type          (str): A string of your choice to identify the type
                                 of feature.
            transcript_id (int): (*) The id of the parent transcript.
            start         (int): (*) Start position in the chromosome
            end           (int): (*) End position in the chromosome
            greydegree        (float): a float between 0 and 1 showing conservation; 0=white=not conserved; 1=black=highly conserved
            outline     (color): (**) The outline color for this feature, the
                                 same color will be used for the label outline
                                 and the link.
                                   -: default = None (automatic based on id)
            verbose       (str): Verbose text to display on the label.
                                   -: default = id
            show_label   (bool): Whether to display or not the label.
                                   -: default = True

                * : 'id','start','end' and 'transcript' are unique together
               ** : The color can be a tuple or a string depending on your
                    need.  If the color is 'RGBA' then a tuple of the form
                    '(R,G,B,A)', else if it's 'RGB, then it could be a tuple of
                    the form '(R,G,B)' or a string with the hexadecimal value
                    with the format '#ffBB33'.
        """
        #with Using(self.database, self.__models):
        import colorsys
        color=colorsys.hsv_to_rgb(0,0,greydegree)
        return Feature.update_or_create(id=id, type="domain", color=color,
                                        outline_color = outline,
                                        transcript_id=transcript_id,
                                        start=start, end=end,
                                        verbose=verbose)
    def draw(self, filename=None):
        """Draw the image, save it into a file if a filename is provided.

        Draw the image following the model below and return a copy of it.
        +----------------+----------------------------------------------------+
        |   title_area   |                    graph_area                      |
        +----------------+----------------------------------------------------+
        |                |                 up_labels_region                   |
        +                +----------------------------------------------------+
        |  title_region  |                    boxes_region                    |
        +                +----------------------------------------------------+
        |                |                  lo_labels_region                  |
        +----------------+----------------------------------------------------+

        Args:
            filename (str): The path to a file for saving the image. Override
                            the one sat at the init phase.
                              -: optional
        """
        filename = filename or self.filename
        image = Bedcover._draw_all()
        if filename:
            image.save(filename)
        image_copy = image.copy()
        image.close()
        return image_copy
