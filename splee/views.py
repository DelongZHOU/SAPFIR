import os
import pandas as pd
import base64
from io import BytesIO


from django.conf import settings
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.http import HttpResponse,Http404
from django.shortcuts import render,redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.core.files import File
from django import forms



from .spleeDrawingImage.splee import Splee  
from .mapping.mapping_domain import *

from .models import Query 	

#create form objects for species and prediction tool selection
class SpeciesForm(forms.Form):
      species_choices = ( ("human","Human GRCh38 (hg38)"),
                          ("mouse","Mouse CRCm39 (mm39)"),
                        )
      name_text = "Please select the species :\n"
      species=forms.ChoiceField(choices=species_choices,label=name_text,widget=forms.RadioSelect,initial='human',required=True)
class ToolForm(forms.Form):
      tool_choices = (  ("Pfam","Pfam: protein families and domains"),
                        ("SFLD","SFLD: protein families"),
                        ("PANTHER","PANTHER: gene classification by functions"),
                        ("Hamap","Hamap: High-quality Automated and Manual Annotation of Microbial Proteomes"),
                        ("ProSiteProfiles","ProSiteProfiles: protein domains, families, functional sites and associated patterns and profiles"),
                        ("ProSitePatterns","ProSitePatterns: protein domains, families, functional sites and associated patterns and profiles"),
                        ("SMART","SMART: domain architectures"),
                        ("CDD","CDD:  protein domains and families"),
                        ("PRINTS","PRINTS: protein fingerprints (groups of conserved motifs used to characterise protein families)"),
                        ("TIGRFAM","TIGRFAM: protein families"),
                        ("PIRSF","PIRSF: protein families and domains"),
                        ("SUPERFAMILY","SUPERFAMILY: structural and functional annotations"),
                        ("Gene3D","Gene3D: protein families and domain architectures"),
                        ("Coils","Coils: coiled coil regions "),
                        ("MobiDBLite","MobiDBLite: intrinsically disordered regions"),
                     )
      name_text = "Please select one (recommended) or more prediction tool(s) from the following list.\nTo start exploring, choose only Pfam.\n"
      prediction_tools=forms.MultipleChoiceField(choices = tool_choices,label=name_text,widget=forms.CheckboxSelectMultiple,required=True,initial="Pfam")

#handel404
def handle404(request,exception):
   html="<p> Your request failed. </p> <br> <p> Please verify your input or consult the <a href='/help'> help page </a> for more information. </p>"
   return HttpResponse(html)

#single query home page
def search_form(request):
   context={'species_form':SpeciesForm(),'tool_form': ToolForm()}
   return render(request,"splee/single_form.html",context)

#redirect to single query result page
def search_single(request):
   gene_id=request.GET["gene_id"]
   species=request.GET['species']
   tools='+'.join(request.GET.getlist('prediction_tools')) #transform the list of tools into a string to pass in url
   ratio=str(request.GET['ratio'])
   return redirect(reverse(single_result,kwargs={'gene_id':gene_id,'species':species,'tools':tools,'ratio':ratio}))
  

#single query result page
def single_result(request,gene_id,species,tools,ratio='0.25'):
   import traceback
   try:
      #generate splee object
      tools=tools.split('+') #reverse transform tools from string to list
      splee=Splee(gene_id,species,tools,float(ratio))
      #generate domain plot images
      splee_plot=splee.images()
      #by default splee.strand is empty; the information is only updated once splee.image() is called
      strand=splee.strand
      with BytesIO() as output:
         splee_plot.save(output, "PNG")
         plot = base64.b64encode(output.getvalue()).decode()
      #generate tables to display in single_result.html
      #Yvan's original code & comment, cleaned up a bit
      #Need rewrite eventually
      if not splee.allPresentProt.empty:
         #Yvan's comment:
         #this might seem weird but what I am basically doing is sending the title of the tables + the contents of the table (in html) via the context for allPresentProt
         #I am doing the same for the others
         #Btw the <h3> tag and the ones from the 
         #splee.allPresentProt.to_html(classes = 'allPresentProt", table_id = "allPresentProt', index= False)
         #(conversion of dataframe to html code)
         #are regulated in the styleForRequestPage.css in the static files
         domain_table_header= "<h3> Constitutive table for protein features </h3>" + splee.allPresentProt.to_html(classes = 'allPresentProt" id = "allPresentProt', index= False)
      else: 
         domain_table_header= "<h3>S2D2 did not detect any protein features with the search parameters.</h3>"
      if not splee.domains_table.empty:
         domains= "<h3> Proteins domains table </h3>" + splee.domains_table.to_html(classes = 'domains" id = "domains',index= False)
      else: 
         domains= ""
      if species=='human':
         species_string='Homo_sapiens'
      else:
         species_string='Mus_musculus'
      gene_url='https://ensembl.org/{}/Gene/Summary?db=core;g={}'.format(species_string,gene_id) #Ensembl link for gene in species as of 2022-05-21
      gene_string='{}, please follow the link to <a href={}>Ensembl gene summary page</a>'.format(gene_id,gene_url)
      context={'gene_id': gene_id,
            'gene_string' : gene_string,
            'species' : species,
            'plot':plot,
            'domains':domains,
            'domain_table_header':domain_table_header,
            'ratio':ratio,
            'tools':', '.join(tools),
            'strand':strand,
            }
      return render(request,'splee/single_result.html',context)
   except:
      traceback.print_exc()
      context={'gene_id': gene_id,
            'species' : species,
            }
      return render(request,'splee/single_error.html',context)



#batch query home
def map_form(request):
   context={'species_form':SpeciesForm(),'tool_form': ToolForm()}
   return render(request,"splee/map_form.html",context)

#redirect to batch query result page

BASE_DIR=settings.BASE_DIR
MEDIA_ROOT = os.path.join(BASE_DIR,'media')



def search_map(request):
    import traceback
    if request.method == "POST":
        try:
            for key, value in request.POST.items():
               print(key,value)
            query_id=get_random_string(length=32) #generate random string as query id
            #make sure query_id is unique
            list_query_ids=Query.objects.all().values_list('query_id',flat=True) #using django model methods to retrieve all used query_id
            while query_id in list_query_ids: 
                query_id=get_random_string(length=32)
            wdir=os.path.join(MEDIA_ROOT,'submission',query_id)
            os.makedirs(wdir,exist_ok=True)

            #initiate query object
            query=Query(query_id=query_id,submit_date=timezone.now())
            #print(query.id)
            #print(Query.objects.all())
            query.species=request.POST.get('species')
            tools=request.POST.getlist('prediction_tools')
            query.tools_str='+'.join(tools)
            #Save uploaded files
            print("save uploaded files")
            default_storage.save(os.path.join(wdir,'target.txt'),request.FILES['targetFile'])
            os.chmod(os.path.join(wdir,'target.txt'),0o444)
            default_storage.save(os.path.join(wdir,'bg.txt'),request.FILES['backgroundFile'])
            os.chmod(os.path.join(wdir,'bg.txt'),0o444)
      
            #First extract events to work with and reorder columns
            extract_file(os.path.join(wdir,'target.txt'),os.path.join(wdir,'target.bed'))
            extract_file(os.path.join(wdir,'bg.txt'),os.path.join(wdir,'bg.bed'))
    
            #Filter domain table based on selected prediction tools
            print("Filter domain table based on selected prediction tools")
            domain=pd.read_csv(os.path.join(BASE_DIR,'utility',query.species+'_domain.tsv'),
                               header=None,sep='\t',
                               names=['gene_id','start','end','tool','signature','InterPro_acc','description'])
            print(domain.head())
            print(tools)
            domain_tool=domain[domain['tool'].isin(tools)]
            print(domain_tool.head())
            #merge tool, signature, IPR_acc, IPR_des columns into one column with ';' as separation
            domain_tool['info']=domain_tool.apply(lambda row: '@'.join(map(str,[row['tool'],
                                                                                row['signature'],
                                                                                row['InterPro_acc'],
                                                                                row['description'],
                                                                               ]
                                                                           ))
                                                   , axis=1)
            domain_tool[['gene_id','start','end','info']].to_csv(os.path.join(wdir,'domain.bed'),header=False,index=False,sep='\t')
    
            #Map domains on target and bg
            print("Map domains")
            map_domain(os.path.join(wdir,'target.bed'),os.path.join(wdir,'domain.bed'),os.path.join(wdir,'target_domain.bed'),wdir)
            map_domain(os.path.join(wdir,'bg.bed'),os.path.join(wdir,'domain.bed'),os.path.join(wdir,'bg_domain.bed'),wdir)
    
            #Save annotated target and bg in correct order, these are the files to link in the output page
            switch_column(os.path.join(wdir,'target_domain.bed'),os.path.join(wdir,'target_annotation.bed'))
            switch_column(os.path.join(wdir,'bg_domain.bed'),os.path.join(wdir,'background_annotation.bed'))
    
            #Make enrichment test
            print("Calculate enrichment")
            query.n_target,query.n_bg,query.n_domains = enrichment(os.path.join(wdir,'target_domain.bed'),os.path.join(wdir,'bg_domain.bed'),wdir)
    
            #associate related files to query object
            query.enrichment.name = os.path.join('submission',query_id,'enrichment.tsv')
            #print(query.enrichment.url)
            query.target_annotation.name = os.path.join('submission',query_id,'target_annotation.bed')
            query.bg_annotation.name = os.path.join('submission',query_id,'background_annotation.bed')
    
            #take the most enriched domains from enrichment.tsv and associate to query object
            df=pd.read_csv(os.path.join(wdir,'enrichment.tsv'),sep='\t',header=0)
            print(df.head())
            header=df[['Tool','Signature','InterPro Accession','InterPro Description','Target Count','Background Count','p-val','q-val','Enrichment']].copy()
            header=header[header['Enrichment']>1].head()
            query.enrichment_html=header.to_html(classes = 'enrichment" id = "enrichment', index= False)
            
            #update query object with save
            query.save()

            return redirect(reverse(map_result,kwargs={'query_id':query_id}))
        except Exception as e:
            traceback.print_exc()
            return render(request, 'splee/map_error.html')

# batch query result

def map_result(request,query_id):
    query=Query.objects.get(query_id=query_id)
    return render(request, 'splee/map_result.html', {"query":query})

    
