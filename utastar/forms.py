#!/usr/bin/python
# -*- coding: utf-8 -*-
from django import forms
from django.forms import ModelForm
from .models import criterion,research,alternative,criterionvalue,multicriteriafile,metafile
from django.forms.extras.widgets import SelectDateWidget 
from django.utils.timezone import localtime, now
from django.contrib.admin import widgets
#Modelfrom with research attributes
class CreateResearchForm(ModelForm):
	class Meta:
		model = research
		fields = ('name',)

#Modelform with criterion attributes		
class CreateCriterionForm(ModelForm):
	class Meta:
		model = criterion
		fields = ('criterion_name','criterion_type','criterion_monotonicity','criterion_a','criterion_worst','criterion_best')

	def clean_criterion_worst(self):
		if 'criterion_worst' in self.cleaned_data:
			criterion_worst = self.cleaned_data['criterion_worst']
			#check if criterion attributes are in the form passed
			if 'criterion_type' in self.cleaned_data and 'criterion_monotonicity' in self.cleaned_data and 'criterion_a' in self.cleaned_data:
				criterion_type = self.cleaned_data['criterion_type']
				criterion_monotonicity = self.cleaned_data['criterion_monotonicity']
				criterion_a = self.cleaned_data['criterion_a']
				if criterion_type == 1 and criterion_monotonicity == 0:#f criterion is qualitive and ascending
					criterion_worst = 1
				elif criterion_type == 1 and criterion_monotonicity == 1:#f criterion is qualitive and descending
					criterion_worst = criterion_a
				elif criterion_worst < 0 and criterion_worst != None:#f criterion worst is a non positive number
					raise forms.ValidationError("Criterion's Worst Value must be a positive number.")
				elif criterion_worst == None:#if no criterion worst value is given
					raise forms.ValidationError("This field is required.")
			return criterion_worst
	
	def clean_criterion_best(self):
		if 'criterion_best' in self.cleaned_data:
			criterion_best = self.cleaned_data['criterion_best']
			if 'criterion_type' in self.cleaned_data and 'criterion_monotonicity' in self.cleaned_data and 'criterion_a' in self.cleaned_data and 'criterion_worst' in self.cleaned_data:
				criterion_type = self.cleaned_data['criterion_type']
				criterion_monotonicity = self.cleaned_data['criterion_monotonicity']
				criterion_a = self.cleaned_data['criterion_a']
				criterion_worst = self.cleaned_data['criterion_worst']
				if criterion_type == 1 and criterion_monotonicity == 0:#if criterion is qualitive and ascending then criterion_a value is criterion best value
					criterion_best = criterion_a
				elif criterion_type == 1 and criterion_monotonicity == 1:#if criterion is qualitive and descending then set criterion best as 1
					criterion_best = 1
				elif criterion_type == 0 and criterion_monotonicity == 0:#if criterion is quantitive and ascending
					if criterion_best < 0 and criterion_best != None:#Raise error if criterion's best value given is a non positive number
						raise forms.ValidationError("Criterion's Best Value must be a positive number.")
					elif criterion_worst > criterion_best:#Raise error if a criterion's worst value is greater than best for an ascending criterion
						raise forms.ValidationError("Criterion Best value must be greater than Worst value(ascending).")
				elif criterion_type == 0 and criterion_monotonicity == 1:
					if criterion_best < 0 and criterion_best != None:
						raise forms.ValidationError("Criterion's Best Value must be a positive number.")
					elif criterion_worst < criterion_best:
						raise forms.ValidationError("Criterion Best value can't be greater than Worst value(descending).")
				elif criterion_best == None:#Raise error if a criterion's best value is greater than worst for a descending criterion
					raise forms.ValidationError("This field is required.")
			return criterion_best

class CreateAlternativeForm(ModelForm):#Modelform of alternatives names
	class Meta:
		model = alternative
		fields = ('name',)
			
class CreateCriterionValueForm(ModelForm):#Modelform of criterion values
	class Meta:
		model = criterionvalue
		fields = ('value',)
		
class CreateMulticriteriaFile(ModelForm):#Modelform for uploading mutlicriteria file
	class Meta:
		model = multicriteriafile
		fields = ('multicriteria_file',)
		
class CreateMetaFile(ModelForm):#Modelform for uploading meta file
	class Meta:
		model = metafile
		fields = ('meta_file',)
		
		
class Decision(forms.Form):#Form for either filling multicriteria table manually or uploading file
	file = 1
	table = 0
	choices = (
				(file,'Upload Files'),
				(table,'Fill out tables manually'),
				)
	decision = forms.ChoiceField(choices=choices,initial=table,label='Select input method :')

class CreateRankingForm(ModelForm):#Modelform for ranking of alternatives
	class Meta:
		model = alternative
		fields = ('ranking',)

class CreateParametersForm(forms.Form):#form for delta and epsilon parameters of utastar
		delta = forms.FloatField(initial='0.001',label='Delta')
		epsilon = forms.FloatField(initial='0.0001',label='Epsilon')
		def clean_delta(self):
			if 'delta' in self.cleaned_data:
				delta = self.cleaned_data['delta']
				if delta == None:#check if a delta value has been given
					raise forms.ValidationError("This field is required.")
				elif delta < 0:
					raise forms.ValidationError("Delta must be a positive number.")
				else:
					return delta
		def clean_epsilon(self):
			if 'epsilon' in self.cleaned_data:
				epsilon = self.cleaned_data['epsilon']
				if epsilon == None:#check if a epsilon value has been given
					raise forms.ValidationError("This field is required.")
				elif epsilon < 0:
					raise forms.ValidationError("Epsilon must be a positive number.")
				else:
					return epsilon
		