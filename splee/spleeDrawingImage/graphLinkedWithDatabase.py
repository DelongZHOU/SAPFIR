import os
import pandas as pd
from django.conf import settings

# Use local db intead of fetching from remote db to improve responsive delay
# Gene, transcript, exon and domain tables are under root/utility/$specie/

BASE_DIR=settings.BASE_DIR


class DataGene: #Rename this when ready for online
	def __init__(self):
		self.genes = pd.read_csv(os.path.join(BASE_DIR,'utility','gene.tsv'),
						sep='\t',header=0)

		self.transcripts = pd.read_csv(os.path.join(BASE_DIR,'utility','transcript.tsv'),
						sep='\t',header=0)

		self.exons = pd.read_csv(os.path.join(BASE_DIR,'utility','exon.tsv'),
						sep='\t',header=0)
		self.exons["exon_id"]=self.exons["transcript_id"]+"."+self.exons["exon_number"]

		self.domains = pd.pd.read_csv(os.path.join(BASE_DIR,'utility','domain.tsv'),
						sep='\t',header=0)

	def get_Genes_Table(self,gene):
		gene = self.genes.loc[self.genes["gene_id"] == gene]
		return gene

	def get_Genes_Table_With_HGNC(self,hgnc):
		gene = self.genes.loc[self.gene["gene_name"] == hgnc]
		return gene


	def show_All_Transcripts_For_A_Gene(self, gene):
		result = self.transcripts.loc[self.transcripts["gene_id"] == gene]
		return result

	def show_Every_Exons_For_Each_Transcript(self,transcript):
		exons = self.exons.loc[self.exons["transcript_id"]==transcript]
		return exons

	def show_Every_Domains_For_Each_Transcript(self,transcript):
		domains = self.domains.loc[self.domains["transcript_id"]==transcript]
		return domains
		


