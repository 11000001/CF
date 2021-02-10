import random
from .models import *

def is_youtube_url(url):
	'''
	Checks whether <url> is a youtube url (but not validity). 
	'''
	return url.startswith("http://www.youtube.com/") or url.startswith("www.youtube.com/") or url.startswith("https://www.youtube.com/")

def is_wikipedia_url(url):
	'''
	Checks whether <url> is a wikipedia url (but not validity). 
	'''
	return url.startswith("https://en.wikipedia.org/wiki/") or url.startswith("en.wikipedia.org/wiki/") or url.startswith("http://en.wikipedia.org/wiki/")

def one_step_close_prereq (origin):
	'''
	Adds all prereqs for prereqs of <origin> as prereqs of <origin>.
	'''
	# Prereqs exist
	if origin.prereq_perks.exists() or origin.prereq_addons.exists():
		# Collect all prereqs into <todo> (checking for NoneType)
		todo = []
		if origin.prereq_perks.exists():
			todo += list(origin.prereq_perks.all())
		if origin.prereq_addons.exists():
			todo += list(origin.prereq_addons.all())
		# Add all prereqs of prereqs as prereqs of <origin>
		for prereq in todo:
			if prereq.prereq_perks.exists():
				for new_perk_prereq in prereq.prereq_perks.all():
					origin.prereq_perks.add(new_perk_prereq)
			if prereq.prereq_addons.exists():
				for new_addon_prereq in prereq.prereq_addons.all():
					origin.prereq_addons.add(new_addon_prereq)

def close_all_prereqs ():
	'''
	Force transitive closure of prereqs for the entire database.
	'''
	finished = []
	unfinished = list(Perk.objects.all())+list(Addon.objects.all())
	while unfinished != []:
		current = unfinished.pop()
		finished, unfinished = close_prereq(current, finished, unfinished)

def close_prereq (current, finished, unfinished):
	'''
	Constructs the transitive closure of <current> and adjusts the <finished> and <unfinished> lists accordingly.
	'''
	# Base case: No prereqs
	if not current.prereq_perks.exists() and not current.prereq_addons.exists():
		finished.append(current)
		return finished, unfinished
	# Prereqs exist
	else:
		# Collect all prereqs (checking for NoneType)
		todo = []
		if current.prereq_perks.exists():
			todo += list(current.prereq_perks.all())
		if current.prereq_addons.exists():
			todo += list(current.prereq_addons.all())
		# Add all prereqs of prereqs (...) as prereqs of <current>
		for prereq in todo:
			if prereq not in finished and prereq not in unfinished:
				raise ValueError("Cycle of prereqs detected on "+str(prereq))
			# Recurse if prereq is unfinished
			elif prereq not in finished:
				unfinished.remove(prereq)
				finished, unfinished = close_prereq (prereq, finished, unfinished)
			# Close current prereqs (all of these should now be finished)
			if prereq.prereq_perks.exists():
				for new_perk_prereq in prereq.prereq_perks.all():
					current.prereq_perks.add(new_perk_prereq)
			if prereq.prereq_addons.exists():
				for new_addon_prereq in prereq.prereq_addons.all():
					current.prereq_addons.add(new_addon_prereq)
		finished.append(current)
		return finished, unfinished

def num_prereqs(prereq_model):
	'''
	Returns the number of prereqs for <prereq_model>.
	'''
	return prereq_model.prereq_perks.all().count()+prereq_model.prereq_addons.all().count()

def order_addons (prereq_models):
	'''
	Takes a query set of models with prereqs and returns a list of these models where prereqs always appear earlier.
	'''
	list(prereq_models).sort(key=num_prereqs)
	return prereq_models

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

def max_addon (run, perk, CP):
	'''
	Returns a pair <(option, total_cost)>.  <option> is a list of unsecured addons from the perk <perk> whose total cost is maximal among affordable addon selections; 
	<total_cost> is this cost. Ties are broken randomly.  Returns <None> if no such list exists.
	'''
	print("in max addon")
	addons = perk.addon_set.all()
	affordable_list = []
	for addon in addons:
		print("addons exist!")
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
					print("option too expensive")
					break
			if total_cost <= CP:
				print("should be an addon")
				if affordable_list == [] or affordable_list[0][1] < total_cost:
					affordable_list = [(option, total_cost)]
				elif affordable_list[0][1] == total_cost:
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
		attempt=Attempt(domain=domain, perk=perk, cp=CP, locked=False, run=run, number=run.get_current_number()+1)
		attempt.save()
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
				if not prereqs_satisfied(run, addon.prereq_perks.exclude(pk=perk.id), addon.prereq_addons.exclude(perk=perk)):
					attempt = Attempt(domain=domain, perk=perk, cp=CP, locked=True, run=run, number=run.get_current_number()+1)
					attempt.save()
					return True
			# No prereq failures
			attempt=Attempt(domain=domain, perk=perk, cp=CP-addon_pair[1], locked=True, run=run, number=run.get_current_number()+1)
			attempt.save()
			for addon in addon_pair[0]:
				attempt.addons.add(addon)
			attempt.save()
			return True
		# Not found or too costly; no addons
		else:
			attempt=Attempt(domain=domain, perk=perk, cp=CP, locked=True, run=run, number=run.get_current_number()+1)
			attempt.save()
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
