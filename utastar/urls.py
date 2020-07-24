from django.conf.urls import url
from . import views
from django.views.generic import TemplateView
urlpatterns = [
	url(r'^$', views.index, name='index'),
	url(r'create_research', views.get_research, name='get_research'),
	url(r'get_meta_table', views.get_meta_table, name='get_meta_table'),
	url(r'get_multicriteria_table', views.get_multicriteria_table, name='get_multicriteria_table'),
	url(r'get_files',views.get_files,name='get_files'),
	url(r'review/(?P<research_id>\w+)/',views.review,name='review'),
	url(r'results/(?P<research_id>\w+)/',views.results,name='results'),
	url(r'^about',views.about,name='about'),
]