Note: This pipeline is patched overtime to include new information in tables and save utility files from database after merging. At least this should reproduce the database files in production.
It would be best to steamline the process in a more systematic way.


1. Download latest gtf and peptide fasta from Ensembl, e.g. (current version human GRCh38 release 106, mouse GRCm39 release 106)
	Homo_sapiens.GRCh38.106.chr_patch_hapl_scaff.gtf
	Homo_sapiens.GRCh38.pep.all.fa.gz 
	
2. Use the following command to remove * from the fasta file:
	sed -i 's/\*//g' pep.fa 
Use the following command to generate individual fasta files from the peptide file. Each individual fasta file contains 1000 entries.
	awk 'BEGIN {n_seq=0;} /^>/ {if(n_seq%1000==0){file=sprintf("/path/to/fold/hsa.38.%03d.fa",n_seq/1000);} print >> file; n_seq++; next;} { print >> file; }' < pep.fa
3. Upload the individual fasta files and interproscan_array.sh (adaptation required) to a culster; use the .sh file to produce interproscan predictions (current interproscan version 5.51-85)
4. Use scripts in gtf_to_db.txt to produce gene, transcript, exon tables, then map cds position to exon table with scripts in the same file. Produces {}.gene, .transcript, .exon, .cds, .exon_cds, .exon_cds_pos
5. Process exon table and interproscan using scripts process_interpro and process_exon from process.txt
6. Use bedtools to sort and map interproscan and exon table.
	For mapBed use the following options:
		mapBed \
		-a <interpro.processed.sorted> \
		-b <exon.processed.sorted> \
		-c 2,3,4,5,6,7 \
		-o collapse,collapse,distinct,collapse,collapse,distinct
	which will produce .domain.exon file with additional columns as :
		start_in_cds, end_in_cds, chromosome, genome start, genome end, strand
7. Use scripts domain_exon in process.txt to produce 
	(a) domain table file that contains domain prediction and corresponding genomic position
8. Combine the gene, transcript, exon and domain tables into a database and ($species)_domain.tsv files
9. Use the following command to replace "," to ";" in Interpro Descriptions for the .tsv files. Bedtools uses "," as separator for multiple mapped features which causes conflicts with the "," in description.
	sed -i 's/,/;/g' ()_domain.tsv
