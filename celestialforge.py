import re
import random

# For populating Django models
from cf_core.models import Domain as mDomain
from cf_core.models import Perk as mPerk
from cf_core.models import Addon as mAddon



class Domain:
	
	def __init__(self, name, desc = ""):
		self.name = name
		self.description = desc
		self.perks=[]
		self.id = -1
	
	def __str__(self):
		id_str =""
		if self.id != -1:
			id_str = str(self.id)+" "
		perk_str=""
		for perk in self.perks:
			perk_str+="\n\t"+str(perk)
		return id_str+self.name+perk_str
	
	def add_perk(self, newperk):
		'''
		Adds a new Perk object <newperk> into <self.perks> maintaining ordering by cost.
		'''
		if self.perks == []:
			self.perks.append(newperk)
		else:
			# Currently a sequential search starting from the end (file is already sorted)
			added = False
			i=len(self.perks)-1
			while i >= 0 and not added:
				if newperk.cost > self.perks[i].cost:
					self.perks.insert(i+1,newperk)
					added = True
				elif i == 0:
					self.perks.insert(0,newperk)
				i-=1

class Perk:
	
	def __init__(self, name, desc="", source="", cost=0):
		self.name = name
		self.description = desc
		self.source = source
		self.cost = cost
		self.addons = []
		self.prereqs=[]
		self.id = -1
	
	def __str__(self):
		pad=60
		id_str =""
		if self.id != -1:
			id_str = str(self.id[0])+"."+str(self.id[1])+" "
		if self.addons != []:
			addon_str=""
			for addon in self.addons:
				addon_str+="\n\t\t"+str(addon)
			return id_str+self.name.ljust(pad)+"\t("+(self.source+")").ljust(pad)+"\t["+str(self.cost)+"CP]"+addon_str
		else:
			return id_str+self.name.ljust(pad)+"\t("+(self.source+")").ljust(pad)+"\t["+str(self.cost)+"CP]"
	
	def add_addon(self, newaddon):
		'''
		Adds a new Addon object <newaddon> into <self.addons> maintaining ordering by cost.
		'''
		if self.addons == []:
			self.addons.append(newaddon)
		else:
			# Currently a sequential search starting from the end (file is already sorted)
			added = False
			i=len(self.addons)-1
			while i >= 0 and not added:
				if newaddon.cost > self.addons[i].cost:
					self.addons.insert(i+1,newaddon)
					added = True
				elif i == 0:
					self.addons.insert(0,newaddon)
				i-=1

class Addon:
	
	def __init__(self, name, desc="", cost=0):
		self.name = name
		self.description = desc
		self.cost = cost
		self.id = -1
		self.prereqs=[]
	
	def __str__(self):
		pad=56
		id_str =""
		if self.id != -1:
			id_str = str(self.id[0])+"."+str(self.id[1])+"."+str(self.id[2])+" "
		return id_str+self.name.ljust(pad)+"".ljust(pad)+"\t["+str(self.cost)+"CP]"

class CelestialForge:
	
	def __init__(self, name="Celestial Forge", desc = "", run=[], CP=0):
		self.name = name
		self.description = desc
		self.domains=[]
		# List of (<CP, index, Locked Boolean>) triples
		self.run=run
		self.CP = CP
	
	def __str__(self):
		pad=30
		domain_str=""
		for domain in self.domains:
			domain_str+="\n\t"+(str(domain.id)+". ").ljust(4)+domain.name.ljust(pad)+" ("+str(len(domain.perks))+" Perks)"
		return self.name+domain_str
	
	def print_run(self):
		'''
		Returns a str which provides a formatted summary of <self.run>.
		'''
		output_str =""
		step = 0
		for attempt in self.run:
			# Locked
			if attempt[2]:
				# Addon
				if len(attempt[1]) == 3:
					output_str += "\n\t\t Locked addon: #{} {} ({}CP)".format(self.domains[attempt[1][0]].perks[attempt[1][1]].addons[attempt[1][2]].id[2], self.domains[attempt[1][0]].perks[attempt[1][1]].addons[attempt[1][2]].name, self.domains[attempt[1][0]].perks[attempt[1][1]].addons[attempt[1][2]].cost)
				else:
					output_str += "\n{} [{}CP] Locked: #{} {} from #{} {} ({}CP)".format(str(step).ljust(4), str(attempt[0]).zfill(3), self.domains[attempt[1][0]].perks[attempt[1][1]].id[1], self.domains[attempt[1][0]].perks[attempt[1][1]].name, self.domains[attempt[1][0]].id, self.domains[attempt[1][0]].name, self.domains[attempt[1][0]].perks[attempt[1][1]].cost)
					step += 1
			# Not locked
			else:
				# Selection failed
				if None in attempt[1]:
					output_str += "\n{} [{}CP] Failed".format(str(step).ljust(4),  str(attempt[0]).zfill(3))
					step += 1
				# Addon
				elif len(attempt[1]) == 3:
					output_str += "\n\t\t Attempted addon: #{} {} ({}CP)".format(self.domains[attempt[1][0]].perks[attempt[1][1]].addons[attempt[1][2]].id[2], self.domains[attempt[1][0]].perks[attempt[1][1]].addons[attempt[1][2]].name, self.domains[attempt[1][0]].perks[attempt[1][1]].addons[attempt[1][2]].cost)
				else:
					output_str += "\n{} [{}CP] Attempted: #{} {} from #{} {} ({}CP)".format(str(step).ljust(4), str(attempt[0]).zfill(3), self.domains[attempt[1][0]].perks[attempt[1][1]].id[1], self.domains[attempt[1][0]].perks[attempt[1][1]].name, self.domains[attempt[1][0]].id, self.domains[attempt[1][0]].name, self.domains[attempt[1][0]].perks[attempt[1][1]].cost)
					step += 1
		return output_str
	
	def id_assign(self, cumulative_addons = True):
		'''
		Assigns a unique id to every domain (int), perk (pair of ints), and addon (triple of ints).  In the case of perks and addons, the first int is the domain id and the second int is the perk id.
		'''
		i = 0
		while i < len(self.domains):
			self.domains[i].id = i
			j = 0
			while j <len(self.domains[i].perks):
				self.domains[i].perks[j].id = (i,j)
				k = 0
				while k <len(self.domains[i].perks[j].addons):
					self.domains[i].perks[j].addons[k].id = (i,j,k)
					# Set basic prereqs if all addons are supposed to be cumulative
					if cumulative_addons:
						if k==0:
							self.domains[i].perks[j].addons[k].prereqs =[(i,j)]
						else:
							self.domains[i].perks[j].addons[k].prereqs = self.domains[i].perks[j].addons[k].prereqs.copy()+[(i,j,k-1)]
					k+=1
				j+=1
			i+=1
	
	def find_domain_id (self, domain_name):
		'''
		Case insensitive search for a domain with name <domain_name>; returns id of first match.
		'''
		for domain in self.domains:
			if domain.name.lower() == domain_name.lower():
				return domain.id
		return "Domain not found."
	
	def find_perk_id (self, perk_name, domain_id = None):
		'''
		Case insensitive search for a perk with name <perk_name>; returns id of first match.
		'''
		if domain_id != None:
			for perk in self.domains[domain_id].perks:
				if perk.name.lower() == perk_name.lower():
					return perk.id
		else:
			for domain in self.domains:
				for perk in domain.perks:
					if perk.name.lower() == perk_name.lower():
						return perk.id
		return "Perk not found."
	
	def find_addon_id (self, addon_name, perk_id = None, domain_id = None):
		'''
		Case insensitive search for an addon with name <addon_name>; returns id of first match.
		'''
		if perk_id != None:
			for addon in self.domains[perk_id[0]].perks[perk_id[1]].addons:
				if addon.name.lower() == addon_name.lower():
					return addon.id
		elif domain_id != None:
			for perk in self.domains[domain_id].perks:
				for addon in perk.addons:
					if addon.name.lower() == addon_name.lower():
						return addon.id
		else:
			for domain in self.domains:
				for perk in domain.perks:
					for addon in perk.addons:
						if addon.name.lower() == addon_name.lower():
							return addon.id
		return "Addon not found."
	
	def populate_from_CF2 (self, filename="CF2.txt"):
		'''
		Populates the <Celestial Forge> object from CF2.txt (Celestial Forge Version 2.0)
		'''
		# CURRENTLY DOES NOT DEAL WITH PREREQS
		# Open file and read non-empty lines into list <raw>
		file = open(filename,"r", encoding="utf-8", errors="backslashreplace")
		raw = []
		for line in file:
			line = line.strip()
			if line:
				raw.append(line)
		file.close()

		# Skip header material
		i = 4
		# Every iteration of this loop is expected to start a new domain
		while i < len(raw):
			if raw[i][0] != '-':
				if raw[i+1][0] != '-':
					self.domains.append(Domain(raw[i],raw[i+1]))
					i+=2
				else:
					self.domains.append(Domain(raw[i],""))
					i+=1
				# Start new perk (-)
				while i < len(raw) and raw[i][0] == '-' and raw[i][1] != '-':
					raw[i] = raw[i].split('(')
					addon_list=[]
					# Perk contains addons
					if '|' in raw[i][0]:
						raw[i][0] = raw[i][0].split('|')
						addon_list = raw[i][0][1:]
						newperk = Perk(raw[i][0][0][1:].strip(), re.split(r'\(\d*\s*CP\s*\)\s*[:|-|\s]\s*',raw[i+1])[1].strip(), raw[i][1].strip()[:-1], int(re.split(r'\s*CP\s*\)',raw[i+1])[0].split('(')[1]))
					else:
						newperk = Perk(raw[i][0][1:].strip(), raw[i+1], raw[i][1].strip()[:-1], int(re.split(r'CP\s*\)\s*',raw[i][2])[0]))
					i+=2
					# Deal with bullets (and random \n) in perk descriptions
					while i < len(raw) and (raw[i][0]=='*' or (raw[i][0].isalpha() and (addon_list == [] or raw[i].split('(')[0].strip().lower() != addon_list[0].strip().lower()))):
						newperk.description+="\n\t"+raw[i]
						i+=1
					# Deal with addons
					for addon_name in addon_list:
						raw[i]=re.split(r'CP\s*\)\s*[:|-|\s]\s*',raw[i])
						newaddon = Addon(addon_name.strip(),raw[i][1].strip(),int(raw[i][0].split('(')[1]))
						i+=1
						# Deal with bullets in addon description
						while i < len(raw) and raw[i][0]=='*':
							newaddon.description+="\n"+raw[i]
							i+=1
						newperk.add_addon(newaddon)
					self.domains[-1].add_perk(newperk)
			else:
				i+=1
		self.id_assign()

	def populate_from_CF (self, filename="CF.txt"):
		'''
		Populates the <Celestial Forge> object from CF.txt (Celestial Forge Version 1.0)
		'''
		# Open file and read non-empty lines into list <raw>
		file = open(filename,"r", encoding="utf-8", errors="backslashreplace")
		raw = []
		for line in file:
			line = line.strip()
			if line:
				raw.append(line)
		file.close()

		prereq_lists = []
		i = 0
		# Every iteration of this loop is expected to start a new domain
		while i < len(raw):
			self.domains.append(Domain(raw[i][raw[i].find('. ')+1:raw[i].find(' Domain')].strip(),""))
			i+=1
			# Start new perk
			while i < len(raw) and re.search(r'^\d+\.\s\(\d+\)-',raw[i]):
				# Parse <raw[i]> into a list with 0: name, 1: source, 2: cost, and 3: description
				raw[i] = re.sub(r'^\d+\.\s\(\d+\)-','',raw[i])
				raw[i] = raw[i].split('(',1)
				raw[i] = [raw[i][0]]+raw[i][1].split(') (',1)
				raw[i] = [raw[i][0],raw[i][1]]+raw[i][2].split('cp) ',1)
				addon_list = []
				prereqs = False
				# Perk has prereqs
				if '!!' == raw[i][3][:2]:
					prereqs = True
					# Create a new sublist in <prereq_list> which starts with the current perk's name
					prereq_lists.append([raw[i][0].strip()])
					# Pull off the prereqs
					temp, raw[i][3] = raw[i][3][2:].split('!!',1)
					temp = temp.replace('Requires ','',1)
					for name in temp.split(';'):
						# Addons are in this part of the prereqs
						if '+' in name:
							first = True
							# Add a list entry which starts with the perk name and then gives the addon names
							for subname in name.split('+'):
								if first:
									prereq_lists[-1].append([subname.strip()])
									first = False
								else:
									prereq_lists[-1][-1].append(subname.strip())
						# No Addons in this part of the prereqs
						else:
							# Just add the perk name
							prereq_lists[-1].append(name.strip())
				# Perk contains addons
				if raw[i][3][0] == '[':
					# Pull perk name from first bracket
					raw[i][0], raw[i][3] = raw[i][3].split('] (',1)
					raw[i][0] = raw[i][0][1:]
					if prereqs:
						# Update perk name in <prereq_list> in case it's changed
						prereq_lists[-1][0] = raw[i][0].strip()
					# Pull perk cost
					raw[i][3] = raw[i][3].split('cp)',1)
					raw[i][2] = raw[i][3][0]
					# Separate description and remaining text block
					raw[i][3], remains = raw[i][3][1].split(' [',1)
					# Find and create addons
					while remains.find('] (') != -1:
						# Parse <remains> into a list with 0: name, 1: cost, 2: description, and (if applicable) 3: remaining text
						remains = remains.split('] (',1)
						remains = [remains[0]]+remains[1].split('cp)',1)
						if remains[2].find('] (') != -1:
							remains = [remains[0], remains[1]]+remains[2].split(' [',1)
						addon_list.append(Addon(remains[0].strip(),remains[2].strip(),int(remains[1].strip())))
						# Prep for next iteration of the loop
						if len(remains)>3:
							remains = remains[3]
						else:
							remains =""
				newperk = Perk(raw[i][0].strip(), raw[i][3].strip(), raw[i][1].strip(), int(raw[i][2].strip()))
				for newaddon in addon_list:
					newperk.add_addon(newaddon)
				self.domains[-1].add_perk(newperk)
				i+=1
		self.id_assign()
		# Assign explicit prereqs
		for prereq_list in prereq_lists:
			# Find the id of the perk with prereqs
			id = self.find_perk_id(prereq_list[0])
			for prereq in prereq_list[1:]:
				# Prereq(s) is addon
				if type(prereq) is list:
					prereq_perk_id = self.find_perk_id(prereq[0])
					for addon_prereq in prereq[1:]:
						self.domains[id[0]].perks[id[1]].prereqs.append(self.find_addon_id(addon_prereq, perk_id=prereq_perk_id))
				# Prereqs is perk
				else:
					self.domains[id[0]].perks[id[1]].prereqs.append(self.find_perk_id(prereq))
			self.domains[id[0]].perks[id[1]].prereqs.sort()
	
	def random_domain (self):
		'''
		Returns a random domain index.
		'''
		return random.randint(0, len(self.domains)-1)
	
	def seq_domain (self):
		'''
		Returns the next domain index.
		'''
		if self.run == [] or self.run[-1][1][0] == len(self.domains)-1:
			return 0
		return self.run[-1][1][0]+1
	
	def random_perk (self, domain_index):
		'''
		Returns a random perk index from the domain with <domain_index>.
		'''
		return random.randint(0, len(self.domains[domain_index].perks)-1)
	
	def random_addon (self, domain_index, perk_index):
		'''
		Returns the index of a random addon from the perk with <perk_index> in the domain with <domain_index>.
		'''
		if self.domains[domain_index].perks[perk_index].addons != []:
			return random.randint(0, len(self.domains[domain_index].perks[perk_index].addons)-1)
		else:
			return None
	
	def bin_search_for_cost(self, list, cost):
		'''
		Recursive binary search for the sublist of <list> with items of cost <cost>.  Returns sublist if found; <None> otherwise.
		'''
		i = len(list)//2
		if len(list) == 1:
			if list[0].cost != cost:
				return None
			else:
				return list
		elif list[i]< cost:
			 return bin_search_for_cost(self, list[i+1:], cost)
		elif list[i] > cost:
			return bin_search_for_cost(self, list[:i], cost)
		else:
			j = i
			while i!=0 and list[i-1].cost == cost:
				i-=1
			while j!=len(list)-1 and list[j+1].cost == cost:
				j+=1
			if j == len(list)-1:
				return list[i:]
			else:
				return list[i:j+1]

	def bin_search_for_max(self, list, cost):
		'''
		Iterative binary search for the sublist of <list> with the maximal cost less than or equal to <cost>.  Returns a tuple (<startindex>, <endindex>) if found; <None> otherwise.
		'''
		low = 0
		high = len(list)
		current_max = None
		while low <= high:
			mid = (high+low)//2
			if list[mid].cost > cost:
				high=mid-1
			elif list[mid].cost < cost:
				current_max = mid
				low = mid+1
			else:
				break
		if current_max == None:
			return None
		# <current_max> is the index of an item with maximal cost; now find endpoints
		low = current_max
		high = current_max
		while low!=0 and list[low-1].cost == cost:
			low-=1
		while high!=len(list)-1 and list[high+1].cost == cost:
			high+=1
		return (low, high)
	
	def bin_search_for_affordable(self, list, cost):
		'''
		Variation on iterative binary search for sublist of <list> where items have cost at most <cost>.  Returns sublist if found; <None> otherwise.
		'''
		low = 0
		high = len(list)
		while low <= high:
			mid = (high+low)//2
			# Breakpoint found or doesn't exist
			if list[mid].cost > cost and (mid == 0 or list[mid-1].cost <= cost):
				if mid == 0:
					return None
				else:
					return list[:mid]
			# Breakpoint lower
			elif list[mid].cost > cost:
				high=mid-1
			# Breakpoint higher
			elif list[mid].cost < cost:
				low = mid+1
			else:
				while mid!=len(list)-1 and list[mid+1].cost == cost:
					mid+=1
				return list[:mid+1]
	
	def max_perk (self, domain_index):
		'''
		Returns the index of the most expensive affordable perk in the domain with <domain_index>, breaking ties randomly.  Returns <None> if no such perk exists.
		'''
		max = self.bin_search_for_max(self.domains[domain_index].perks, self.CP)
		if max == None:
			return None
		return random.randint(max[0], max[1])
	
	def random_affordable_perk (self, domain_index):
		'''
		Returns the index of a random affordable perk in the domain with <domain_index>.
		'''
		return random.randint(0, len(self.bin_search_for_affordable(self.domains[domain_index].perks, self.CP))-1)
	
	def random_affordable_addon (self, domain_index, perk_index):
		'''
		Returns the index of a random affordable addon from the perk with <perk_index> in the domain with <domain_index>.  Returns <None> if no affordable addons exist.
		'''
		if self.domains[domain_index].perks[perk_index].addons == []:
			return None
		i=0
		running_cost = 0
		while self.domains[domain_index].perks[perk_index].addons[i].cost + running_cost < self.CP:
			running_cost += self.domains[domain_index].perks[perk_index].addons[i].cost
			i+=1
		if i == 0 and self.domains[domain_index].perks[perk_index].addons[0].cost > self.CP:
			return None
		else:
			return random.randint(0, len(self.domains[domain_index].perks[perk_index].addons[:i])-1)
			
	def select (self, domain_method="random", perk_method="random", addon_method="random_affordable", repeat_attempts=True, timeout=100):
		'''
		Select domain, perk, and possibly addon indices according to the specified methods, updating <self.run> accordingly.  Return True if perk locked and False otherwise.
		'''
		if timeout == 0:
			print("Timeout Error: No acceptable perk found.")
			return None
		# Exec doesn't allow direct modification of local variables, so pass an explicit dictionary and then modify
		ldict = {'self':self}
		exec("domain_index = self."+domain_method+"_domain()",globals(),ldict)
		domain_index = ldict['domain_index']
		exec("perk_index = self."+perk_method+"_perk(domain_index)",globals(),ldict)
		perk_index = ldict['perk_index']
		# Perk not locked and ( either repeats are allowed or not a repeat )
		if (domain_index, perk_index) not in {item[1] for item in self.run if item[2] == True} and (repeat_attempts or (domain_index, perk_index) not in {item[1] for item in self.run}):
			# Can't afford
			if (perk_index == None or domain_index == None) or self.CP < self.domains[domain_index].perks[perk_index].cost:
				self.run.append((self.CP,(domain_index, perk_index), False))
				return False
			# Can afford
			else:
				self.run.append((self.CP, (domain_index, perk_index), True))
				self.CP -= self.domains[domain_index].perks[perk_index].cost
				# Handle possible addons
				if self.domains[domain_index].perks[perk_index].addons != []:
					exec("addon_index = self."+addon_method+"_addon(domain_index, perk_index)",globals(),ldict)
					addon_index = ldict['addon_index']
					if addon_index != None:
						# Collate addon info; currently implemented as all or nothing 
						i=0
						attempts=[]
						running_cost = 0
						while i <= addon_index:
							# Store (<cost>, <id>) tuples
							attempts.append((self.domains[domain_index].perks[perk_index].addons[i].cost, (domain_index, perk_index, i)))
							running_cost += attempts[-1][0]
							i += 1
						# Can afford
						if running_cost <= self.CP:
							for pair in attempts:
								self.run.append((self.CP, pair[1], True))
								self.CP -= pair[0]
						else:
							for pair in attempts:
								self.run.append((self.CP, pair[1], False))
				return True
		# Perk already locked; redo
		return self.select(domain_method, perk_method, addon_method, repeat_attempts,timeout-1)
	
def populate_django_models ():
	#exec(open('celestialforge.py').read()) in Django terminal
	# Create forge
	cf = CelestialForge()
	cf.populate_from_CF()
	# Create Django models
	i=0
	id_dict = {}
	for domain in cf.domains:
		d = mDomain(name=domain.name, description=domain.description)
		try:
			d.save()
			id_dict[i] = d
		except:
			print("Problem", domain)
			d.save()
		j=0
		for perk in domain.perks:
			p = mPerk(name=perk.name, description=perk.description, cost=perk.cost, source_old=perk.source, domain=d)
			try:
				p.save()
				id_dict[(i,j)] = p
			except:
				print("Problem", perk)
				p.save()
			k=0
			for addon in perk.addons:
				a = mAddon(name=addon.name, description=addon.description, cost=addon.cost, perk=p)
				try:
					a.save()
					id_dict[(i,j,k)] = a
				except:
					print("Problem", addon)
					a.save()
				k+=1
			j+=1
		i+=1
	# Add prereqs
	i=0
	for domain in cf.domains:
		j=0
		for perk in domain.perks:
			k=0
			for addon in perk.addons:
				for prereq in addon.prereqs:
					if len(prereq) == 2:
						id_dict[(i,j,k)].prereq_perks.add(id_dict[prereq])
					else:
						id_dict[(i,j,k)].prereq_addons.add(id_dict[prereq])
				k+=1
			for prereq in perk.prereqs:
				if len(prereq) == 2:
					id_dict[(i,j)].prereq_perks.add(id_dict[prereq])
				else:
					id_dict[(i,j)].prereq_addons.add(id_dict[prereq])
			j+=1
		i+=1

'''
if __name__ == "__main__":
	cf = CelestialForge()
	cf.populate_from_CF()
	while len(cf.run)<20:
		cf.select(domain_method="seq", perk_method="random_affordable", addon_method="random_affordable", repeat_attempts=True, timeout=100)
		cf.CP += 100
	print(cf.run)
	print(cf.print_run())
'''

populate_django_models()
