from splee.graph import Graph


class testdata(object):

    g = Graph()

    g.add_gene('yolo','5','-1','141653401','141682221')





    g.add_transcript('ENST00000513878','yolo',141653791,141673160)
    g.add_transcript('ENST00000524066','yolo',141672768, 141673387)

    g.add_transcript('ENST00000513872','yolo','141653791','141673160')
    #g.add_transcript('ENST00000524063','yolo','141672768', '141673387')

    g.add_exon('ENSE00002051288', 'ENST00000513878', '141673013', '141673160')
    g.add_exon('ENSE00001086053', 'ENST00000513878', '141672741', '141672925', '141672741', '141672925')









    #g.add_exon('ENSE00002051288','ENST00000524066','141673013','141673160','141673013','141673091')

    g.draw('test_gene.png')