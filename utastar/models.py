#!/usr/bin/python
# -*- coding: utf-8 -*-
#imports
from django.db import models
from django import forms
from django.core.exceptions import ValidationError
import os
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.utils.timezone import now
from picklefield.fields import PickledObjectField

class research(models.Model): #Defining research model 
	#Model research has 4 model fields
	user = models.ForeignKey(User) #relate research model with User model
	name = models.CharField(max_length = 200,verbose_name='Research Name') # field for research name
	date_created = models.DateTimeField(default=now()) #field for date research started
	status = models.BooleanField(default=False)
	def __str__(self):
		return self.name

class criterion(models.Model): #Criterion model with fields name,type,monotonicity,worst,best,a
	quantity = 0
	quality = 1
	ascending = 0
	descending = 1
	two = 2
	three = 3
	four = 4
	five = 5
	six = 6
	seven = 7
	eight = 8
	nine = 9
	ten = 10
	#available choices for each field
	type_choices = (
		(quantity,'Quantitative'), # for Quantitive choice number 0 is saved on database field
		(quality,'Qualitative'),
		)
	monotonicity_choices = (
		(ascending,'Ascending'),
		(descending,'Descending'),
		)
	a_choices = (
		(two,'Second Grade(a = 2)'),
		(three,'Third Grade(a = 3)'),
		(four,'Forth Grade(a = 4)'),
		(five,'Fifth Grade(a = 5)'),
		(six,'Sixth Grade(a = 6)'),
		(seven,'Seventh Grade(a = 7)'),
		(eight,'Eighth Grade(a = 8)'),
		(nine,'Ninth Grade(a = 9)'),
		(ten,'Tenth Grade(a = 10)'),
		)
	criterion_research = models.ForeignKey('research', on_delete=models.CASCADE,null=True) #relate criterion model with research model (In which research does a criterion belong to)
	criterion_name = models.CharField(max_length = 200,verbose_name='Name')
	criterion_type = models.IntegerField(choices = type_choices , default = quantity,verbose_name='Type') #available choices and default value
	criterion_monotonicity = models.IntegerField(choices = monotonicity_choices , default = ascending,verbose_name='Monotonicity')#This field saves only integer values
	criterion_a = models.IntegerField(choices = a_choices , default = five,verbose_name='Scale',help_text='Select one of the ten scales available.')
	criterion_worst = models.FloatField(default=' ',verbose_name='Worst Value',help_text='Type the worst value the criterion can take.',blank=True)
	criterion_best = models.FloatField(default=' ',verbose_name='Best Value',help_text='Type the best value the criterion can take.',blank=True)
	def __str__(self):
		return self.criterion_name
    
class alternative(models.Model): # Model to save alternative names and ranking 
    name = models.CharField(default=' ',max_length = 200,verbose_name='Name')
    ranking = models.IntegerField(default=1)
    alternative_research = models.ForeignKey('research', on_delete=models.CASCADE) #relate to research model
    criteria = models.ManyToManyField('criterion', through='criterionvalue',blank=True) #many to many relation with criterion model through criterionvalue model
    def __str__(self):
        return self.name

class criterionvalue(models.Model): #model to save values of each criterion for each alternative
	value = models.FloatField(default=0)
	alt = models.ForeignKey('alternative',on_delete=models.CASCADE,null=True) #relate to alternative model
	crit = models.ForeignKey('criterion',on_delete=models.CASCADE,null=True)#relate to criterion model
	research = models.ForeignKey('research',on_delete=models.CASCADE,null=True)#relate to research model

def handle_multicriteria_file(instance, filename): #function necessary for uploading multicriteria file
	ext = filename.split('.')[-1]
	filename = "multicriteria_%s.%s" % (instance.research.pk,ext)
	return  'user_{0}/input/multicriteria/{1}'.format(instance.research.user.pk, filename)
	
def handle_meta_file(instance, filename):# function necessary for uploading meta file
	ext = filename.split('.')[-1]
	filename = "meta_%s.%s" % (instance.research.pk,ext)
	return 'user_{0}/input/meta/{1}'.format(instance.research.user.pk, filename)

def handle_gup_file(instance, filename):#function for saving global utilities to a file
	ext = 'png'
	filename = "global_utilities_post_%s.%s" % (instance.research.pk,ext)
	relative_path = 'user_{0}/results/gup/{1}'.format(instance.research.user.pk, filename)
	absolute_path = os.path.join(settings.MEDIA_ROOT,relative_path)
	if os.path.isfile(absolute_path) :
		os.remove(absolute_path)
	return  relative_path #returns a path showing where the file is
	
def handle_mwp_file(instance, filename): #function for saving model weights to a file
	ext = 'png'
	filename = "model_weights_post_%s.%s" % (instance.research.pk,ext)
	relative_path = 'user_{0}/results/mwp/{1}'.format(instance.research.user.pk, filename)
	absolute_path = os.path.join(settings.MEDIA_ROOT,relative_path)
	if os.path.isfile(absolute_path) :
		os.remove(absolute_path)
	return  relative_path
def handle_mp_file(instance, filename): #function for saving marginal utilities to a file
	ext = 'png'
	filename = "marginal_post_%s.%s" % (instance.research.pk,ext)
	relative_path = 'user_{0}/results/mp/{1}'.format(instance.research.user.pk, filename)
	absolute_path = os.path.join(settings.MEDIA_ROOT,relative_path)
	if os.path.isfile(absolute_path) :
		os.remove(absolute_path)
	return  relative_path
	
class metafile(models.Model): #model to save uploaded meta file
	research = models.ForeignKey('research',on_delete=models.CASCADE,null=True)
	meta_file = models.FileField(upload_to=handle_meta_file)
	def delete(self, *args, **kwargs):
		os.remove(os.path.join(settings.MEDIA_ROOT, self.meta_file.name))
		super(metafile,self).delete(*args,**kwargs)
	def __str__(self):
		return self.meta_file.name	
		
class multicriteriafile(models.Model): #model to save uploaded multicriteria file
	research = models.ForeignKey('research',on_delete=models.CASCADE,null=True)
	multicriteria_file = models.FileField(upload_to=handle_multicriteria_file)
	def delete(self, *args, **kwargs):
		os.remove(os.path.join(settings.MEDIA_ROOT, self.multicriteria_file.name))
		super(multicriteriafile,self).delete(*args,**kwargs)
	def __str__(self):
		return self.multicriteria_file.name
#models to save global utilities,marginal utilities and criterion weights graphs accordingly		
class global_utilities_image(models.Model):
	research = models.ForeignKey('research',on_delete=models.CASCADE,null=True)
	global_utilities_post =  models.ImageField(upload_to=handle_gup_file)
	def delete(self, *args, **kwargs):
		os.remove(os.path.join(settings.MEDIA_ROOT, self.global_utilities_post.name))
		super(global_utilities_image,self).delete(*args,**kwargs)
	def __str__(self):
		return 'global_utilities_image_' + str(self.research.pk)
class weights_image(models.Model):
	research = models.ForeignKey('research',on_delete=models.CASCADE,null=True)
	model_weights_post =  models.ImageField(upload_to=handle_mwp_file)
	def delete(self, *args, **kwargs):
		os.remove(os.path.join(settings.MEDIA_ROOT, self.model_weights_post.name))
		super(weights_image,self).delete(*args,**kwargs)
	def __str__(self):
		return 'weights_image_' + str(self.research.pk)
class marginal_image(models.Model):
	research = models.ForeignKey('research',on_delete=models.CASCADE,null=True)
	marginal_post = models.ImageField(upload_to=handle_mp_file)
	def delete(self, *args, **kwargs):
		os.remove(os.path.join(settings.MEDIA_ROOT, self.marginal_post.name))
		super(marginal_image,self).delete(*args,**kwargs)
	def __str__(self):
		return 'marginal_image_' + str(self.research.pk)

#Model to save the utastar model of each research		
class utastar_model(models.Model):
		research = models.ForeignKey('research',on_delete=models.CASCADE,null=True)
		parameters = PickledObjectField()