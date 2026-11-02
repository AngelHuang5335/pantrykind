from django.db import models

from django.conf import settings

class Household(models.Model):
    name=models.CharField(max_length=80)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self):return self.name

class Membership(models.Model):
    household=models.ForeignKey(Household,on_delete=models.CASCADE,related_name='memberships')
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='pantry_memberships')
    role=models.CharField(max_length=10,choices=[('owner','Owner'),('member','Member')],default='member')
    class Meta:
        constraints=[models.UniqueConstraint(fields=['household','user'],name='unique_household_member')]
