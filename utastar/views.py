#!/usr/bin/python
# -*- coding: utf-8 -*-
#import needed libraires
from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from .models import research,criterion,alternative,criterionvalue,multicriteriafile,metafile,utastar_model
from django.forms import formset_factory,modelformset_factory,inlineformset_factory
from .forms import CreateResearchForm,CreateCriterionForm,CreateAlternativeForm,CreateCriterionValueForm,Decision,CreateMulticriteriaFile,CreateMetaFile,CreateRankingForm, CreateParametersForm
from .extras import crit_per_alt,multicriteria_to_df,meta_to_df,validate_multicriteria_file,validate_meta_file,run_utastar,create_plots,create_csv
from django.contrib import messages
from django.shortcuts import get_list_or_404, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
import pandas as pd

#Login required to access this view
@login_required
#View that handles the research creation
def get_research(request):
	#Get the user that is logged in
	current_user = request.user
	#if the request is post
	if request.method == 'POST':	
		#Create a research form that containes the psot data
		research_form = CreateResearchForm(request.POST,prefix='research_form')
		#Create a decision form (upload or manual insertion) that includes the posted data
		decision_form = Decision(request.POST,request.FILES)
		#if the submit button is clicked
		if 'submit' in request.POST:
			#if the forms are valid
			if research_form.is_valid() and decision_form.is_valid():
				#get a copy of the research object contained in the research form
				instance = research_form.save(commit=False)
				#add the user instance to the research object
				instance.user = current_user 
				#save the research object
				instance.save()
				#Set cookie to signal the other views that this step finnished(research creation)
				request.session['research'] = True
				#if the decision is to insert the data manually
				if decision_form.cleaned_data['decision'] == '0':
					#Set cookie to signal the other views that in this step "manual entry" was chosen
					request.session['decision'] = 'tables'
					#Set a cookie to track the next step's status(the insert meta table step)
					request.session['meta_table'] = False
					#Redirect user to the meta table insertion page
					return  HttpResponseRedirect('get_meta_table')
				else:
					#Set cookie to signal the other views that in this step "upload from files" was chosen
					request.session['decision'] = 'files'
					#Set a cookie to track the next step's status(the upload files step)
					request.session['files'] = False
					#Redirect uswr to the file uploading page
					return HttpResponseRedirect('get_files')
	#if the request is get
	else:
		#Create a research form
		research_form = CreateResearchForm(prefix='research_form')
		#Create a decision form (upload or manual insertion)
		decision_form = Decision()
	#Render the page.Arguments passed:research and decision form
	return render(request,'CreateResearch.html',{
												'research_form':research_form,
												'decision_form':decision_form,
												})		
#Login required to access this view
@login_required
#View that handles the manual insertion of the meta table
def get_meta_table(request):
	#Get the user that is logged in
	current_user = request.user
	#Get the last research created by the current user
	current_research = current_user.research_set.last()
	#if a research has been created 
	if request.session.get('research',False): 
		#if the decision was manual insertion (in the decision form)
		if request.session.get('decision',None) == 'tables':
			#if the meta table is not yet
			if request.session.get('meta_table',False) == False:
				#Flag to track "add" button for criteria 
				change_crit = '0'
				#Flag to track "add" button for alternatives
				change_alt = '0'
				#Create a formset template based on the criterion model 
				CriterionFormSet = formset_factory(CreateCriterionForm,extra=1,can_delete=True)
				#Create a formset template based on the alternative model
				AlternativeFormset = formset_factory(CreateAlternativeForm,extra=1,can_delete=True)
				#if the request is post
				if request.method == 'POST':
					#if the add button for the criteria was clicked
					if 'add_criterion' in request.POST:
						##Hack to add new forms dynamically without using javascript
						#Create a copy of the post data
						post_data = request.POST.copy()
						#Add a new criterion form in the post data
						post_data['criterion_form-TOTAL_FORMS'] = int(post_data['criterion_form-TOTAL_FORMS']) + 1 
						#Create a criterion formset with the updated post data
						criterion_formset = CriterionFormSet(post_data, request.FILES,prefix='criterion_form')
						#Create a alternative formset with updated post data
						alternative_formset = AlternativeFormset(post_data,request.FILES,prefix='alternative_form')
						#Trigger flag for criterion form addition
						change_crit ='1'
					#if the add button for the alternatives was clicked
					elif 'add_alternative' in request.POST:
						##Hack to add new forms dynamically without using javascript
						#Create a copy of the post data
						post_data = request.POST.copy()
						#Add a new alternative form in the post data
						post_data['alternative_form-TOTAL_FORMS'] = int(post_data['alternative_form-TOTAL_FORMS']) + 1
						#Create a criterion formset with the updated post data
						criterion_formset = CriterionFormSet(post_data, request.FILES,prefix='criterion_form')
						#Create an alternative formset with updated post data
						alternative_formset = AlternativeFormset(post_data,request.FILES,prefix='alternative_form')
						#Trigger flag for alternative form addition
						change_alt = '1'
					#if the submit button was clicked	
					elif 'submit' in request.POST:
						#Create a criterion formset with the post data
						criterion_formset = CriterionFormSet(request.POST, request.FILES,prefix='criterion_form')
						#Create an alternative formset with post data
						alternative_formset = AlternativeFormset(request.POST,request.FILES,prefix='alternative_form')
						#if the criterion formset is valid
						if criterion_formset.is_valid():
							#For every form in the criterion formset
							for form in criterion_formset:
								#if the current form is valid 
								if form.is_valid():
									#get a copy of the criterion object contained in the form
									instance = form.save(commit=False)
									#add the relationship with the current research
									instance.criterion_research = current_research
									#save the object
									instance.save()
							#if the alternative formset is valid
							if alternative_formset.is_valid():
								#For every form in the alternative formset
								for form in alternative_formset:
									#if the current form is valid
									if form.is_valid():
										#get a copy of the alternative object contained in the form
										instance = form.save(commit=False)
										#add the relationship with the current research
										instance.alternative_research = current_research
										#set the default ranking as the form's index in the alternative formset(starting from 1)
										instance.ranking = alternative_formset.forms.index(form)+1
										#save the object
										instance.save()
								#Signal the other views that the manual insertion step has finnished succesfully
								request.session['meta_table'] = True
								#Set a cookie to track the next step's status(manual insertion of multicriteria table)
								request.session['multicriteria_table'] = False
								#Redirect the user to the manual insertion page for the multicriteria table
								return  HttpResponseRedirect('get_multicriteria_table')
				#if the request is get 
				else:
					#Create a criterion formset 
					criterion_formset = CriterionFormSet(prefix='criterion_form')
					#Create an alternative formset
					alternative_formset = AlternativeFormset(prefix='alternative_form')
				#Render the page.Arguments:criterion and alternative formset,form addition flags
				return render(request,'CreateMeta_Table.html',{
															'criterion_formset':criterion_formset,
															'alternative_formset':alternative_formset,
															'change_crit':change_crit,
															'change_alt':change_alt,
															})
			#if this step has alterady finnished
			else:
				#redirect user to the next step's page(manual multicriteria table insertion)
				return redirect(reverse('get_multicriteria_table'))
		#if the decision made on the first step(research creation) was not "manual entry"
		else:
			#Redirect user to the "upload files" page
			return redirect(reverse('get_files'))
	#if a research was not created succesfully 
	else:
		#redirect user to the research creation page
		return redirect(reverse('get_research'))

#Login required to access this view		
@login_required		
#View to handle manual multicriteria table insertion
def get_multicriteria_table(request):
	#Get the user that is logged in
	current_user = request.user
	#Get the last research created by the current user
	current_research = current_user.research_set.last()
	#if a research has been created 
	if request.session.get('research',False):
		#if the decision was manual insertion (in the decision form)
		if request.session.get('decision',None) == 'tables':
			#if the meta table manual insertion step has finnished succesfully
			if request.session.get('meta_table',False):
				#if the multicriteria table is not yet set
				if request.session.get('multicriteria_table',False) == False:
					#Get the criteria of the current research
					criteria = current_research.criterion_set.all()
					#Get the alternatives of the current research
					alternatives = current_research.alternative_set.all()
					#Get the criteria count
					criteria_number = len(criteria)
					#Get the alternatives count
					alternatives_number = len(alternatives)
					#Create a formset template for the multicriteria table cells
					CriterionValueFormset = modelformset_factory(criterionvalue,extra=criteria_number*alternatives_number,fields=('value',),form=CreateCriterionValueForm)
					#List containing all possible permuations of alternatives with the criteria
					altcrit = crit_per_alt(alternatives,criteria)
					#if the request is post
					if request.method == 'POST':
						#Dict to count error's for every column of the multicriteria table
						save_flags = {}
						#Initialize the above mentioned dict(criterion best,worst,number of errors)
						for crit in criteria:
							save_flags.update({crit.criterion_name:[crit.criterion_worst,crit.criterion_best,0]})
						#Create criterion value formset with the post data
						criterion_value_formset = CriterionValueFormset(request.POST,request.FILES,queryset=criterion.objects.none())
						#if the criterion value formset 
						if criterion_value_formset.is_valid():
							#for each permuation and each form in the criterion value formset(parrallel indexing)
							for comp,form in zip(altcrit,criterion_value_formset):
								#if the current form is valid
								if form.is_valid():
									#get a copy of the criterion value object contained in the form
									instance = form.save(commit=False)
									#add the current permuation's alternative to the criterion value object(set the relationship)
									instance.alt = comp[0]
									#add the current permuation's criterion to the criterion value object(set the relationship)
									instance.crit = comp[1]
									#Set the relationship of the criterion value object with the current research
									instance.research = current_research
									##Multicriteria table validation
									#if the criterion monotonicity is ascending and the criterion value is not between worst and best value 
									if instance.crit.criterion_monotonicity == 0 and (instance.value < instance.crit.criterion_worst or instance.value > instance.crit.criterion_best):
										#Raise the current criterion's error counter by one
										save_flags[instance.crit.criterion_name][2]+= 1
										#delete all the criterion value object's of the current research
										criterionvalue.objects.filter(research=current_research).delete()
									#if the criterion monotonicity is descending and the criterion value is not between worst and best value
									elif instance.crit.criterion_monotonicity == 1 and (instance.value > instance.crit.criterion_worst or instance.value < instance.crit.criterion_best):
										#Raise the current criterion's error counter by one
										save_flags[instance.crit.criterion_name][2]+= 1
										#delete all the criterion value object's of the current research
										criterionvalue.objects.filter(research=current_research).delete()
									#if there is no error in the multicriteria table till now 
									elif sum(save_flags[key][2] for key in save_flags.keys()) == 0:
										#save the criterion value object
										instance.save()
										form.save_m2m()
							#for every criterion in the criteria set of the current research
							for key in save_flags.keys():
								#if there is at least one error for this criterion
								if save_flags[key][2] != 0:
									#add the error to the user messages(message framework)
									messages.warning(request,'%s can take values between %f and %f .'%( key ,save_flags[key][0],save_flags[key][1]))
							#if there is no error in the multicriteria table
							if  sum(save_flags[key][2] for key in save_flags.keys()) == 0:
								#Signal the other views that this step has finnished succesfully(manual multicriteria table insertion)
								request.session['multicriteria_table'] = True
								#Redirect the user to the review page of the current research
								return HttpResponseRedirect('review/'+str(current_research.pk))
					#if the request is get
					else:
						#Create a criterion value formset
						criterion_value_formset = CriterionValueFormset(queryset=criterion.objects.none())
					#Render the page.Arguments:the criteria,the alternatives,the criterion value formset and the criteria count
					return render (request,'CreateMulticriteria_Table.html',{
																			'criteria':criteria,
																			'criterion_value_formset':criterion_value_formset,
																			'alternatives':alternatives,
																			'criteria_number':criteria_number,
																			})
				#if this step has already been completed
				else:
					#Delete all the related cookies
					del request.session['multicriteria_table']
					del request.session['meta_table']
					del request.session['research']
					del request.session['decision']
					#Redirect user to the review page of the current research
					return redirect(reverse('review',kwargs={'research_id':current_research.pk,}))
			#if the meta table step is not complete
			else:
				#Redirect user to the manual meta table insertion page
				return redirect(reverse('get_meta_table'))
		#if the decision was not "manual entry"
		else:
			#Redirect user to the "upload files" page
			return redirect(reverse('get_files'))
	#if no research has been created 
	else:
		#Redirect user to the research creation page
		return redirect(reverse('get_research'))

#Login required to access this view			
@login_required
#View to handle the upload of the meta and multicriteria table files
def get_files(request):
	#Get the user that is logged in
	current_user = request.user
	#Get the last research created by the current user
	current_research = current_user.research_set.last()
	#if a research has been created
	if request.session.get('research',False):
		#if the decision in the first step was "upload files"
		if request.session.get('decision',None) == 'files':
			#if there is not file uploaded yet
			if request.session.get('files',False) == False:
				#Get the current research alternatives 
				alternatives = current_research.alternative_set.all()
				#Get the current research criteria
				criteria = current_research.criterion_set.all()
				#if the request is post
				if request.method == 'POST':
					#Create a multicriteria file form with the post data
					multicriteria_file_form = CreateMulticriteriaFile(request.POST,request.FILES)
					#Create a meta file form with the post data
					meta_file_form = CreateMetaFile(request.POST,request.FILES)
					#if the meta file form is valid
					if meta_file_form.is_valid():
						#if the multicriteria file form is valid
						if multicriteria_file_form.is_valid():
							#get a copy of the meta file object in the meta file form
							meta_instance = meta_file_form.save(commit=False)
							#Set relationship with the current research
							meta_instance.research = current_research
							#Save the meta file object
							meta_instance.save()
							#Get the newlly added meta file object
							meta_file = metafile.objects.get(pk=meta_instance.pk)
							#Validate the meta file in the meta file object
							meta_errors = validate_meta_file(current_research)
							#if there is any error in the meta file 
							if meta_errors:
								#Pass the errors as messages to the user
								for error in meta_errors:
									messages.warning(request,error)
								#Delete the meta file object
								meta_file.delete()
							else:
								#get a copy of the multicriteria file object in the multicriteria file form
								multicriteria_instance = multicriteria_file_form.save(commit=False)
								#Set relationship with the current research
								multicriteria_instance.research = current_research
								#Save the multicriteria file object
								multicriteria_instance.save()
								#Get the newlly added multicriteria file object
								multicriteria_file = multicriteriafile.objects.get(pk=multicriteria_instance.pk)
								#Validate the multicriteria file in the multicriteria file object
								multicriteria_errors = validate_multicriteria_file(current_research)
								#if the is any error in the multicriteria file
								if multicriteria_errors:
									#Pass the errors as messages to the user 
									for error in multicriteria_errors:
										messages.warning(request,error)
									#Delete the criteria of the current research
									criteria.delete()
									#Delete the alternatives of the current research 
									alternatives.delete()
									#Delete the multicriteria file of the current research
									multicriteria_file.delete()
									#Delete the meta file of the current research
									meta_file.delete()
								else:
									#Signal the other views that this step has been complteted succesfully
									request.session['files'] = True
									#Refirect the user to the review page of the current research
									return HttpResponseRedirect('review/'+str(current_research.pk))
				else:
					#Create multicriteria file form
					multicriteria_file_form = CreateMulticriteriaFile()
					#Create meta file form
					meta_file_form = CreateMetaFile()
				#Render the page.Arguments:multicriteria,meta file forms
				return render(request,'Create_Files.html',{
														'multicriteria_file_form':multicriteria_file_form,
														'meta_file_form':meta_file_form,
														})
			#if this step is already complete
			else:
				#Delete related cookies
				del request.session['research']
				del request.session['files']
				del request.session['decision']
				#Redirect user to the review page of the current research
				return redirect(reverse('review',kwargs={'research_id':current_research.pk,}))
		#if the decision in the first step was not "upload file"
		else:
			#Redirect user to the manual insertion page of the meta table
			return redirect(reverse('get_meta_table'))
	#if there is no research created
	else:
		#Redirect user to the research creation page
		return redirect(reverse('get_research'))

#Login required to access this view			
@login_required		
#View to handle the review a research(see what is already inserted in the database of the current research).Arguments:research id
def review(request,research_id):
	#Get the user that is logged in
	current_user = request.user
	#Get the research with the specified research id else return 404(if the research does not exist or does not belong to the current user)
	current_research = get_object_or_404(research, pk=research_id,user = current_user.pk)
	#Get the alternatives of the current research
	alternatives = current_research.alternative_set.all()
	#Get the criteria of the current research
	criteria = current_research.criterion_set.all()
	#Get the multicriteria table of the current research(criterion value objects)
	criterionvalues = current_research.criterionvalue_set.all()
	#Get the size of the multicriteria table
	size = len(criterionvalues)
	#Criteria count
	criteria_number = len(criteria)
	#Alternatives count
	alternatives_number = len(alternatives)
	#Create inline formset template based on the criterion model
	CriterionFormSet = inlineformset_factory(research,criterion,extra=0,form=CreateCriterionForm,can_delete=False)
	#Create inline formset template based on the criterion value model
	CriterionValueFormset = inlineformset_factory(research,criterionvalue,extra=0,form=CreateCriterionValueForm,can_delete=False)
	#Create inline formset template based on the alternative model(only the ranking field)
	RankingFormset = inlineformset_factory(research,alternative,extra=0,form=CreateRankingForm,can_delete=False)
	#Get all possible permuations of criteria with alternatives
	altcrit = crit_per_alt(alternatives,criteria)
	#Get the utastar model of the current research
	current_utaobj = current_research.utastar_model_set.last()
	#if the request is post
	if request.method == 'POST':
		#if the save button is clicked
		if 'save' in request.POST:
			#Signal the other views that there has been a change on the current data
			request.session['edit'] = True
			#Set the status of the research as "saved"
			current_research.status = True
			#Save the updated research object
			current_research.save()
			#Create a criterion formset with the post data
			criterion_formset = CriterionFormSet(request.POST, request.FILES,instance=current_research)
			#Create a criterion value formset with post data
			criterion_value_formset = CriterionValueFormset(request.POST,request.FILES,instance=current_research)
			#Create a ranking formset with post data
			ranking_formset = RankingFormset(request.POST,request.FILES,instance=current_research)
			#Create a parameters form(delta,epsilon)
			parameters_form =  CreateParametersForm(request.POST,request.FILES)
			#if the criterion formset is valid
			if criterion_formset.is_valid():
				#for every form in the criterion formset
				for form in criterion_formset:
					#if the current criterion form is valid
					if form.is_valid():
						#Update the criterion object
						form.clean()
						form.save()
				#if the criterion value formset is valid
				if criterion_value_formset.is_valid():
					##Validate multicriteria file(same as above in the get_multicriteria_table view,except there is no object deletion in this version)
					save_flags = {}
					#Fetch the updated research object
					current_research = get_object_or_404(research, pk=research_id,user = current_user.pk)
					criteria = current_research.criterion_set.all()
					for crit in criteria:
						save_flags.update({crit.criterion_name:[crit.criterion_worst,crit.criterion_best,0]})
					for comp,form in zip(altcrit,criterion_value_formset):
						if form.is_valid():
							instance = form.save(commit=False)
							if instance.crit.criterion_monotonicity == 0 and (instance.value < instance.crit.criterion_worst or instance.value > instance.crit.criterion_best):
								save_flags[instance.crit.criterion_name][2]+= 1
							elif instance.crit.criterion_monotonicity == 1 and (instance.value > instance.crit.criterion_worst or instance.value < instance.crit.criterion_best):
								save_flags[instance.crit.criterion_name][2]+= 1
					if sum(save_flags[key][2] for key in save_flags.keys()) == 0:
						criterion_value_formset.save()
					else:
						request.session['edit'] = False
					for key in save_flags.keys():
						if save_flags[key][2] != 0:
							messages.warning(request,'%s can take values between %f and %f .'%( key ,save_flags[key][0],save_flags[key][1]))
					## end multicriteria table validation
					#if the ranking formset is valid
					if ranking_formset.is_valid():
						#Flag to check if ranking formset data is between acceptable values 
						flags = alternatives_number*[0]
						#Flags to check if all the ranking are the same
						same_flag = alternatives_number*[0]
						#For every form in the ranking formset
						for form in ranking_formset:
							#if the current form is valid
							if form.is_valid():
								#get a copy of the ranking field contained in the current ranking form
								instance = form.save(commit=False)
								#Copy the current ranking to the flags list
								same_flag[ranking_formset.forms.index(form)] = instance.ranking
								#if the ranking is not between the logical bounds(1,number of alternatives)
								if not instance.ranking in range(1,alternatives_number+1):
									#Flag the current ranking as out of bounds
									flags[ranking_formset.forms.index(form)] = 1
						#if there is at least one error related with the ranking logical bounds			
						if sum(flags) != 0:
							#Signal other views there has been a change in the data of this page 
							request.session['edit'] = False
							#Pass the error as message to the user
							messages.warning(request,'Ranking must be between %d and %d.'%(1,alternatives_number))
						#if all the rankings are the same 
						elif all(x == same_flag[0] for x in same_flag):
							#Signal other views there has been a change in the data of this page
							request.session['edit'] = False
							#Pass the error as message to the user
							messages.warning(request,'Ranking set must contain at least 2 different values.')
						else:
							#Update the alternative objects contained in the ranking formset
							ranking_formset.save()
						#if the parameters form is valid 
						if parameters_form.is_valid():
								#if the delta and epsilon are in the post data
								if 'delta' in parameters_form.cleaned_data and 'epsilon' in parameters_form.cleaned_data:
									#Set cookies containing the posted parameters 
									request.session['epsilon'] = parameters_form.cleaned_data['epsilon']
									request.session['delta'] = parameters_form.cleaned_data['delta']
							
		#if the analyze button has been clicked
		elif 'analyze' in request.POST:
			#If there is a change in the data of this page 
			if request.session.get('edit',None) == False:
				#Create criterion formset with the post data
				criterion_formset = CriterionFormSet(request.POST, request.FILES,instance=current_research)
				#Create criterion value formset with the post data
				criterion_value_formset = CriterionValueFormset(request.POST,request.FILES,instance=current_research)
				#Create ranking formset with the post data
				ranking_formset = RankingFormset(request.POST,request.FILES,instance=current_research)
				#Create parameters form
				parameters_form = CreateParametersForm(request.POST,request.FILES)
				#Signal the user about the possible erros in the data
				messages.warning(request,'Unresolved errors still exist.Please press the save button in order to be informed about the errors.')
			#if there is not a change in the data of this page
			else:
				#Create criterion formset with the post data
				criterion_formset = CriterionFormSet(request.POST, request.FILES,instance=current_research)
				#Create criterion value formset with the post data
				criterion_value_formset = CriterionValueFormset(request.POST,request.FILES,instance=current_research)
				#Create ranking formset with the post data
				ranking_formset = RankingFormset(request.POST,request.FILES,instance=current_research)
				#Create parameters form
				parameters_form = CreateParametersForm(request.POST,request.FILES)
				#if the parameters form is valid
				if parameters_form.is_valid():
					#if delta and epsilon are in the post data
					if 'delta' in parameters_form.cleaned_data and 'epsilon' in parameters_form.cleaned_data:
						#Set cookies containing the posted parameters 
						request.session['epsilon'] = parameters_form.cleaned_data['epsilon']
						request.session['delta'] = parameters_form.cleaned_data['delta']
						#Redirect user to the results page of the current research 
						return redirect(reverse('results',kwargs={'research_id':current_research.pk,}))
						
	#if request is get
	else:
		#Create criterion formset
		criterion_formset = CriterionFormSet(instance=current_research)
		#Create criterion value formset
		criterion_value_formset = CriterionValueFormset(instance=current_research)
		#Create ranking formset
		ranking_formset = RankingFormset(instance=current_research)
		#if there is utastar model for the current research
		if current_utaobj:
			#Load the parameters from this utastar model
			data = { 
				'delta':current_utaobj.parameters.delta,
				'epsilon':current_utaobj.parameters.epsilon,
			}
			#Create a parameters form using the current utastar model's parameters
			parameters_form = CreateParametersForm(initial=data)
		else:
			#Create a parameters form
			parameters_form = CreateParametersForm()
	#Render the page.Arguments:criterion,criterion value,ranking formsets ,criteria , alternatives ,criteria count 
	return render(request,'Review.html',{
									'criterion_formset':criterion_formset,
									'criterion_value_formset':criterion_value_formset,
									'ranking_formset':ranking_formset,
									'parameters_form':parameters_form,
									'criteria':criteria,
									'alternatives':alternatives,
									'criteria_number':criteria_number,
									})
#Login required to access this view	
@login_required
#View to handle the results of the specified research.Arguments:research id								
def results(request,research_id):
	#Get the user that is logged in
	current_user = request.user
	#Get the research with the specified research id else return 404(if the research does not exist or does not belong to the current user
	current_research = get_object_or_404(research, pk=research_id,user = current_user.pk)
	#Get the alternatives of the current research
	alternatives = current_research.alternative_set.all()
	#Get the criteria of the current research
	criteria = current_research.criterion_set.all()
	#Get the ranking of alternatives(in a list) 
	ranking_list = alternatives.values_list('ranking',flat=True)
	#Get the utastar model of the current research
	current_utaobj = current_research.utastar_model_set.last()
	#if there is a utastar model and there has been a succesfull change in the data
	if current_utaobj and request.session.get('edit',None) == True:
		#Delete previous utastar model object
		current_utaobj.delete()
		#Run utastar 
		utastar_obj = run_utastar(table=multicriteria_to_df(alternatives,criteria,current_research),metatable=meta_to_df(criteria),ranking_list=ranking_list,delta=request.session['delta'],epsilon=request.session['epsilon'])
		#Create a utastar model object
		uobject = utastar_model()
		#Add the utastar model in the utastar model object
		uobject.parameters = utastar_obj
		#Set the relationship with the current research
		uobject.research = current_research
		#Save the utastar model object
		uobject.save()
	#if there is a utastar model and there has been no change in the data
	elif current_utaobj and request.session.get('edit',None) == None: 
		#Load the utastar model
		utastar_obj = current_utaobj.parameters
	#if there is a utastar model and there has been a failed changed in the data
	elif current_utaobj and request.session.get('edit',None) == False:
		#Redirect user back to the review page of the current research in order to correct the errors
		return redirect(reverse('review',kwargs={'research_id':current_research.pk,}))
	#if there is not a utastar model and there has been no change in the data
	else:
		#Run utastar 
		utastar_obj = run_utastar(table=multicriteria_to_df(alternatives,criteria,current_research),metatable=meta_to_df(criteria),ranking_list=ranking_list,delta=request.session['delta'],epsilon=request.session['epsilon'])
		#Create a utastar model object
		uobject = utastar_model()
		#Add the utastar model in the utastar model object
		uobject.parameters = utastar_obj
		#Set the relationship with the current research
		uobject.research = current_research
		#Save the utastar model object
		uobject.save()
	#Create the figures of the utastar model
	img = create_plots(utastar_obj,current_research)
	#Get the model weights from the current utastar model
	model_weights = pd.Series(utastar_obj.model_weights_post).to_frame('Model Weights')
	#Get the global utilities from the current utastar model
	global_utilities = pd.Series(utastar_obj.global_utilities_post).to_frame('Global Utilities')
	#Get the partial utilities of the current utastar model
	marginals=[]
	for crit in utastar_obj.criteria:
		marginals.append(pd.Series(utastar_obj.marginal_post[crit]))
	partial_utilities=pd.DataFrame(marginals)
	partial_utilities=partial_utilities.fillna('-')
	partial_utilities.insert(0,'Criteria / intervals',utastar_obj.criteria)
	partial_utilities.reset_index()
	#Create the csv files to be exported
	csvs = create_csv(model_weights,global_utilities,partial_utilities)
	#Create the http responses for the the csv export buttons
	csv_mw = HttpResponse (csvs['model_weights'], content_type='text/csv')
	csv_gu = HttpResponse (csvs['global_utilities'], content_type='text/csv')
	csv_pu = HttpResponse (csvs['partial_utilities'], content_type='text/csv')
	#Add file names to the http responses for the csv files
	csv_mw['Content-Disposition'] = 'attachment; filename="model_weights_%s.csv"'%(current_research.pk)
	csv_gu['Content-Disposition'] = 'attachment; filename="global_utilities_%s.csv"'%(current_research.pk)
	csv_pu['Content-Disposition'] = 'attachment; filename="partial_utilities_%s.csv"'%(current_research.pk)
	#if the request is post
	if request.method == 'POST':
		#if the export button for global utilities is clicked
		if 'export_gu' in request.POST:
			#export global utilities csv file
			return csv_gu
		#if the export button for model weights is clicked
		elif 'export_mw' in request.POST:
			#export model weights csv file
			return csv_mw
		#if the export button for the partial utilities is clicked
		elif 'export_pu' in request.POST:
			#export partial utilities csv file
			return csv_pu
	#if the request is get 
	else:
		#Render the page.Arguments:utastar model figures encoded in base64,model weights html table,global utilities html table,partial utilities html table,multicriteria html table,meta html table
		return render(request,'Results.html',{
										'img':img,
										'model_weights':model_weights.to_html(classes=['table-striped','table-responsive']),
										'global_utilities':global_utilities.to_html(classes=['table-striped','table-responsive']),
										'partial_utilities':partial_utilities.to_html(index=False,classes=['table-striped','table-responsive']),
										'table':utastar_obj.table.to_html(index=False,classes=['table-striped','table-responsive']),
										'metatable':utastar_obj.metatable.to_html(index=False,classes=['table-striped','table-responsive']),
										})
#Login required to access this view
@login_required
#Main page view
def index(request):
	#Get the user that is logged in
	current_user = request.user
	#Get all the saved researches of the current user
	research_set = research.objects.filter(user=current_user.pk,status=True)
	#if the request is post
	if request.method == 'POST':
		#Get the value from all the delete buttons
		delete_buttons = [int(key.replace('delete_','')) for key in request.POST if 'delete_' in key]
		#if at least a delete button is clicked
		if delete_buttons:
			#Delete the researches whose delete buttons have been clicked
			research_set.filter(pk__in=delete_buttons).delete()
			#Fetch the new research set of the current user
			research_set = research.objects.filter(user=current_user.pk,status=True)
		#if the add research button is clicked
		if 'add_research' in request.POST:
			#Redirect user to the research creation page
			return redirect(reverse('get_research'))
	#Render the page.Arguments:user's saved research set
	return render(request,'Index.html',{
									'research_set':research_set,
									})

#View that handles the platform's about page									
def about(request):
	#Render the static about page
	return render(request,'About.html')