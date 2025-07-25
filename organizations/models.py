from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

class Organization(models.Model):
    name = models.CharField(max_length=255, verbose_name='Organization Name')
    full_name = models.CharField(max_length=255, verbose_name='Full/Extended Organization Name', blank=True, null=True)
    office_address = models.CharField(max_length=255, verbose_name='Office Address', null=True, blank=True)
    office_email = models.EmailField(verbose_name='Office Email Address', null=True, blank=True)
    office_phone = models.CharField(max_length=255, verbose_name='Office Phone Number', null=True, blank=True)
    executive_director = models.CharField(max_length=255, verbose_name='Name of Executive Director', null=True, blank=True)
    ed_email = models.EmailField(verbose_name='Exeuctive Director Email Address', null=True, blank=True)
    ed_phone = models.CharField(max_length=255, verbose_name='Exeuctive Director Phone Number', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='organization_created_by')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='organization_updated_by')

    def __str__(self):
        return self.name