from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core import serializers

class Forge (models.Model):
	name = models.CharField(max_length = 200) 
	description = models.TextField(default="", blank=True)
	perks = models.ManyToManyField("Perk", related_name="forges", blank=True)
	created = models.DateTimeField(editable=False)
	last_update = models.DateTimeField()
	banner = models.ImageField(upload_to='imgs/forge_banners/', null=True, blank=True)
	
	def __str__(self):
		return self.name
	
	def save(self, *args, **kwargs):
		''' On save, update timestamps '''
		if not self.id:
			self.created = timezone.now()
		self.last_update = timezone.now()
		return super(Forge, self).save(*args, **kwargs)
	
	@property
	def get_banner_url(self):
		if self.banner and hasattr(self.banner, 'url'):
			return self.banner.url
		else:
			return "/static/networkcircle--GerdAltmann.png"

class Domain (models.Model):
	name = models.CharField(max_length = 200) 
	description = models.TextField(default="")
	created = models.DateTimeField(editable=False)
	last_update = models.DateTimeField()

	def __str__(self):
		return self.name
	
	def save(self, *args, **kwargs):
		''' On save, update timestamps '''
		if not self.id:
			self.created = timezone.now()
		self.last_update = timezone.now()
		return super(Domain, self).save(*args, **kwargs)
	
	class Meta:
		ordering = ["name"]

class Source (models.Model):
	name = models.CharField(max_length = 200)
	created = models.DateTimeField(editable=False)
	url_wikipedia = models.URLField(null=True, blank=True)
	
	def __str__(self):
		return self.name
		
	def save(self, *args, **kwargs):
		''' On save, update timestamps '''
		if not self.id:
			self.created = timezone.now()
		return super(Source, self).save(*args, **kwargs)
	
	class Meta:
		ordering = ["name"]

class Perk (models.Model):
	name = models.CharField(max_length = 200) 
	description = models.TextField()
	created = models.DateTimeField(editable=False)
	last_update = models.DateTimeField()
	cost = models.PositiveIntegerField()
	source = models.ForeignKey(Source, on_delete = models.SET_NULL, null=True)
	domain = models.ForeignKey(Domain, on_delete = models.CASCADE)
	prereq_perks = models.ManyToManyField("self", symmetrical=False, related_name="required_for_perks", blank=True)
	prereq_addons = models.ManyToManyField("Addon", related_name="required_for_perks", blank=True)
	url_wikipedia = models.URLField(null=True, blank=True)
	url_youtube = models.URLField(null=True, blank=True)
	background = models.ImageField(upload_to='imgs/perk_backgrounds/', null=True, blank=True)
	last_editor = models.ForeignKey(User, on_delete = models.SET_NULL, null=True)
	original = models.TextField(null=True, blank=True)
	
	def __str__(self):
		return f"[{self.domain.name}] {self.name}"
	
	def save(self, *args, **kwargs):
		'''
		On save, update timestamps and set initial values.
		'''
		if not self.id:
			self.created = timezone.now()
		if self.id and not self.original:
			self.original = serializers.serialize('json', [self], fields=('name','description','created','cost','source', 'domain', 'prereq_perks', 'prereq_addons','url_wikipedia','url_youtube','background','last_editor'))
		self.last_update = timezone.now()
		return super(Perk, self).save(*args, **kwargs)
	
	@property
	def get_background_url(self):
		if self.background and hasattr(self.background, 'url'):
			return self.background.url
		else:
			return "/static/forge.gif"
	
	class Meta:
		ordering = ["domain", "name"]

class Addon (models.Model):
	name = models.CharField(max_length = 200) 
	description = models.TextField()
	created = models.DateTimeField(editable=False)
	last_update = models.DateTimeField()
	cost = models.PositiveIntegerField()
	perk = models.ForeignKey(Perk, on_delete = models.CASCADE, blank=True, null=True)
	prereq_perks = models.ManyToManyField(Perk, related_name="required_for_addons", blank=True)
	prereq_addons = models.ManyToManyField("self", symmetrical=False, related_name="required_for_addons", blank=True)

	def __str__(self):
		return f"[{self.perk.domain.name}:{self.perk.name}] {self.name}"
	
	def save(self, *args, **kwargs):
		''' On save, update timestamps '''
		if not self.id:
			self.created = timezone.now()
		self.last_update = timezone.now()
		return super(Addon, self).save(*args, **kwargs)

	class Meta:
		ordering = ["perk", "name"]

class Version (models.Model):
	number = models.PositiveIntegerField(default=0)
	created = models.DateTimeField(editable=False)
	json = models.TextField()
	perk = models.ForeignKey(Perk, related_name="previous_versions", on_delete = models.CASCADE)
	editor = models.ForeignKey(User, on_delete = models.SET_NULL, null=True)
	
	class Meta:
		ordering = ["number"]

	def __str__(self):
		return self.perk.name+" [Version "+str(self.created)+']'
	
	def save(self, *args, **kwargs):
		''' On initial save, set <created> timestamp '''
		if not self.id:
			self.created = timezone.now()
		return super(Version, self).save(*args, **kwargs)

class Run (models.Model):
	name = models.CharField(max_length = 200, blank=True, null=True)
	created = models.DateTimeField(editable=False)
	last_update = models.DateTimeField()
	owner = models.ForeignKey(User, related_name="runs", on_delete = models.CASCADE)
	forge = models.ForeignKey(Forge, related_name="runs", on_delete = models.CASCADE)
	
	class Meta:
		ordering = ["last_update"]

	def __str__(self):
		if self.name:
			return self.owner.username+"'s "+self.name
		else:
			return self.owner.username+"'s Unnamed Run"
	
	def save(self, *args, **kwargs):
		''' On save, update timestamps '''
		if not self.id:
			self.created = timezone.now()
		self.last_update = timezone.now()
		return super(Run, self).save(*args, **kwargs)
	
	@property
	def get_current_cp (self):
		if self.attempts.exists():
			return self.attempts.order_by('number').last().cp
		else:
			return 0
	
	@property
	def get_current_cp_formatted (self):
		if self.attempts.exists():
			return f"{self.attempts.order_by('number').last().cp:,}"
		else:
			return 0
	
	def get_current_number (self):
		if self.attempts.exists():
			return self.attempts.order_by('number').last().number
		else:
			return -1
	
	def get_number_locked (self):
		if self.attempts.exists():
			return self.attempts.filter(locked=True).count()
		else:
			return 0

class Attempt (models.Model):
	domain = models.ForeignKey(Domain, on_delete = models.CASCADE)
	perk = models.ForeignKey(Perk, on_delete = models.CASCADE)
	addons = models.ManyToManyField(Addon, symmetrical=False, blank=True)
	cp = models.PositiveIntegerField()
	locked = models.BooleanField()
	run = models.ForeignKey(Run, on_delete = models.CASCADE, related_name="attempts", blank=True, null=True)
	number = models.PositiveIntegerField(default=0)
	
	class Meta:
		ordering = ["number"]

	def __str__(self):
		if self.run.name:
			return '['+self.run.owner.username+"::"+self.run.name+"] Attempt #"+str(self.number)+" ("+self.perk.name+')'
		else:
			return '['+self.run.owner.username+":: Unnamed Run] Attempt #"+str(self.number)+" ("+self.perk.name+')'

	def save(self, *args, **kwargs):
		''' On save, update timestamps '''
		if self.run:
			self.run.save()
		return super(Attempt, self).save(*args, **kwargs)

