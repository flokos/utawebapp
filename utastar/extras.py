#!/usr/bin/python
# -*- coding: utf-8 -*-
#imports
import matplotlib
matplotlib.use('Agg')
import matplotlib.pylab as plt
import pandas as pd
import utalib
import math
import time
import operator
import numpy as np
from utalib import IOtools, Utastar
from utalib import *
from django.conf import settings
from .models import multicriteriafile,criterionvalue,metafile,criterion,alternative,global_utilities_image,weights_image,marginal_image
from django.core.files.base import ContentFile
from io import BytesIO
import base64
from django.core.files.images import ImageFile
import csv
from django.http import HttpResponse
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import gc

#Make a temporary base64 image
def temp_image(figure):
	#Inittiate buffer
	figfile = BytesIO()
	#Save figure to buffer
	figure.savefig(figfile, format='png')
	figfile.seek(0) # rewind to beginning of file
	figfile.truncate()
	#figdata_png = base64.b64encode(figfile.getvalue()).decode('utf-8').replace('\n', '') 
	#figfile.close()
	#return figdata_png
	canvas=FigureCanvas(figure)
	canvas.print_png(figfile)
	figdata_png = base64.b64encode(figfile.getvalue())
	#Close buffer
	figfile.close()
	#Return the encoded image
	return figdata_png

#Make permanent png image
def perm_image(figure):
	#Initiate buffer
	figfile = BytesIO()
	#Save figure to buffer
	figure.savefig(figfile, format='png')
	#Convert buffer to file
	content_file = ImageFile(figfile)
	#Return the image file
	return content_file

#Create the csvs for export
def create_csv(model_weights,global_utilities,partial_utilities):
	#Create a dict containing empty httpresponses for all the data
	response_dict = {
			'model_weights':HttpResponse(content_type='text/csv'),
			'global_utilities':HttpResponse(content_type='text/csv'),
			'partial_utilities':HttpResponse(content_type='text/csv'),
			}
	#Save the data to the httpresponses
	model_weights.to_csv(response_dict['model_weights'])
	global_utilities.to_csv(response_dict['global_utilities'])
	partial_utilities.to_csv(response_dict['partial_utilities'])
	#Return the httpresponses dict
	return response_dict
# create utastar plots
def create_plots(utastar_obj,research):
	# plot partial utilities
	numofcriteria =len(utastar_obj.criteria)
	n = numofcriteria
	if n % 2 == 0:
		fig1, axs = plt.subplots(n/2, 2)
	else:
		fig1, axs = plt.subplots(n/2+1, 2)
	for i in range(n):
		y = utastar_obj.marginal_post[utastar_obj.criteria[i]]
		x = utastar_obj.intervals[utastar_obj.criteria[i]]
		if i % 2 == 0:
			if utastar_obj.get_type(utastar_obj.criteria[i])==1:
				axs[i/2, 0].plot(x, y, '--ok')
				axs[i/2, 0].set_title(utastar_obj.criteria[i])
				axs[i/2, 0].set_xticks(x)
				axs[i/2, 0].set_xlim(x[0],x[-1])
				axs[i/2, 0].set_ylabel(r'$u_{%d}(g_{%d})$'%((i+1),(i+1)))
				axs[i/2, 0].yaxis.grid(False)
				if utastar_obj.get_monotonicity(utastar_obj.criteria[i])==1:
					axs[i/2, 0].set_xlim(x[-1],x[0])
			else:
				axs[i/2, 0].plot(x, y, '-ok')
				axs[i/2, 0].set_title(utastar_obj.criteria[i])
				axs[i/2, 0].set_xticks(x)
				axs[i/2, 0].set_xlim(x[0],x[-1])
				axs[i/2, 0].set_ylabel(r'$u_{%d}(g_{%d})$'%((i+1),(i+1)))
				axs[i/2, 0].yaxis.grid(False)
				if utastar_obj.get_monotonicity(utastar_obj.criteria[i])==1:
					axs[i/2, 0].set_xlim(x[-1],x[0])
		else:
			if utastar_obj.get_type(utastar_obj.criteria[i])==1:
				axs[i/2, 1].plot(x, y, '--ok')
				axs[i/2, 1].set_title(utastar_obj.criteria[i])
				axs[i/2, 1].set_xticks(x)
				axs[i/2, 1].set_xlim(x[0],x[-1])
				axs[i/2, 1].set_ylabel(r'$u_{%d}(g_{%d})$'%((i+1),(i+1)))
				axs[i/2, 1].yaxis.grid(False)
				if utastar_obj.get_monotonicity(utastar_obj.criteria[i])==1:
					axs[i/2, 1].set_xlim(x[-1],x[0])

			else:
				axs[i/2, 1].plot(x, y, '-ok')
				axs[i/2, 1].set_title(utastar_obj.criteria[i])
				axs[i/2, 1].set_xticks(x)
				axs[i/2, 1].set_xlim(x[0],x[-1])
				axs[i/2, 1].set_ylabel(r'$u_{%d}(g_{%d})$'%((i+1),(i+1)))
				axs[i/2, 1].yaxis.grid(False)
				if utastar_obj.get_monotonicity(utastar_obj.criteria[i])==1:
					axs[i/2, 1].set_xlim(x[-1],x[0])
	if n % 2 != 0:
		for l in axs[i/2-1,1].get_xaxis().get_majorticklabels():
			l.set_visible(True)
		fig1.delaxes(axs[i/2, 1])
	#plt.subplots_adjust(wspace = 0.3,hspace = 0.3)
	plt.tight_layout()
	## plot bar weights
	fig2 = plt.figure(2)
	ax = fig2.gca()
	ax.bar(range(len(utastar_obj.model_weights_post))[::-1], utastar_obj.model_weights_post.values(), align='center',color='grey',alpha=0.8)
	plt.xticks(range(len(utastar_obj.model_weights_post))[::-1], utastar_obj.model_weights_post.keys())
	plt.title('Model weights')
	plt.tight_layout()
	# ## plot radar weights
	# # example data
	# variables = utaobj.model_weights_post.keys()
	# data = utaobj.model_weights_post.values()
	# ranges = [(0.1, max(utaobj.model_weights_post.values()))]*len(utaobj.criteria)
	# 
	# # plotting
	# fig3 = plt.figure(3,figsize=(8, 8))
	# radar = ComplexRadar(fig3, variables, ranges,4)
	# radar.plot(data)
	# radar.fill(data, alpha=0.2, color='grey')
	##plot  Ranking
	fig4 = plt.figure(4)
	ax = fig4.gca()
	ax.barh(range(len(utastar_obj.global_utilities_post))[::-1], utastar_obj.global_utilities_post.values(), align='center',color='grey',alpha=0.8)
	plt.yticks(range(len(utastar_obj.global_utilities_post))[::-1], utastar_obj.global_utilities_post.keys())
	ax.plot(utastar_obj.global_utilities_post.values(),range(len(utastar_obj.global_utilities_post))[::-1],linestyle='--',color='black',alpha=0.8)
	plt.xlim(0,1)
	plt.title('Ranking')
	plt.tight_layout()
	existing_gui_file = research.global_utilities_image_set.last()
	existing_wi_file = research.weights_image_set.last()
	existing_mi_file = research.marginal_image_set.last()
	if existing_gui_file:
		existing_gui_file.delete()
	if existing_wi_file:
		existing_wi_file.delete()
	if existing_mi_file:
		existing_mi_file.delete()
	gui = global_utilities_image(research=research)
	wi = weights_image(research=research)
	mi = marginal_image(research=research)
	gui.global_utilities_post.save('gup.png',perm_image(fig1))
	wi.model_weights_post.save('mwp.png',perm_image(fig2),save=True)
	mi.marginal_post.save('mp.png',perm_image(fig4),save=True)
	#k = pd.DataFrame.from_dict(utastar_obj.model_weights_post,orient='index')
	#return mpld3.fig_to_html(fig4,template_type='general')
	gui.save()
	wi.save()
	mi.save()
	img_dict = {
			'partial_utilities':temp_image(fig1),
			'weights':temp_image(fig2),
			'ranking':temp_image(fig4),
			}
	fig1.clf()
	fig2.clf()
	fig4.clf()
	gc.collect()
	return img_dict
#function to create list of criteria per alternatives	
def crit_per_alt(alternatives,criteria):
		altcrit = []
		for alternative in alternatives:
			for criterion in criteria:
				altcrit.append([alternative,criterion])
		return altcrit
#function to create mutlicriteria table as pd.DataFrame
def multicriteria_to_df(alternatives_set,criteria_set,current_research):
		multicriteria_table = []
		for alternative in alternatives_set:
			criterionvalues_set = alternative.criterionvalue_set.filter(research__name = current_research.name)#get criterion values for each alternative of current research
			multicriteria_row = []
			for criterionvalue in criterionvalues_set:
				multicriteria_row.append(criterionvalue.value)#list of criterion values for each criterion 
			multicriteria_table.append(multicriteria_row)#list of lists including criterion values for each alternative
		criteria = list( criteria_set.values_list('criterion_name',flat=True))#get criterion names
		alternatives = list(alternatives_set.values_list('name', flat=True))#get alternatives names
		dfalternatives = pd.DataFrame({'Alt/cri':alternatives})
		df = pd.DataFrame(multicriteria_table,columns=criteria)#create multicriteria table df
		data = dfalternatives.join(df,lsuffix='_dfalternatives',rsuffix='_df')#set dfalternatives as first column of df 
		return data
#function to create metatable to pd.DataFrame		
def meta_to_df(criteria_set):
		meta_table = []
		for crit in criteria_set:#get criterion model attributes
			meta_row = [crit.criterion_name,crit.criterion_monotonicity,crit.criterion_type,crit.criterion_worst,crit.criterion_best,crit.criterion_a]
			
			meta_table.append(meta_row)
		criteria_attr = ['Cri/atributes','Monotonicity','Type','Worst','Best','a'] #set column names
		df = pd.DataFrame(meta_table,columns=criteria_attr)
		return df

#Function to run utastar method		
def run_utastar(table,metatable,ranking_list,delta,epsilon):
	#Make the ranking column as dataframe
	ranking = pd.DataFrame({'Ranking':ranking_list})
	#Join the ranking column with the multicriteria table
	table = table.join(ranking, lsuffix='_table', rsuffix='_ranking')
	#Create utastar object with the data created above
	utaobj=Utastar(table,metatable,delta,epsilon)
	#Solve the problem
	utaobj.solve()
	#Return utastar object that contains the solution of the problem and the given data
	return utaobj
	
def validate_multicriteria_file(research):#function to check if uploaded mutlicriteria data file is valid
	file_obj = multicriteriafile.objects.filter(research=research).last()
	file_name = file_obj.multicriteria_file.name
	file_path = os.path.join(settings.MEDIA_ROOT,file_name)
	io_object = IOtools()
	file = io_object.load_from_csv(file_path)#load uploaded file
	criteria = research.criterion_set.all()#get criterion attributes that are saved in database(not the ones uploaded from file)
	criteria_length = len(criteria)
	file_columns = file.columns#get uploaded file's columns
	file_columns_length = len(file_columns)#number of uploaded file's columns
	file_rows_length = len(file.index)#get uploaded file's rows number
	header = ['Alt/cri'] + list(criteria.values_list('criterion_name',flat=True))#list with criterion names (based on our database)
	criteria_names = list( criteria.values_list('criterion_name',flat=True))#get criterion values from database
	flags = {}
	string_flags = flags 
	errors = []# list of strings describing errors
	try:
		for c in criteria:
				flags.update({c.criterion_name:[c.criterion_worst,c.criterion_best,0]})
		if file_columns_length == criteria_length+1:#check if uploaded file's column number is equal to criteria number saved in database
			if 'Alt/cri' in file.columns:#check if uploaded file has a column named 'Alt/cri'
				save_alternatives(file,research)#call function to get alternatives from database
				alternatives = research.alternative_set.all()
				alternatives_length = len(alternatives)
				rows = list(alternatives.values_list('name', flat=True))
				if file_rows_length == alternatives_length:#check if uploaded file's rows number is equal to alternatives number from database
					uncommon_columns = list(set(file_columns).difference(set(header)))#get file columns which have different names from criterion names list
					if not uncommon_columns:#if list is empty
						file_rows = file['Alt/cri'].tolist()
						if list(file_columns).index('Alt/cri') == 0:#if uploaded file's 1st column is named 'Alt/cri'
							for row in file.index:
								for column in file_columns:
									if column != 'Alt/cri':#for every file column besides the 1st one
										crivalue = file.ix[row][column]#get criterion value from file
										alt_name = file_rows[row]#get alternative name from file
										alt = alternatives.get(name=alt_name)# get alternative name from database
										crit = criteria.get(criterion_name=column)#get criterion name from database
										#check if criterion value is between worst and best values (according to monotonicty)
										if (crit.criterion_monotonicity == 0 and (crivalue < crit.criterion_worst or crivalue > crit.criterion_best)) or (crit.criterion_monotonicity == 1 and (crivalue > crit.criterion_worst or crivalue < crit.criterion_best)) :
											flags[column][2]+= 1
											criterionvalue.objects.filter(research=research).delete()#if there are errors delete uploaded file's criterion values
										elif sum(flags[key][2] for key in flags.keys()) == 0:#if there are 0 errors save criterion values
											critvalue = criterionvalue(research=research,alt=alt,crit=crit,value=crivalue)
											critvalue.save()
							for key in flags.keys():
								if flags[key][2] != 0:
									errors.append('%s can take values between %f and %f .'%(key,flags[key][0],flags[key][1]))
						else:
							errors.append('Multicriteria table file must have Alt/cri as first column.')
					else:
						for uncommon in uncommon_columns:
							errors.append('Column with name %s is not included in mutlicriteria table file.'% uncommon) 
				else:
					errors.append('Multicriteria table file must have %d rows.'%(alternatives_length+1))
			else:
				errors.append('Multicriteria table file must contain a column name Alt/cri.')
		else:
			errors.append('Multicriteria table file must have %d columns.'%(criteria_length+1))
	except Exception:
		research.delete()
		errors.append("Unknown error.")
		time.sleep(5)
	return errors#list of all the errors uploaded file has
	
def save_alternatives(file,research):# function to save alternatives from multicriteria file
	alternatives = list(file['Alt/cri'])
	for alt in alternatives:
		alt_instance = alternative(alternative_research=research,name=alt,ranking=alternatives.index(alt)+1)
		alt_instance.save()

def validate_meta_file(research):#function to check if uploaded metatable file is valid
	file_obj = metafile.objects.filter(research=research).last()
	file_name = file_obj.meta_file.name
	file_path = os.path.join(settings.MEDIA_ROOT,file_name)
	io_object = IOtools()
	file = io_object.load_from_csv(file_path)
	file_columns = list(file.columns)#get file columns
	file_columns_length = len(file_columns)
	errors = [] # list with errors
	default_header = ['Cri/atributes','Monotonicity','Type','Worst','Best','a'] # list with default column names an uploaded file must have
	flag = 0 #if there is an error in uploaded file flag +=1
	try:
		if file_columns_length == 6:
			print file_columns
			print default_header
			if file_columns == default_header: # check if uploaded file's column names are the same with default header
				if file['Monotonicity'].isin([0,1]).all():# check if monotonicity takes only 2 values
					if file['Type'].isin([0,1]).all(): #check if type takes only 2 values
						if file['a'].dtype == 'int64' and (file['a'] >= 2).all():#a varriable of file must be integer greater than 2
							for row in file.index:
								if not file.ix[row]['Monotonicity'] == 0 and file.ix[row]['Worst'] < file.ix[row]['Best']:#Check best and worst values according to monotonicity
									errors.append('%s:Best must be strictly greater than Worst.')
									flag += 1
									criterion.objects.filter(research=research).delete()#if there is an error delete criterion
								elif not file.ix[row]['Monotonicity'] == 1 and file.ix[row]['Worst'] > file.ix[row]['Best']:
									errors.append('%s:Worst must be strictly greater than Best.')
									flag += 1
									criterion.objects.filter(research=research).delete()
								elif flag == 0:#if there is no error save criterion to database
									crit_instance = criterion(criterion_research=research,criterion_name=file.ix[row]['Cri/atributes'],criterion_type=file.ix[row]['Type'],criterion_monotonicity=file.ix[row]['Monotonicity'],criterion_a=file.ix[row]['a'],criterion_worst=file.ix[row]['Worst'],criterion_best=file.ix[row]['Best'])
									crit_instance.save()
						else:
							errors.append('a must be integer and equal or greater than 2.')
					else:
						errors.append('Type can take two values: 0 for quantitative,1 for qualitative.')
				else:
					errors.append('Monotonicity can take two values: 0 for ascending,1 for descending.')
			else:
				errors.append('The header of the meta file must be the following: %s'%(','.join(default_header)))
		else:
			errors.append('Meta file must have 6 columns with name %s'%(','.join(default_header)))
	except Exception:
		research.delete()
		errors.append("Unknown error.")
		time.sleep(5)
	return errors