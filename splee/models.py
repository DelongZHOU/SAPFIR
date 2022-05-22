from django.db import models
from django import forms
#from picklefield.fields import PickledObjectField
#import pandas as pd

# Create your models here.

  


class Query(models.Model):
    query_id = models.CharField(max_length =32,default="0"*32) #query_id is a randomly generated string of 32 character
    #status = models.CharField(max_length =32,default="")
    submit_date = models.DateTimeField('date submitted')
    species = models.CharField(max_length=20,default="human")
    tools_str = models.CharField(max_length=200,default="")
    email = models.EmailField(max_length=254,default="test@test.test")
    n_target=models.IntegerField()
    n_bg=models.IntegerField()
    n_domains=models.IntegerField()
    enrichment=models.FileField(upload_to='submission')
#    enrichment_df=PickledObjectField()
#    enrichment_df=pd.DataFrame()
    enrichment_html=models.CharField(max_length =2000)
    target_annotation=models.FileField(upload_to='submission')
    bg_annotation=models.FileField(upload_to='submission')
    def __str__(self):
        return self.query_id

