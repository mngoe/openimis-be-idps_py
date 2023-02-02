from django.db import models

from datetime import datetime, time
import calendar
import core
from core import fields 
from django.core.exceptions import ValidationError
from core import models as core_models
from django.http import request
from insuree.models import Insuree, Family, InsureePolicy
from claim import models as claim_models
from django.db import connection


# Create your models here.

class PerformanceCriteria(models.Model):
    id = models.SmallIntegerField(db_column='ID', primary_key=True)
    period = models.CharField(db_column='Period', max_length=50, blank=True, null=True)
    health_facility = models.IntegerField(db_column='HFID', blank=True, null=True)
    #health_facility =  models.ForeignKey(location_models.HealthFacility, models.DO_NOTHING, db_column='HFID', blank=True, null=True)
    medecine_availability = models.IntegerField(db_column='MedecineAvailability',blank=True, null= True, )
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
        val_claim = 16
        period_year = int(self.period[:4])
        period_month = int(self.period[6:7])
        period_month_end = calendar.monthrange(period_year,period_month)[-1]
        format_period_start = datetime(year=period_year, month=period_month,day=1, hour=00, minute=00, second=000)
        format_period_end = datetime(year=period_year, month=period_month,day=period_month_end, hour=00, minute=00, second=000)    
        mid_month = datetime.strptime(str( self.period[:4] + '-' + '0'+ self.period[6:7] + '-' +'15 00:00:00'),'%Y-%m-%d %H:%M:%S')
        no_date  =  datetime.strptime(str( self.period[:4] + '-' + '0'+ self.period[6:7] + '-' +'16 00:00:00'),'%Y-%m-%d %H:%M:%S')
        
        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT 1 AS id, CAST(AVG(CAST(DateProcessed AS FLOAT)) AS DATETIME) AS average_date
                FROM tblClaim
                WHERE ClaimStatus=%s 
                AND DateProcessed >=%s AND DateProcessed <=%s     
            ''',[val_claim,format_period_start,format_period_end])
            row =  cursor.fetchone()

        if row[1]==None:
            dt = str(no_date)
        else:
            dt =  str(row[1])

        format_medium_date = datetime.strptime(dt,'%Y-%m-%d %H:%M:%S')

        interval_diff = ( mid_month - format_medium_date ).days
        
        if  interval_diff < 0:
            promptness_score = 0
        elif interval_diff in range(10,14):
            promptness_score = 30
        elif  interval_diff in range(5,9):
            promptness_score = 20
        elif interval_diff in range(0,4):
            promptness_score = 15
        else: None
        
        return promptness_score

    @property
    def claim_rejection_service(self,*args, **kwargs):
        coef = 0.3
        score_ratio = 0.67
        period_claim = claim_models.Claim.objects.filter(submit_stamp__year = self.period[:4],submit_stamp__month = self.period[6:7], health_facility=self.health_facility)
        
        num_valuated_claim = claim_models.Claim.objects.filter(submit_stamp__year = self.period[:4],submit_stamp__month = self.period[6:7],status=16, health_facility=self.health_facility).count()
        num_rejected_claim = claim_models.Claim.objects.filter(submit_stamp__year = self.period[:4],submit_stamp__month = self.period[6:7],status=1, health_facility=self.health_facility).count()
        terminated_claims = num_valuated_claim + num_rejected_claim

        if terminated_claims == 0:
            rejection_ratio = 0
        elif num_rejected_claim == 0 and num_valuated_claim > 0 :
           rejection_ratio = num_rejected_claim / terminated_claims
        else:
                rejection_ratio = num_rejected_claim / terminated_claims

        
        if rejection_ratio >= coef:
            rejection_score = 0
        if rejection_ratio == 0:
            rejection_score = 0
        elif rejection_ratio < coef:
            rejection_score = (rejection_ratio * score_ratio) * 100
        else: None

        return  int(rejection_score)


    @property
    def score_service(self,*args, **kwargs):
        score = (self.promptness_submission + self.degre_of_rejection + self.medecine_availability + self.qualified_personnel + self.garbagecan_availability + self.rooms_cleaness + self.waste_separation + self.sterilization_tools +self.functionals_toilets)
        return score
   

    def save(self, *args, **kwargs):
            self.promptness_submission = self.promptness_submission_service
            self.degre_of_rejection = self.claim_rejection_service
            self.hf_score = self.score_service
            super(PerformanceCriteria,self).save(*args, **kwargs)
    class Meta:
        managed=True
        db_table = 'tblPerformanceCriteria'





