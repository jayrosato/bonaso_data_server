from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from users.models import User
from indicators.models import Indicator, IndicatorSubcategory
from projects.models import Project, Task
from datetime import datetime, date
import uuid
from django.utils.timezone import now
from datetime import timedelta

class DisabilityType(models.Model):
    class DisabilityTypes(models.TextChoices):
        VI = 'VI', _('Visually Impaired')
        PD = 'PD', _('Physical Disability')
        ID = 'ID', _('Intellectual Disability')
        HI = 'HD', _('Hearing Impaired')
        PSY = 'PSY', _('Psychiatric Disability')
        SI = 'SI', _('Speech Impaired')
        OTHER = 'OTHER', _('Other Disability')
    
    name = models.CharField(max_length=10, choices=DisabilityTypes.choices, unique=True)

class KeyPopulation(models.Model):
    class KeyPopulations(models.TextChoices):
        FSW = 'FSW', _('Female Sex Workers')
        MSM = 'MSM', _('Men Who Have Sex With Men')
        PWID = 'PWID', _('People Who Inject Drugs')
        TG = 'TG', _('Transgender')
        INTERSEX = 'INTERSEX', _('Intersex')
        LBQ = 'LBQ', _('Lesbian Bisexual or Queer')
        OTHER = 'OTHER', _('Other Key Population Status')
    
    name = models.CharField(max_length=10, choices=KeyPopulations.choices, unique=True)

class RespondentAttributeType(models.Model):
    class Attributes(models.TextChoices):
        PLWHIV = 'PLWHIV', _('Person Living with HIV')
        PWD = 'PWD', _('Person Living with a Disability')
        KP = 'KP', _('Key Population')
        COMMUNITY_LEADER = 'Community_Leader', _('Community Leader')
        CHW = 'CHW', _('Community Health Worker')
        STAFF = 'Staff', _('Organization Staff')

    name = models.CharField(max_length=25, choices=Attributes.choices, unique=True)
    def __str__(self):
        return self.name
      
class Respondent(models.Model):
    class Sex(models.TextChoices):
        FEMALE = 'F', _('Female')
        MALE = 'M', _('Male')
        NON_BINARY = 'NB', _('Non-Binary')
    
    class District(models.TextChoices):
        CENTRAL = 'Central', _('Central District')
        GHANZI = 'Ghanzi', _('Ghanzi District')
        KGALAGADI = 'Kgalagadi', _('Kgalagadi District')
        KGATLENG = 'Kgatleng', _('Kgatleng District')
        KWENENG = 'Kweneng', _('Kweneng District')
        NE = 'North East', _('North East District')
        NW = 'North West', _('North West District')
        SE = 'South East', _('South East District')
        SOUTHERN = 'Southern', _('Southern District')
        CHOBE = 'Chobe', _('Chobe District')

    class AgeRanges(models.TextChoices):
        U18 = 'under_18', _('Under 18')
        ET_24 = '18_24', _('18–24')
        T5_34 = '25_34', _('25–34')
        T5_44 = '35_44', _('35–44')
        F5_64 = '45_64', _('45–64')
        O65 = '65_plus', _('65+')
        
    uuid =  models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    is_anonymous = models.BooleanField(default=False, verbose_name='Is Anonymous')
    id_no = models.CharField(max_length=255, unique=True, verbose_name='ID/Passport Number', blank=True, null=True)
    first_name = models.CharField(max_length=255, verbose_name='First Name', blank=True, null=True)
    last_name = models.CharField(max_length=255, verbose_name='Last Name', blank=True, null=True)
    age_range = models.CharField(max_length=10, choices=AgeRanges.choices, blank=True, null=True, verbose_name='Age Range')
    dob = models.DateField(verbose_name='Date of Birth', blank=True, null=True)
    sex = models.CharField(max_length=2, choices=Sex.choices, verbose_name='Sex')
    ward = models.CharField(max_length=255, verbose_name='Ward', blank=True, null=True)
    village = models.CharField(max_length=255, verbose_name='Village')
    district = models.CharField(max_length=25, choices=District.choices, verbose_name='District')
    citizenship = models.CharField(max_length=255, verbose_name='Citizenship/Nationality')
    special_attribute = models.ManyToManyField(RespondentAttributeType, through='RespondentAttribute', blank=True, verbose_name='Special Respondent Attributes')
    kp_status = models.ManyToManyField(KeyPopulation, through='KeyPopulationStatus', blank=True, verbose_name='Key Population Status')
    disability_status = models.ManyToManyField(DisabilityType, through='DisabilityStatus', blank=True, verbose_name='Disability Status')
    email = models.EmailField(verbose_name='Email Address', null=True, blank=True)
    phone_number = models.CharField(max_length=255, verbose_name='Phone Number', null=True, blank=True)
    comments = models.TextField(blank=True, null=True, verbose_name='Comments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, default=None, null=True, blank=True, related_name='respondent_created_by')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, default=None, null=True, blank=True, related_name='respondent_updated_by')

    def clean(self):
        if self.is_anonymous:
            if self.first_name or self.last_name or self.email or self.phone_number or self.id_no or self.dob:
                raise ValidationError('This respondent was marked as anonymous, but personal information was provided. Please either remove this information or get permission from the respondent to collect their personal information.')
            if not self.age_range:
                raise ValidationError('Anonymous respondents are required to provide an age range for reporting purposes.')
        
        if not self.is_anonymous:
            missing = []
            if not self.id_no: 
                missing.append('Passport/ID Number')
            if not self.first_name: 
                missing.append('First Name')
            if not self.last_name: 
                missing.append('Last Name')
            if not self.ward: 
                missing.append('Ward')
            if not self.dob:
                missing.append('Date of Birth')
            if missing:
                raise ValidationError({field: "This field is required If the respondent does not wish to provide any of this information, please mark them as anonymous." for field in missing})

    def save(self, *args, **kwargs):
        if self.dob:
            # If dob is a string, convert it
            if isinstance(self.dob, str):
                self.dob = date.fromisoformat(self.dob)
            # If dob is a tuple, assume (year, month, day)
            elif isinstance(self.dob, tuple) and len(self.dob) == 3:
                self.dob = date(*self.dob)
            # Optionally, handle datetime objects
            elif isinstance(self.dob, datetime):
                self.dob = self.dob.date()
            today = date.today()

            age = today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))
            if age < 18:
                self.age_range = self.AgeRanges.U18
            elif age <= 24:
                self.age_range = self.AgeRanges.ET_24
            elif age <= 34:
                self.age_range = self.AgeRanges.T5_34
            elif age <= 44:
                self.age_range = self.AgeRanges.T5_44
            elif age <= 64:
                self.age_range = self.AgeRanges.F5_64
            else:
                self.age_range = self.AgeRanges.O65
        super().save(*args, **kwargs)

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'
    
    def get_age(self):
        today = datetime.today()
        return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))

    def __str__(self):
        return self.get_full_name() if not self.is_anonymous else f'Anonymous Respondent ({self.uuid})'

class RespondentAttribute(models.Model):
    respondent = models.ForeignKey(Respondent, on_delete=models.CASCADE, blank=True, null=True)
    attribute = models.ForeignKey(RespondentAttributeType, on_delete=models.CASCADE, blank=True, null=True)
    auto_assigned = models.BooleanField(default=False)
    class Meta:
        unique_together = ('respondent', 'attribute')

    def __str__(self):
        return f'{self.respondent} - {self.attribute}'

class KeyPopulationStatus(models.Model):
    respondent = models.ForeignKey(Respondent, on_delete=models.CASCADE, blank=True, null=True)
    key_population = models.ForeignKey(KeyPopulation, on_delete=models.CASCADE, blank=True, null=True)
    class Meta:
        unique_together = ('respondent', 'key_population')

    def __str__(self):
        return f'{self.respondent} - {self.key_population}'

class DisabilityStatus(models.Model):
    respondent = models.ForeignKey(Respondent, on_delete=models.CASCADE, blank=True, null=True)
    disability = models.ForeignKey(DisabilityType, on_delete=models.CASCADE, blank=True, null=True)
    class Meta:
        unique_together = ('respondent', 'disability')

    def __str__(self):
        return f'{self.respondent} - {self.disability}'

class Pregnancy(models.Model):
    respondent = models.ForeignKey(Respondent, on_delete=models.CASCADE)
    is_pregnant = models.BooleanField(null=True, blank=True)
    term_began = models.DateField(null=True, blank=True)
    term_ended = models.DateField(null=True, blank=True)

class HIVStatus(models.Model):
    respondent = models.OneToOneField(Respondent, on_delete=models.CASCADE)
    hiv_positive = models.BooleanField(null=True, blank=True)
    date_positive = models.DateField(null=True, blank=True)

class InteractionFlag(models.Model):
    interaction = models.ForeignKey("Interaction", on_delete=models.CASCADE, related_name="flags")
    reason = models.TextField()
    auto_flagged = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='flag_created_by')
    resolved = models.BooleanField(default=False)
    auto_resolved = models.BooleanField(default=False)
    resolved_reason = models.TextField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='flag_resolved_by')
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'Flag  for interaction {self.interaction.task.indicator.name} for respondent {self.interaction.respondent} for reason {self.reason}.'

class Interaction(models.Model):
    respondent = models.ForeignKey(Respondent, on_delete=models.PROTECT)
    task = models.ForeignKey(Task, on_delete=models.PROTECT)
    interaction_date = models.DateField()
    interaction_location = models.CharField(max_length=255, null=True, blank=True, verbose_name='Interaction Location')
    subcategories = models.ManyToManyField(IndicatorSubcategory, through='InteractionSubcategory', blank=True)
    comments = models.TextField(verbose_name='Comments', null=True, blank=True, default=None)
    numeric_component = models.IntegerField(null=True, blank=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, default=None, null=True, blank=True, related_name='interaction_created_by')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, default=None, null=True, blank=True, related_name='interaction_updated_by')
    
    def __str__(self):
        return f'Interaction with {self.respondent} on {self.interaction_date} for {self.task.indicator.code}'



class InteractionSubcategory(models.Model):
    interaction = models.ForeignKey(Interaction, on_delete=models.CASCADE)
    numeric_component = models.IntegerField(null=True, blank=True, default=None)
    subcategory = models.ForeignKey(IndicatorSubcategory, on_delete=models.CASCADE)