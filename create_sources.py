from cf_core.models import *

def create_sources():
	sources = {}
	for perk in Perk.objects.all():
		if perk.source_old in sources:
			perk.source = sources[perk.source_old]
		elif perk.source_old.lower() in sources:
			perk.source = sources[perk.source_old.lower()]
			Source.objects.get(pk=sources[perk.source_old.lower()]).name = perk.source_old
		elif perk.source_old.upper() in sources:
			perk.source = sources[perk.source_old.upper()]
			Source.objects.get(pk=sources[perk.source_old.upper()]).name = perk.source_old
		else:
			s = Source(name=perk.source_old)
			s.save()
			perk.source = s
			sources[perk.source_old]=s
		perk.save()

create_sources()