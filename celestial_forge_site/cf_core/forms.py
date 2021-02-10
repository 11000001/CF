from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import *

class UserCreationForm(UserCreationForm):
	email = forms.EmailField(required=False)

	class Meta:
		model = User
		fields = ("username", "email", "password1", "password2")

	def save(self, commit=True):
		user = super(UserCreationForm, self).save(commit=False)
		user.email = self.cleaned_data["email"]
		if commit:
			user.save()
		return user

class DelForm (forms.Form):
	to_delete = forms.RegexField(label='(Hide)', regex="(\d+;)*", initial="", required=False, widget=forms.HiddenInput())

class PerkForm (forms.ModelForm):
	
	class Meta:
		model = Perk
		fields = ['name', 'description', 'cost', 'source', 'domain', 'prereq_perks', 'prereq_addons','url_wikipedia','url_youtube','background', 'last_editor']
		widgets = {
			'url_wikipedia': forms.URLInput(attrs={'placeholder': 'Wikipedia URL'}),
			'url_youtube': forms.URLInput(attrs={'placeholder': 'Youtube URL'})
		}

class AddonForm (forms.ModelForm):
	
	class Meta:
		model = Addon
		fields = ['name', 'description', 'cost', 'prereq_perks', 'prereq_addons']


class DomainForm (forms.ModelForm):
	
	class Meta:
		model = Domain
		fields = ['name']

class SourceForm (forms.ModelForm):
	
	class Meta:
		model = Source
		fields = ['name','url_wikipedia']
		widgets = {
			'name': forms.TextInput(attrs={'placeholder': 'Name'}),
			'url_wikipedia': forms.URLInput(attrs={'placeholder': 'Wikipedia URL'})
		}
		
class SelectionDropForm(forms.Form):
	DOMAIN_CHOICES = [('random','Random'),('seq','Sequential')]
	PERK_CHOICES = [('max', 'Maximum'),('random','Random'),('random_affordable','Affordable')]
	ADDON_CHOICES = [('max', 'Maximum'),('random','Random'),('random_affordable','Affordable')]
	CP_CHOICES = [('fixed','Fixed'),('random','Random')]
	
	
	domain_method = forms.ChoiceField(label='Domain', help_text="Choose a method for selecting the domain that new perks will be drawn from.", choices=DOMAIN_CHOICES, widget=forms.RadioSelect, initial="random")
	perk_method = forms.ChoiceField(label='Perk', help_text="Choose a method for selecting perks.", choices=PERK_CHOICES, widget=forms.RadioSelect)
	addon_method = forms.ChoiceField(label='Addon', help_text="Choose a method for selecting addons.", choices=ADDON_CHOICES, widget=forms.RadioSelect)
	cp_method = forms.ChoiceField(label='CP', help_text="Choose a method for gaining CP.", choices=CP_CHOICES, widget=forms.RadioSelect)
	cp_fixed_value = forms.RegexField(label='CP [Fixed]', regex="\d+", initial="100", required=False)
	cp_random_value = forms.RegexField(label='CP [Random]', regex="(\d+\-\d+)|\d+", initial="0-100", required=False)
	open_settings = forms.RegexField(label='CP - hide', regex="[10]", initial="0", required=False, widget=forms.HiddenInput())

	def clean(self):
		cp_method = self.cleaned_data.get('cp_method')
		if (cp_method == 'fixed' and self.cleaned_data.get('cp_fixed_value') == '') or (cp_method == 'random' and self.cleaned_data.get('cp_random_value') == ''):
			raise ValidationError("You must specify a value along with a CP method.")
		return self.cleaned_data