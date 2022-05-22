from django.conf.urls import  url, handler404

from splee import views

urlpatterns = [
 
   url(r'^search-form/$', views.search_form, name= 'single_form'),
   url(r'^search-form/search/$', views.search_single, name='search_single'),
   url(r'^search-form/result/(?P<gene_id>[A-Za-z0-9\-@\_]*),(?P<species>[A-Za-z]*),(?P<tools>[A-Za-z0-9\+]*),(?P<ratio>[0]*.[0-9]+)',views.single_result, name='single_result'), 
   url(r'^map-form/$', views.map_form, name= 'search_map'),
   url(r'^map-form/search/$', views.search_map, name='search_map'),
   url(r'^map-form/query/(?P<query_id>[A-Za-z0-9]{32})$', views.map_result, name='map_result'),
]

handler404 = 'splee.views.handle404'
