from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .forms import *
from .functions import *
from .models import *

def logout_view(request):
	logout(request)
	return HttpResponseRedirect(reverse('logout'))

@login_required
def index(request):
	if request.method == 'POST':
		for id in [x for x in request.POST['to_delete'].split(';') if x]:
			request.user.runs.get(pk=int(id)).delete()
		return redirect(reverse('index'))
	context = {}
	form = DelForm()
	context['form'] = form
	context['runs'] = request.user.runs.order_by('-last_update')
	return render(request, "cf_core/index.html", context)

def new_account(request):
	if request.method == 'POST':
		form = UserCreationForm(request.POST)
		if form.is_valid():
			form.save()
			username = form.cleaned_data.get('username')
			raw_password = form.cleaned_data.get('password1')
			user = authenticate(username=username, password=raw_password)
			login(request, user)
			return redirect(reverse('index'))
	else:
		form = UserCreationForm()
	return render(request, 'cf_core/new_account.html', {'form': form})

@login_required
def new_perk(request):
	addon_limit = 10
	context = {'addon_limit':addon_limit}
	context['page_title'] = 'Create a New Perk'
	if request.method == 'POST':
		context['domain_form'] = DomainForm(request.POST, prefix="domain_form")
		context['source_form'] = SourceForm(request.POST, prefix="source_form")
		# List of triples: 1 - Form, 2- Prereq numbers to be displayed, 3- Checked prereq numbers
		context['addon_form_list'] = [ [AddonForm(request.POST, prefix="addon_form_"+str(i)), range(i), []] for i in range(addon_limit) ]
		# Check for new domain/source; if they exist, record for later update
		updated_request = request.POST.copy()
		if context['domain_form'].is_valid():
			new_domain = context['domain_form'].save()
			updated_request.update({'perk_form-domain': new_domain})
		if context['source_form'].is_valid():
			new_source = context['source_form'].save()
			updated_request.update({'perk_form-source': new_source})
		context['perk_form'] = PerkForm(updated_request, request.FILES, prefix="perk_form")
		# Check the resulting perk form and all addon forms for validity
		valid = context['perk_form'].is_valid()
		# Track the last addon form with input
		last = -1
		i = 0
		for addon_triple in context['addon_form_list']:
			addon_triple[2]=request.POST.getlist('self_prereqs_for_addon_'+str(i), [])
			# Form is valid
			if addon_triple[0].is_valid():
				last = i
			# Form is invalid (empty or bad input)
			else:
				# Form is empty
				if addon_triple[0]['name'].value() == '' and addon_triple[0]['cost'].value() == '' and addon_triple[0]['description'].value() == '':
					# Reset form to erase error messages
					addon_triple[0] = AddonForm(prefix="addon_form_"+str(len(addon_triple[1])))
				# Form has bad input 
				else:
					valid = False
					last = i
			i += 1
		# Perk form is valid and every Addon form is either valid or empty
		if valid:
			new_perk = context['perk_form'].save()
			one_step_close_prereq(new_perk)
			i = 0
			while i <= last:
				new_addon = context['addon_form_list'][i][0].save()
				new_addon.prereq_perks.add(new_perk)
				one_step_close_prereq(new_addon)
				i += 1
			return redirect(reverse('index'))
		# Included so the template knows which addons to display
		context['last_addon_index'] = last
	else:
		context['perk_form'] = PerkForm(prefix="perk_form")
		context['domain_form'] = DomainForm(prefix="domain_form")
		context['source_form'] = SourceForm(prefix="source_form")
		context['addon_form_list'] = [ [AddonForm(prefix="addon_form_"+str(i)), range(i), []] for i in range(addon_limit) ]
		context['last_addon_index'] = -1
	return render(request, 'cf_core/new_perk.html', context)


@login_required
def edit_perk(request, perk_id):
	close_all_prereqs ()
	addon_limit = 10
	context = {'addon_limit':addon_limit}
	context['page_title'] = 'Edit Perk'
	perk = get_object_or_404(Perk,pk=perk_id)
	#POST
	if request.method == 'POST':
		context['domain_form'] = DomainForm(request.POST, prefix="domain_form")
		context['source_form'] = SourceForm(request.POST, prefix="source_form")
		# List of triples: 1 - Form, 2- Prereq numbers to be displayed, 3- Checked prereq numbers
		context['addon_form_list'] = [ [AddonForm(request.POST, prefix="addon_form_"+str(i)), range(i), []] for i in range(addon_limit) ]
		# Check for new domain/source; if they exist, record for later update
		updated_request = request.POST.copy()
		if context['domain_form'].is_valid():
			new_domain = context['domain_form'].save()
			updated_request.update({'perk_form-domain': new_domain})
		if context['source_form'].is_valid():
			new_source = context['source_form'].save()
			updated_request.update({'perk_form-source': new_source})
		context['perk_form'] = PerkForm(updated_request, request.FILES, prefix="perk_form")
		# Check the resulting perk form and all addon forms for validity
		valid = context['perk_form'].is_valid()
		# Track the last addon form with input
		last = -1
		i = 0
		for addon_triple in context['addon_form_list']:
			addon_triple[2]=request.POST.getlist('self_prereqs_for_addon_'+str(i), [])
			# Form is valid
			if addon_triple[0].is_valid():
				last = i
			# Form is invalid (empty or bad input)
			else:
				# Form is empty
				if addon_triple[0]['name'].value() == '' and addon_triple[0]['cost'].value() == '' and addon_triple[0]['description'].value() == '':
					# Reset form to erase error messages
					addon_triple[0] = AddonForm(prefix="addon_form_"+str(len(addon_triple[1])))
				# Form has bad input 
				else:
					valid = False
					last = i
			i += 1
		# Perk form is valid and every Addon form is either valid or empty
		if valid:
			# Save previous version if necessary
			if datetime.date.today() - perk.previous_versions.latest('created') > timedelta(days=7):
				newVersion=Version(perk=perk, json=serializers.serialize('json', perk), editor=request.user)
				i = 0
				while i <= last:
					newVersion.json += serializers.serialize('json', perk)
					i += 1
			# Update live perk to new input
			new_perk = context['perk_form'].save()
			one_step_close_prereq(new_perk)
			i = 0
			while i <= last:
				new_addon = context['addon_form_list'][i][0].save()
				new_addon.prereq_perks.add(new_perk)
				one_step_close_prereq(new_addon)
				i += 1
			return redirect(reverse('index'))
		# Included so the template knows which addons to display
		context['last_addon_index'] = last
	# GET
	else:
		context['perk_form'] = PerkForm(instance=perk, prefix="perk_form")
		context['domain_form'] = DomainForm(prefix="domain_form")
		context['source_form'] = SourceForm(prefix="source_form")
		context['addon_form_list'] = [ [AddonForm(prefix="addon_form_"+str(i)), range(i), []] for i in range(addon_limit) ]
		# Populate addon forms with previous data
		i = 0
		for addon in order_addons(perk.addon_set.all()):
			context['addon_form_list'][i][0] = AddonForm(instance=addon, prefix="addon_form_"+str(i))
			# Set prereqs for addons within this perk
			ii = 0
			while ii < i:
				if perk.addon_set.all()[ii] in addon.prereq_addons.all():
					context['addon_form_list'][i][2].append(str(ii))
				ii += 1
			i += 1
		context['last_addon_index'] = i-1
	return render(request, 'cf_core/new_perk.html', context)

# TO DO:
# email sending
# cardbacks/links

# Error on first submit doesn't show as error

# add most recent roll selections to run model?
# menu open not working in general
# check that youtube and wikipedia links are in fact youtube and wikipedia links
# don't show link buttons unless they exist
# Scrolling cards doesn't work?

# create indices for database
# editperk and newperk is really slow
# perk cards have edge clippling on left side
# commas for CP
# drop brackets for CP on cards?
# improve str output for some models

@login_required
def new_run(request):
	run = Run(owner=request.user, forge = Forge.objects.get(pk=1))
	run.save()
	return HttpResponseRedirect(reverse('run', kwargs={'run_id':run.id}))

@login_required
def run(request, run_id):
	context = {}
	run = get_object_or_404(Run,pk=run_id)
	context['run_id'] = run.id
	if run.name:
		context['run_name'] = run.name
	else:
		context['run_name'] = "Run #"+str(run.id)
	context['run'] = run.attempts.order_by('number')
	if request.method == 'POST':
		form = SelectionDropForm (request.POST)
		if form.is_valid():
			CP = update_CP(run.get_current_cp(), CP_method=form.cleaned_data['cp_method'], value=form.cleaned_data['cp_'+form.cleaned_data['cp_method']+'_value'])
			success = select(run, CP, domain_method=form.cleaned_data['domain_method'], perk_method=form.cleaned_data['perk_method'], addon_method=form.cleaned_data['addon_method'])
		# Save most recent form selections to session
		for k,v in request.POST.items():
			if k in {'domain_method', 'perk_method', 'addon_method', 'cp_method', 'cp_fixed_value', 'cp_random_value', 'open_settings'}:
				request.session[k] = v
		return HttpResponseRedirect(reverse('run', kwargs={'run_id':run_id}))
	else:
		# set text input to default if empty?
		# If not a new run and saved info, set form info off session
		if run.attempts.exists() and 'domain_method' in request.session:
			form = SelectionDropForm(request.session)
		else:
			form = SelectionDropForm()
	context['CP'] = run.get_current_cp()
	context['form']=form
	return render(request, "cf_core/run.html", context)