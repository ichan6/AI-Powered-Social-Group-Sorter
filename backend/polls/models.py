from django.db import models
from django.utils import timezone
import uuid

class AccessKey(models.Model):
    key = models.CharField(max_length=64, unique=True)
    usage_limit = models.IntegerField(default=5)
    usage_count = models.IntegerField(default=0)
    device_id = models.CharField(max_length=128, null=True, blank=True)
    ip_log = models.JSONField(default=list, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_expired(self):
        return self.expires_at and timezone.now() > self.expires_at

    @property
    def can_be_used(self):
        return self.usage_count < self.usage_limit and not self.is_expired
        