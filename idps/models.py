from django.db import models

import datetime
import core
from core import fields 
from django.core.exceptions import ValidationError
from core import models as core_models
from django.http import request
from location import models as location_models
from insuree.models import Insuree, Family, InsureePolicy
from claim import models as claim_models
from django.db.models import Case, Value, When

# Create your models here.

class PerformanceCriteria(models.Model):
    id = models.SmallIntegerField(db_column='ID', primary_key=True)
    period = models.CharField(db_column='Period', max_length=50, blank=True, null=True)
    health_facility = models.IntegerField(db_column='HFID', blank=True, null=True)
    #health_facility =  models.ForeignKey(location_models.HealthFacility, models.DO_NOTHING, db_column='HFID', blank=True, null=True)
    medecine_availability = models.IntegerField(db_column='MedecineAvailability',blank=True, null= True)
    qualified_personnel =  models.IntegerField(db_column='QualifiedPersonel',blank=True, null= True)
    garbagecan_availability = models.IntegerField(db_column='GarbagecanAvailable',blank=True, null= True)
    rooms_cleaness = models.IntegerField(db_column='RoomCleaness',blank=True, null= True)
    waste_separation = models.IntegerField(db_column='WasteSeparationSystem',blank=True, null= True)
    functionals_toilets =  models.IntegerField(db_column='FunctionalToilets',blank=True, null= True)
    sterilization_tools = models.IntegerField(db_column='SterilizationTools',blank=True, null= True)
    is_validated = models.BooleanField(db_column='isValidated', blank=True, null=True, default=True)
    record_date = models.DateTimeField(db_column='RecordDate',blank=True, null=True)
    audit_user_id = models.IntegerField(db_column='AuditUserId',blank=True, null= True)
    degre_of_rejection = models.IntegerField(db_column='degreofRejection',  blank=True, null= True,default=0)
    promptness_submission = models.IntegerField(db_column='Promptness',blank=True, null= True,default=0)
    hf_score = models.IntegerField(db_column='HFScore', blank=True, null= True, default=0)
    
    @property
    def promptness_submission_service(self,*args, **kwargs):
        promptness_score = 0
        
        return promptness_score


    @property
    def claim_rejection_service(self,*args, **kwargs):
        coef = 0.3
        score_ratio = 0.67
        #recuperer tous les claims dont la date de soumission est dans cette periode
        period_claim = claim_models.Claim.objects.filter(submit_stamp__year = self.period[:4],submit_stamp__month = self.period[6:7], health_facility=self.health_facility)
        num_period_claim = period_claim.count()
        num_valuated_claim = claim_models.Claim.objects.filter(submit_stamp__year = self.period[:4],submit_stamp__month = self.period[6:7],status=16, health_facility=self.health_facility).count()
        num_rejected_claim = claim_models.Claim.objects.filter(submit_stamp__year = self.period[:4],submit_stamp__month = self.period[6:7],status=1, health_facility=self.health_facility).count()
        terminated_claims = num_valuated_claim + num_rejected_claim
        #fais un ratio des deux
        rejection_ratio = num_rejected_claim / terminated_claims
        if rejection_ratio >= 0.3:
            rejection_score = 0
        elif rejection_ratio == 0:
            rejection_score = 20
        elif rejection_ratio < 0.3:
            rejection_score = (rejection_ratio * score_ratio) * 100
        else: None
        
        print(num_valuated_claim)
        print(num_rejected_claim)
        print(terminated_claims)
        print(rejection_ratio)
        print(rejection_ratio * 0.67)
        print(rejection_score)

        return  rejection_score



    @property
    def score_service(self,*args, **kwargs):
        score = (self.promptness_submission + self.degre_of_rejection + self.medecine_availability + self.qualified_personnel + self.garbagecan_availability + self.rooms_cleaness + self.waste_separation + self.sterilization_tools +self.functionals_toilets)
        return score
   

    def save(self, *args, **kwargs):
            self.hf_score = self.score_service
            self.degre_of_rejection = self.claim_rejection_service
            super(PerformanceCriteria,self).save(*args, **kwargs)
    class Meta:
        managed=True
        db_table = 'tblPerformanceCriteria'





