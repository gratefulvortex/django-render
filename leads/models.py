from django.db import models

class Lead(models.Model):
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    mobile_number = models.CharField(max_length=10)
    through = models.CharField(max_length=255)
    comments = models.TextField()

    

    def __str__(self):
        return self.full_name
