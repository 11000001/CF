import random
from .models import *

def random_domain (run):
	'''
	Returns a random domain.
	'''
	domains = Domain.objects.all()
	return domains[random.randint(0, domains.count()-1)]

def seq_domain (run):
	'''
	Returns the next domain.
	'''
	domains = Domain.objects.all().order_by('id')
	latest = run.attempts.order_by('-number').first()
	if latest == None or latest.domain == domains.last():
		return domains.first()
	i = 0
	for domain in domains:
		if domain.id == latest.domain.id:
			return domains[i+1]
		i+=1

def random_perk (run, domain, CP):
	'''
	Returns a random unlocked perk from the domain <domain>.
	'''
	perks = domain.perk_set.all()
	perk = perks[random.randint(0, perks.count()-1)]
	while run.attempts.filter(perk=perk, locked=True).exists():
		perks = perks.exclude(id=perk.id)
		if perks:
			perk = perks[random.randint(0, perks.count()-1)]
		else:
			return None
	return perk


def max_perk (run, domain, CP):
	'''
	Returns the most expensive unlocked affordable perk in the domain, breaking ties randomly.  Returns <None> if no such perk exists.
	'''
	perks = domain.perk_set.all().order_by('-cost')
	max_list = []
	for perk in perks:
		if perk.cost <= CP and (max_list == [] or max_list[0].cost == perk.cost) and not run.attempts.filter(perk=perk, locked=True).exists():
			max_list.append(perk)
	if max_list == []:
		return None
	return max_list[random.randint(0, len(max_list)-1)]


def random_affordable_perk (run, domain, CP):
	'''
	Returns a random unlocked affordable perk in the domain.
	'''
	perks = domain.perk_set.all().order_by('-cost')
	affordable_list = []
	for perk in perks:
		if perk.cost <= CP and not run.attempts.filter(perk=perk, locked=True).exists():
			affordable_list.append(perk)
	if affordable_list == []:
		return None
	return affordable_list[random.randint(0, len(affordable_list)-1)]

def random_addon (run, perk, CP):
	'''
	Returns a pair of a random list of unlocked addons from the perk <perk> and their total cost. Returns <None> if no such list exists.
	'''
	addons = perk.addon_set.all()
	options = []
	for addon in addons:
		# if unlocked
		if not run.attempts.filter(perk=perk, locked=True, addons__id=addon.id).exists():
			total_cost = addon.cost
			option = [addon]
			# Add other addons from this perk required by this one
			for prereq_addon in addon.prereq_addons.all():
				if prereq_addon.perk == perk and not run.attempts.filter(perk=perk, locked=True, addons__id=prereq_addon.id).exists():
					option.append(prereq_addon)
					total_cost += prereq_addon.cost
			options.append((option,total_cost))
	if options == []:
		return None
	return options[random.randint(0, len(options)-1)]

def random_affordable_addon (run, perk, CP):
	'''
	Returns a pair of a random list of unlocked addons from the perk <perk> whose cumulative cost can be afforded and this total cost.  Returns <None> if no such list exists.
	'''
	addons = perk.addon_set.all()
	affordable_list = []
	for addon in addons:
		# if unlocked
		if not run.attempts.filter(perk=perk, locked=True, addons__id=addon.id).exists():
			total_cost = addon.cost
			option = [addon]
			# Add other addons from this perk required by this one
			for prereq_addon in addon.prereq_addons.all():
				if prereq_addon.perk == perk and not run.attempts.filter(perk=perk, locked=True, addons__id=prereq_addon.id).exists():
					total_cost += prereq_addon.cost
					option.append(prereq_addon)
				if total_cost > CP:
					break
			if total_cost <= CP:
				affordable_list.append((option, total_cost))
	if affordable_list == []:
		return None
	return affordable_list[random.randint(0, len(affordable_list)-1)]

def prereqs_satisfied (run, prereq_perks, prereq_addons):
	'''
	Checks that all <prereq_perks> and <prereq_addons> have already been locked in <run>, returning <True> if they have and <False> otherwise.
	'''
	for prereq_perk in prereq_perks.all():
		if not run.attempts.filter(perk=prereq_perk, locked=True).exists():
			return False
	for prereq_addon in prereq_addons.all():
		if not run.attempts.filter(addons__id=prereq_addon.id, locked=True).exists():
			return False
	return True

def select (run, CP, domain_method="random", perk_method="random", addon_method="random_affordable", timeout=100):
	'''
	Select domain, perk, and possibly addons according to the specified methods, updating <run> accordingly.  Return True if perk locked and False otherwise.
	'''
	if timeout == 0:
		raise ValueError("Timeout: No acceptable perk found.")
		return None
	# Exec doesn't allow direct modification of local variables, so pass an explicit dictionary and then modify
	ldict = {'run':run, 'CP':CP}
	exec("domain = "+domain_method+"_domain(run)",globals(),ldict)
	domain = ldict['domain']
	exec("perk = "+perk_method+"_perk(run,domain,CP)",globals(),ldict)
	perk = ldict['perk']
	# No perk found; retry?
	if perk == None:
		return select(run, CP, domain_method, perk_method, addon_method, timeout-1)
	# Can't afford perk or prereqs not satisfied
	elif CP < perk.cost or not prereqs_satisfied(run, perk.prereq_perks, perk.prereq_addons):
		a=Attempt(domain=domain, perk=perk, cp=CP, locked=False, run=run, number=run.get_current_number()+1)
		a.save()
		return False
	# Can afford perk
	else:
		CP -= perk.cost
		# Handle possible addons
		exec("addon_pair = "+addon_method+"_addon(run, perk, CP)",globals(),ldict)
		addon_pair = ldict['addon_pair']
		# Exists and can afford
		if addon_pair is not None and addon_pair[1]<=CP:
			for addon in addon_pair[0]:
				#Prereq failure; no addons
				if not prereqs_satisfied(run, addon.prereq_perks, addon.prereq_addons.exclude(perk=perk)):
					Attempt(domain=domain, perk=perk, cp=CP, locked=True, run=run, number=run.get_current_number()+1)
					a.save()
					return True
			a=Attempt(domain=domain, perk=perk, cp=CP-addon_pair[1], locked=True, run=run, number=run.get_current_number()+1)
			for addon in addon_pair[0]:
				a.addons.add(addon)
			a.save()
			return True
		# Not found or too costly; no addons
		else:
			a=Attempt(domain=domain, perk=perk, cp=CP, locked=True, run=run, number=run.get_current_number()+1)
			a.save()
			return True

def fixed_CP(value):
	try:
		return int(value)
	except ValueError:
		return None

def random_CP(value):
	if '-' in value:
		value = value.split('-')
		try:
			return random.randint(int(value[0]),int(value[1]))
		except ValueError:
			return None
	try:
		return random.randint(0,int(value))
	except ValueError:
		return None

def update_CP (CP, CP_method="fixed", value='100'):
	ldict = {'value':value}
	exec("new = "+CP_method+"_CP(value)",globals(),ldict)
	new = ldict['new']
	if new is not None:
		return CP+new
	return CP