from django.db import models

class Group(models.Model):
    group_name = models.CharField(max_length=100)
    create_at = models.DateTimeField()

class Message(models.Model):
    message = models.CharField(max_length=250)
    create_at = models.DateTimeField()
    groupe_name = models.ForeignKey(Group, on_delete=models.CASCADE)
    



