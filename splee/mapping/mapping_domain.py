def extract_file(origin,extraction):
    '''
Extract the first 6 columns from a tab-separated file origin and saves into extraction a 6 column pandas dataframe with ensembl_id (4th column) as chr and chr as id
Example input:
	chr1	100	200	ENSG00x 100 +
Example output:
	ENSG00x	100	200	chr1	100 +
    '''
    import pandas as pd
    df=pd.read_csv(origin,sep='\t',header=None).iloc[:,[3,1,2,0,4,5]]
    df.to_csv(extraction,index=False,header=False,sep='\t')



def map_domain(events,domains,annotated_events,temp):
    '''
Use bedtools to map bed4 like domains or localization file into bed6 like events, annotating which domains are found in each exon. Save output as annotated_events in ensembl id first order
Save pybedtools temp files in the temp folder
    '''
    import pybedtools
    pybedtools.set_tempdir(temp) #set temp file dir for better space management
    events=pybedtools.BedTool(events).sort()
    domains=pybedtools.BedTool(domains).sort()
    events.map(domains,c=[4],o=['distinct']).saveas(annotated_events) #bedtool syntax #tool, signature, IPR_acc, IPR_des

def switch_column(origin,reorder):
    '''
	Swtich the 1st column (Ens ID for annotated events) with the 4th column (real chr)
	Also split last column of predictions
    '''
    with open(origin) as fi, open(reorder,'a') as fo:
        for l in fi:
            s=l.strip().split('\t')
            s[0],s[3]=s[3],s[0] #swtich columns
            if s[-1]=='.':
                pass
            else:
                predictions=s[-1].split(',')
                tools=[]
                signatures=[]
                accs=[]
                dess=[]
                for prediction in predictions:
                    tool,signature,acc,des=prediction.split('@')
                    tools.append(tool)
                    signatures.append(signature)
                    accs.append(acc)
                    dess.append(des)
                s=s[:-1]+[','.join(tools),','.join(signatures),','.join(accs),','.join(dess)]
            fo.write('\t'.join(s)+'\n')

def chi2(c1r1,c1r2,c2r1,c2r2):
    '''
chi squared test with c=condition r=result
equivalent for prop.test in R
return p value
    '''
    import numpy as np
    from scipy import stats
    return stats.chi2_contingency(np.array([[c1r1,c1r2],[c2r1,c2r2]]))[1]

def enrichment(annotated_target,annotated_bg,fold):
    '''
Take annonated target and annotated background as input, and
1) count how many domains are found in each list and save into a dict object
	domain: [ count_target, count_bg ]
2) create a dataframe of counts from the dict object
3) calculate enrichment p val
4) Benjamini adjustment
5) Save a log file which contains 3 values: number of target entries, number of bg entries and number of domains
6) Save the domains, counts, pval, qval and enrichment
    '''
    import os
    import pandas as pd
    res_dict={} #dictionary to hold domain count

    n_target=0 #count target entries
    n_bg=0 #count bg entries
    with open(annotated_target) as f:
        for l in f:
            n_target+=1
            #last column contains tool, signature, InterPro_acc and InterPro_des joined by ";"
            domains=l.strip().split('\t')[-1] 
            if domains != '.': #there is at least one overlapping domain
                domains=domains.split(',')
                for i in range(len(domains)): #mapBed collapse result is separated by comma
                     domain=domains[i].strip() #remove the white space before and after comma
                     if domain in res_dict: #domain already encountered
                         res_dict[domain][0]+=1 
                     else: #a new domain appeared
                         res_dict[domain]=[1,0] #initiate with count 

    with open(annotated_bg) as f:
        for l in f:
            n_bg+=1
            #last column contains tool, signature, InterPro_acc and InterPro_des joined by ";"
            domains=l.strip().split('\t')[-1] 
            if domains != '.': #there is at least one overlapping domain
                domains=domains.split(',')
                for i in range(len(domains)): #mapBed collapse result is separated by comma
                     domain=domains[i].strip() #remove the white space before and after comma
                     if domain in res_dict: #domain already encountered
                         res_dict[domain][1]+=1 
                     else: #a new domain appeared
                         res_dict[domain]=[0,1] #initiate with count 

    if res_dict:
        df=pd.DataFrame.from_dict(res_dict,orient='index',columns=['Target Count','Background Count'])
        df.index.name='prediction'
        df.reset_index(level='prediction',inplace=True)
        df[['Tool','Signature','InterPro Accession','InterPro Description']]=df['prediction'].str.split("@",4,expand=True)
        df['Link']=''
        df['Link']=df['InterPro Accession'].apply(lambda x: "nan" if x=="nan" else "https://www.ebi.ac.uk/interpro/entry/{}".format(x))
        #df.to_csv('df.csv')
        df['p-val']=df.apply(lambda row: chi2(n_bg-row['Background Count'],row['Background Count'],n_target-row['Target Count'],row['Target Count']), axis=1)
        df=df.sort_values(by=['p-val']) #sort by p-val in ascending order
        df['Rank']=df['p-val'].rank()
        n_domains=len(res_dict.keys()) #total number of domains mapped
        df['q-val']=df.apply(lambda row: min(row['p-val']*n_domains/row['Rank'],1) , axis=1)
        df['Enrichment']=df.apply(lambda row: row['Target Count']*(n_bg+n_target)/(row['Background Count']+row['Target Count'])/n_target , axis=1)
        #mark down submission summary and save enrichment file for download
        with open(os.path.join(fold,'log'),'a') as log:
            log.write('Target_entries\t{}\n'.format(n_target))
            log.write('Background_entries\t{}\n'.format(n_bg))
            log.write('Number_of_domain_or_ls_mapped\t{}\n'.format(n_domains))
        df=df[['Tool','Signature','InterPro Accession','InterPro Description','Link','Target Count','Background Count','p-val','q-val','Enrichment']]
    else:
        df=pd.DataFrame(columns=['Tool','Signature','InterPro Accession','InterPro Description','Link','Target Count','Background Count','p-val','q-val','Enrichment'])
        n_domains=0
    df.to_csv(os.path.join(fold,'enrichment.tsv'),sep='\t',index=False)
    return (n_target,n_bg,n_domains)


