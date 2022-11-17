from django.db import models

import datetime
import core
from core import fields 
from django.core.exceptions import ValidationError
from core import models as core_models
from django.http import request
from location import models as location_models

# Create your models here.

class PerformanceCriteria(models.Model):
    id = models.SmallIntegerField(db_column='ID', primary_key=True)
    date_from =  core.fields.DateField(db_column='StartDate', blank=True, null=True)
    date_to = core.fields.DateField(db_column='EndDate', blank=True, null= True)
    health_facility =  models.ForeignKey(location_models.HealthFacility, models.DO_NOTHING, db_column='HFID', blank=True, null=True)
    promptness =  models.IntegerField(db_column='PromptnessInvoiceSubmission')
    degree_of_rejection =  models.DecimalField(db_column='DegreeofInvoiceRejection', decimal_places=2,max_digits=18,blank=True, null=True)
    medecine_availability = models.IntegerField(db_column='MedecineAvailability',blank=True, null= True)
    qualified_personnel =  models.IntegerField(db_column='QualifiedPersonel',blank=True, null= True)
    garbagecan_availability = models.IntegerField(db_column='GarbagecanAvailable',blank=True, null= True)
    rooms_cleaness = models.IntegerField(db_column='RoomCleaness',blank=True, null= True)
    waste_separation = models.IntegerField(db_column='WasteSeparationSystem',blank=True, null= True)
    functionals_toilets =  models.IntegerField(db_column='FunctionalToilets',blank=True, null= True)
    sterilization_tools = models.IntegerField(db_column='SterilizationTools',blank=True, null= True)

    class Meta:
        managed=True
        db_table = 'tblPerformanceCriteria'


# prevent multiples insertions on the same period for the same hf in this period



