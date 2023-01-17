from django.db import models

import datetime
import core
from core import fields 
from django.core.exceptions import ValidationError
from core import models as core_models
from django.http import request
from location import models as location_models
from insuree.models import Insuree, Family, InsureePolicy
from claim.models import Claim, ClaimService
from django.db.models import Count

# Create your models here.

class PerformanceCriteria(models.Model):
    id = models.SmallIntegerField(db_column='ID', primary_key=True)
    date_from =  core.fields.DateField(db_column='StartDate', blank=True, null=True)
    date_to = core.fields.DateField(db_column='EndDate', blank=True, null= True)
    health_facility = models.IntegerField(db_column='HFID', blank=True, null=True)
    #health_facility =  models.ForeignKey(location_models.HealthFacility, models.DO_NOTHING, db_column='HFID', blank=True, null=True)
    promptness =  models.IntegerField(db_column='PromptnessInvoiceSubmission')
    medecine_availability = models.IntegerField(db_column='MedecineAvailability',blank=True, null= True)
    qualified_personnel =  models.IntegerField(db_column='QualifiedPersonel',blank=True, null= True)
    garbagecan_availability = models.IntegerField(db_column='GarbagecanAvailable',blank=True, null= True)
    rooms_cleaness = models.IntegerField(db_column='RoomCleaness',blank=True, null= True)
    waste_separation = models.IntegerField(db_column='WasteSeparationSystem',blank=True, null= True)
    functionals_toilets =  models.IntegerField(db_column='FunctionalToilets',blank=True, null= True)
    sterilization_tools = models.IntegerField(db_column='SterilizationTools',blank=True, null= True)
    is_validated = models.BooleanField(db_column='isValidated', blank=True, null=True, default=False)
    record_date = models.DateTimeField(db_column='RecordDate',blank=True, null=True)
    audit_user_id = models.IntegerField(db_column='AuditUserId',blank=True, null= True)
    degre_of_rejection = models.DecimalField(db_column='degreofRejection', max_digits=18, decimal_places=2,blank=True, null= True)
    hf_score = models.DecimalField(models.DecimalField(db_column='HFScore', max_digits=18, decimal_places=2,blank=True, null= True))


    @property
    def claim_rejection_degree(self,*args, **kwargs):
        date_from = kwargs.get("date_from") #revoir le format de la date
        date_to = kwargs.get("date_to")
        hfid = kwargs.get("health_facility")

        #get all the claims for the defined period
        queryset = Claim.objects.filter(
            health_facility=hfid,
            date_from__gte = date_from,
            date_to__gte = date_to
        ).Count()
        #get the rejected claims for the specified period
        queryset1 = Claim.objects.filter(
            health_facility=hfid,
            status = 1,
            date_from__gte = date_from,
            date_to__gte = date_to
            ).Count()

        #make a ratio of these
        coef = queryset / queryset1

        #score per rejection
        if coef >= 0.3:
            self.degre_of_rejection = 0
        def save(self, *args, **kwargs):
            self.degre_of_rejection = self.claim_rejection_degree
            super(PerformanceCriteria,self).save(*args, **kwargs)

    @property
    def health_facility_score_service(self,*args, **kwargs):
        period =  kwargs.get("") #revoir la format de la date
        hfid = kwargs.get("health_facility")

        hf_data = PerformanceCriteria.objects.filter(
            health_facility= hfid,
            date_from__gte =  period,
            is_validated = True  
        )

        for i in hf_data:
            score=10
       
        # score = sum(
        #     self.functionals_toilets,
        #     self.garbagecan_availability,
        #     self.medecine_availability,
        #     self.qualified_personnel,
        #     self.waste_separation,
        #     self.sterilization_tools) 
            

        self.hf_score = score


        def save(self, *args, **kwargs):
            self.hf_score = self.health_facility_score_service
            super(PerformanceCriteria,self).save(*args, **kwargs)
    class Meta:
        managed=True
        db_table = 'tblPerformanceCriteria'

#django filter data in certain month




