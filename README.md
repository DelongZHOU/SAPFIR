# SAPFIR: Sherbrooke Alternative Protein Feature IdentificatoR


## Preface

Sherbrooke Alternative Protein Feature IdentificatoR (SAPFIR) seeks to understand how alternative splicing, transcription initiation and termination change the localization or function of a gene by regulating which localization signals, functional features and other important protein features are present in the mature mRNA. 
This repository accompanies the paper titled "SAPFIR: A webserver for the identification of alternative protein features" published in BMC Bioinformatics DOI: [10.1186/s12859-022-04804-w](https://doi.org/10.1186/s12859-022-04804-w).

SAPFIR has two main functions.

The first function is to:
- annotate, in individual genes, protein features such as functional domains or localization signals
- identify which ones of these features are only present in some of its transcripts (alternative), and
- plot these prtein features in relation to exons.

This allows visualization for how alternative splicing, among other mechanisms, changes what protein features are present in the final product.

The second function is to identify protein features in a list of genome regions, as an attempt to provide functional analysis for differential splicing analysis.

## Getting started

[Our website](https://bioinfo-scottgroup.med.usherbrooke.ca/sapfir/home/) has precompiled database for human and mouse annotation. The following instruction would help to reproduce our database as well as create database for other species with annotated genomes.

### Dependency

SAPFIR webserver is built with Python 3.9.5 and Django 3.2.3 and requires the following python packages which can be installed with 

> pip install *package_name*

- Django==3.2.3
- numpy==1.21.0
- pandas==1.2.5
- Pillow==8.2.0
- pybedtools==0.8.2
- pysam==0.16.0.1
- scipy==1.7.0

In addition Bedtools is needed for pybedtools installation.

In case of problem, try:

> sudo apt-get install gcc libpq-dev -y

> sudo apt-get install python-dev  python-pip -y

> sudo apt-get install python3-dev python3-pip python3-venv python3-wheel -y

> pip3 install wheel


### Installing

- Clone the git repository to your prefered location.
- Follow the steps under database/scripts to produce the *species*.db and *species*_domain.tsv files, which should be put into /root/utility
- In splee/views.py modify the SpeciesForm to include the correct species
- Initiate the webserver per Django instructions


## Usage

Once the databased constructed and Django initation performed, use Django runserver command to start local server. The local server should function identically as the web version albeit using local resources and database.

## Authors

* **Delong Zhou** - Making of enrichment analysis and updating individual gene annotation.
* **Yvan Tran** - Making of individual gene annotation.
* **Sherif Abou Elela** - Supervisor [Abou Elela lab](https://abouelela.recherche.usherbrooke.ca/en/index.php)
* **Michelle Scott** - Supervisor [Scott lab](https://bioinfo-scottgroup.med.usherbrooke.ca)


## License

SAPFIR: Sherbrooke Alternative Protein Feature IdentificatoR

Copyright (c) 2022 Delong Zhou, Yvan Tran, Sherif Abou Elela & Michelle Scott

This program is distributed under [GNU General Public License](http://www.gnu.org/licenses/) as published by the Free Software Foundation, version 3. 

## Acknowledgments

* Many thanks to Danny Bergeron for his help in developing and deploying the web server.

## Reference

**Ensembl** Cunningham, et al. Ensembl 2022. Nucleic Acids Research. 2022. PMID: 34791404.

**InterProScan** Blum, et al. The InterPro protein families and domains database: 20 years on. Nucleic Acids Research. 2020. PMID: 33156333.

**APPRIS** Rodriguez, et al. APPRIS 2017: principal isoforms for multiple gene sets. Nucleic Acids Research. 2018. PMID: 29069475.


