from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


# Create your models here.
class Feature (models.Model):
    key = models.CharField(max_length=64, unique=True)
    used_count = models.IntegerField(default=0)

    def __str__(self):
        return self.key


class Plans(models.Model):
    key = models.CharField(max_length=64, unique=True)
    features = models.ManyToManyField(Feature)

    def __str__(self):
        return self.key


class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plans, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()

    def __str__(self):
        return f"{self.user.email} - {self.plan.key} ({self.start_date} to {self.end_date})"


class History(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to="history", null=True, blank=True)
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.date} - {self.feature.key}"


