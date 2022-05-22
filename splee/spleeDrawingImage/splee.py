import os
import re
import pandas as pd
import sqlite3 as sql

from django.conf import settings

from .graph import Graph
#from .graphLinkedWithDatabase import DataGene


BASE_DIR=settings.BASE_DIR

############################
# lines of 

#cmd = $query_string
#query=conn.execute(cmd)
#columns=[]
#table=pd.DataFrame.from_records(query,columns=columns)

#can be replaced by

#table=pd.read_sql(cmd,conn)

#which adds the column names by default

############################



class Splee:
	def __init__(self, name,species,tools,ratio=0.50):
		self.name = name
		self.species = species
		self.tools = tools
		#transform tool from a list to a string in form of 'tool1','tool2',... with '' surrounding each item.
		#this transformation is needed to pass the list to the sqlite3 query
		self.tool_string=','.join(map(lambda x : "\'{}\'".format(x), tools))
		self.ratio=ratio
		self.strand=''
		print(self.tools)
		print(self.tool_string)

	def images(self):
		'''
		Uses the Graph class to generate the image displaying the gene structure and predicted domains
		'''	
		graph = Graph()

		conn = sql.connect(os.path.join(BASE_DIR,'utility',self.species+'.db'))
		#get gene info
		cmd="SELECT gene_id, chromosome, strand, start, end from gene where {} = '{}' COLLATE NOCASE"
		# working with Ensembl ID
		if re.search('^ENS(MUS)?G[0-9]{11}$',self.name):
			#get gene info
			gene_query = conn.execute(cmd.format("gene_id",self.name))
		# working with gene symbol
		else:
			gene_query = conn.execute(cmd.format("gene_name",self.name))
		try:
			gene_table = pd.DataFrame.from_records(data = gene_query.fetchall(), 
								columns = ["gene_id","chromosome","strand","start","end"])
			gene_id=gene_table.iloc[0]['gene_id']
			chromosome=gene_table.iloc[0]['chromosome']
			self.strand=gene_table.iloc[0]['strand']
		except:
			raise("Gene not found.")
		print(gene_id,self.strand)	
		#add gene info to Graph object
		for line in gene_table.to_numpy().tolist():
			graph.add_gene(*line)
		#get transcript info
		transcript_query = conn.execute("SELECT transcript_id, gene_id, start, end, cds_length, cds_start, cds_end, APPRIS from transcript where gene_id = '{}'".format(gene_id))
		transcripts_table = pd.DataFrame.from_records(data = transcript_query.fetchall(),
								columns=["transcript_id",
									"gene_id",
									"start", "end",
									"cds_length",
									"cds_start","cds_end",
                                                                        "APPRIS"])
		#n_transcript= len(transcripts_table.groupby(by=["transcript_id"]))
		#mark major isoform according to APPRIS
		major={}
		for index, row in transcripts_table.iterrows():
			if row['APPRIS']=='PRINCIPAL:1':
				major[row['transcript_id']]=row['transcript_id']+'*'
			elif row['APPRIS']=='MINOR':
				pass
			else: #principal 2-5 or alternative
				major[row['transcript_id']]=row['transcript_id']+'**'


		print(transcripts_table)
		#add transcript to Graph object
		for line in transcripts_table[["transcript_id","gene_id","start","end"]].to_numpy().tolist():
			graph.add_transcript(*line) #transcript_id, gene_id, start, end
		print("get exons")
		for index, row in transcripts_table.iterrows():
			ENST_ID = row["transcript_id"]
			exon_query = conn.execute("Select exon_number, transcript_id, exon_start, exon_end, cds_start, cds_end from exon where transcript_id = '{}'".format(ENST_ID))
			exons_table = pd.DataFrame.from_records(data=exon_query.fetchall(),
								columns=["exon_number",
									"transcript_id",
									"exon_start", "exon_end",
									"cds_start", "cds_end"])
			exons_table['exon_id']=exons_table.apply(lambda row: '{}.{}'.format(row['transcript_id'],row['exon_number']), axis=1)
			exons_table=exons_table[["exon_id","transcript_id","exon_start","exon_end","cds_start","cds_end"]]
			exons_table.fillna(0,inplace=True)
			exons_table.sort_values("exon_start",ascending=True,inplace=True)
			#add exons to the Graph object
			for line in exons_table.to_numpy().tolist():
				try:
					graph.add_exon(*line) #exon_id, transcript_id, start, end, cdstart=None, cdend=None
				except:
					print(line)
			#print(exons_table)
		print("getting domains")
		#get domains
		#conservation information is dropped because duplication for unknown reason in mouse db (potentially also in human db)
		for i,(index, row) in enumerate(transcripts_table.iterrows()):
			ENST_ID = row["transcript_id"]
			cmd="Select InterPro_acc, transcript_id, start, end, InterPro_des, tool, signature from domain where transcript_id = '{}' and tool in ({})".format(ENST_ID,self.tool_string)
			#print(cmd)
			domain_query = conn.execute(cmd)
			domains_table = pd.DataFrame.from_records(data=domain_query.fetchall(),
								columns=["InterPro Accession","Transcript ID","Start","End","InterPro Description",'Tool','Signature'])
			domains_table.drop_duplicates(inplace=True)
			domains_table['Signature2']=''
			domains_table['Signature2']=domains_table.apply(lambda row: row['InterPro Accession'] if row['InterPro Accession'].startswith('IPR') else row['Signature'], axis=1)
			print(domains_table)
			if i == 0: #initiate new domain table
				all_domains=domains_table.copy(deep=True)
			else:
				all_domains=pd.concat([all_domains,domains_table])
			for line in domains_table[["Signature2","Transcript ID","Start","End"]].to_numpy().tolist():
				print(line)
				try:
					graph.add_feature(*line) #id, transcript_id, start, end, fill==conservation
				except:
					print(all_domains)
					print(line)
					return
		print(all_domains)
		print("calculating alternative / constitutive info")
		#Check for domain overlapping
		#Overlapping domains of same ipro_acc or signature are considered as the same domain. 
		all_domains.sort_values(["Signature2", "Start"], ascending=[True, True], inplace=True)
		all_domains['special_id'] =1
		all_domains.reset_index(drop=True, inplace=True)
		row=0
		domain_id=1
		while row < len(all_domains) - 1:
			if all_domains.iloc[row]["Signature2"] == all_domains.iloc[row+1]["Signature2"]: 
				#since the table is already sorted by start, only need to compare the i,end vs i+1,bgn
				#in fact it's better to track the max(end) and compare to the next bgn
				if all_domains.iloc[row]['End'] < all_domains.iloc[row+1]['Start']:
					domain_id+=1
			else: #different domain type
				domain_id+=1
			all_domains.at[row + 1,'special_id'] = domain_id
			row+=1
		#Need to renameename special Id
		all_domains.sort_values(["InterPro Accession", "Transcript ID"], ascending=[True, True], inplace=True)
		print("special_id done")
		all_domains["Chromosome"]= chromosome
		all_domains=all_domains[["Tool","Signature","InterPro Accession","InterPro Description","Transcript ID","Chromosome","Start","End","special_id"]]
		domains_table_prepare=all_domains[["Tool","Signature","InterPro Accession","InterPro Description","Transcript ID","Chromosome","Start","End"]].copy()
		domains_table_prepare['Transcript ID']=domains_table_prepare.apply(lambda row: major[row['Transcript ID']] if row['Transcript ID'] in major else row['Transcript ID'],axis=1)
		self.domains_table=domains_table_prepare.copy()
		print(all_domains)
		#Group domains by similar transcript and domain
		special_id_group = all_domains[["Tool","Signature","InterPro Accession","InterPro Description", "special_id"]].drop_duplicates()
		print(special_id_group)
		print("calculate by coding")
		special_id_group['Coding'] = ''
		def as_by_coding(special_id,transcript_table,domain_table):
			contain_transcripts=domain_table.loc[domain_table['special_id']==special_id ]["Transcript ID"].tolist()
			candidate_transcripts=transcript_table.loc[transcript_table['cds_length']>0]["transcript_id"].tolist()
			for candidate in candidate_transcripts:
				if candidate in contain_transcripts:
					pass
				else:
					return "Alternative"
			return "Constitutive"
		for index, row in special_id_group.iterrows():
			special_id_group.at[index,'Coding']=as_by_coding(row["special_id"],transcripts_table,all_domains)
		#print(special_id_group)
		print("calculate by cds length ratio")
		special_id_group['CDS Length Ratio'] = ''
		def as_by_length(special_id,transcript_table,domain_table,ratio=0.50):
			contain_transcripts=domain_table.loc[domain_table['special_id']==special_id]["Transcript ID"].tolist()
			max_cds=max(transcript_table["cds_length"].tolist())
			candidate_transcripts=transcript_table.loc[transcript_table['cds_length']>(max_cds*ratio)]["transcript_id"].tolist()
			for candidate in candidate_transcripts:
				if candidate in contain_transcripts:
					pass
				else:
					return "Alternative"
			return "Constitutive"
		for index, row in special_id_group.iterrows():
			special_id_group.at[index,'CDS Length Ratio']=as_by_length(row["special_id"],transcripts_table,all_domains,self.ratio)
		#print(special_id_group)
		print("calculate by overlap cds")
		special_id_group['Overlap CDS'] = ''
		def as_by_cds(special_id,transcript_table,domain_table):
			contain_transcripts=domain_table.loc[domain_table['special_id']==special_id]["Transcript ID"].tolist()
			left=min(all_domains.loc[all_domains['special_id']==special_id]["Start"].tolist())
			right=max(all_domains.loc[all_domains['special_id']==special_id]["End"].tolist())
			print(left,right)
			candidate_transcripts=transcript_table.loc[(transcript_table['cds_start']<=left) & (transcript_table['cds_end']>=right)]["transcript_id"].tolist()
			print(candidate_transcripts)
			for candidate in candidate_transcripts:
				if candidate in contain_transcripts:
					pass
				else:
					return "Alternative"
			return "Constitutive"
		for index, row in special_id_group.iterrows():
			special_id_group.at[index,'Overlap CDS']=as_by_cds(row["special_id"],transcripts_table,all_domains)
		print(special_id_group)
		self.allPresentProt = special_id_group[["Tool","Signature","InterPro Accession", 'InterPro Description','Coding','CDS Length Ratio','Overlap CDS']].copy()
		return graph.draw() 			
