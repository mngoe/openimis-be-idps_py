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
from location import models as location_models
from location.models import Location, HealthFacility
from claim.models import Claim, ClaimService, ClaimItem, ClaimServiceService, ClaimServiceItem
from collections import defaultdict

# Create your models here.

class PerformanceCriteria(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)
    period = models.CharField(db_column='Period', max_length=50, blank=True, null=True)
    health_facility =  models.ForeignKey(location_models.HealthFacility, models.DO_NOTHING, db_column='HFID', blank=True, null=True)
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
                SELECT 1 AS id, DATEADD(DAY, AVG(DATEDIFF(DAY, '1900-01-01', DateProcessed)), '1900-01-01') AS average_date
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
        
        promptness_score = 0
        # if  interval_diff < 0:
        #     promptness_score = 0
        if interval_diff in range(10,14):
            promptness_score = 30
        elif  interval_diff in range(5,9):
            promptness_score = 20
        elif interval_diff in range(0,4):
            promptness_score = 15
        
        return promptness_score

    @property
    def claim_rejection_service(self,*args, **kwargs):
        coef = 0.3
        score_ratio = 0.67
        period_claim = claim_models.Claim.objects.filter(submit_stamp__year = self.period[:4],submit_stamp__month = self.period[6:7], health_facility=self.health_facility.id)
        
        num_valuated_claim = claim_models.Claim.objects.filter(submit_stamp__year = self.period[:4],submit_stamp__month = self.period[6:7],status=16, health_facility=self.health_facility.id).count()
        num_rejected_claim = claim_models.Claim.objects.filter(submit_stamp__year = self.period[:4],submit_stamp__month = self.period[6:7],status=1, health_facility=self.health_facility.id).count()
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

def invoice_report_query(user, **kwargs):
    print("on the go ", kwargs)
    date_from = kwargs.get("dateFrom")
    date_to = kwargs.get("dateTo")
    hflocation = kwargs.get("hflocation")
    
    format = "%Y-%m-%d"

    date_from_object = datetime.strptime(date_from, format)
    date_from_str = date_from_object.strftime("%d/%m/%Y")

    date_to_object = datetime.strptime(date_to, format)
    date_to_str = date_to_object.strftime("%d/%m/%Y")

    dictGeo = {}
    dictBase = {
        "dateFrom": date_from_str,
        "dateTo": date_to_str
    }
    # If there is HealthFacility defined in the form
    if hflocation and hflocation!="0" :
        hflocationObj = HealthFacility.objects.filter(
            code=hflocation,
            validity_to__isnull=True
            ).first()
        if hflocationObj:
            dictBase["fosa"] = hflocationObj.name
            dictBase["adress"] = hflocationObj.phone
            dictGeo['health_facility'] = hflocationObj.id

    invoiceElemtTotal_MontantRecueTotal = 0
    invoiceElemtTotal_MtnValideTotal = 0
    dictBase.update({
        "prestationForfaitaire" : [],
        "prestationPlafonnees" : [],
        "prestationsNonMedicales" : [],
        "invoiceElemtTotal": [],
    })
    ## Get All claim corresponding to parameter sent
    statusExcluded = [1, 2]
    claimList = Claim.objects.exclude(
        status=1
    ).filter(
        date_from__gte=date_from,
        date_from__lte=date_to,
        validity_to__isnull=True,
        **dictGeo
    )

    invoiceElemtList = defaultdict(dict)
    invoiceElemtTotal = defaultdict(int)
    invoiceElemtListP = []
    invoiceElemtListF = []
    invoiceElemtListS = []


    for cclaim in claimList:
        #First we calculate on each Service inside a
        claimService = ClaimService.objects.filter(
            claim = cclaim,
            status=1
        )
        for claimServiceElmt in claimService:
            invoiceElemtTotal[claimServiceElmt.service.packagetype+"QtyValuatedV"] = 0
            invoiceElemtTotal[claimServiceElmt.service.packagetype+"MtnValideV"] = 0
            if claimServiceElmt.service.id not in invoiceElemtList[claimServiceElmt.service.packagetype]:
                invoiceElemtList[claimServiceElmt.service.packagetype][claimServiceElmt.service.id] = defaultdict(dict)
                invoiceElemtList[claimServiceElmt.service.packagetype][claimServiceElmt.service.id]["qty"] = defaultdict(int)
                invoiceElemtList[claimServiceElmt.service.packagetype][claimServiceElmt.service.id]["MontantRecue"] = 0

            ## Define global information of each Line
            invoiceElemtList[claimServiceElmt.service.packagetype][claimServiceElmt.service.id]["name"] = claimServiceElmt.service.name
            invoiceElemtList[claimServiceElmt.service.packagetype][claimServiceElmt.service.id]["code"] = claimServiceElmt.service.code
            invoiceElemtList[claimServiceElmt.service.packagetype][claimServiceElmt.service.id]["tarif"] = claimServiceElmt.service.price
            ## Status Valuated of Claim
            if cclaim.status==16:
                invoiceElemtList[claimServiceElmt.service.packagetype][claimServiceElmt.service.id]["qty"]['valuated'] += int(claimServiceElmt.qty_provided)
                if claimServiceElmt.price_valuated == None :
                    claimServiceElmt.price_valuated = 0
                invoiceElemtList[claimServiceElmt.service.packagetype][claimServiceElmt.service.id]["qty"]['sum'] += int(claimServiceElmt.qty_provided * claimServiceElmt.price_valuated)
                invoiceElemtTotal[claimServiceElmt.service.packagetype+"QtyValuatedV"] += int(invoiceElemtList[claimServiceElmt.service.packagetype][claimServiceElmt.service.id]["qty"]['valuated'])
                invoiceElemtTotal[claimServiceElmt.service.packagetype+"MtnValideV"] += int(invoiceElemtList[claimServiceElmt.service.packagetype][claimServiceElmt.service.id]["qty"]['sum'])

            invoiceElemtList[claimServiceElmt.service.packagetype][claimServiceElmt.service.id]["qty"]['all'] += claimServiceElmt.qty_provided
            ## Specific Rules for Montant Recue (for different type of package)
            if claimServiceElmt.service.packagetype == "S":
                pass
                # invoiceElemtList[claimServiceElmt.service.packagetype][claimServiceElmt.service.id]["MontantRecue"] += invoiceElemtList[claimServiceElmt.service.packagetype][claimServiceElmt.service.id]["qty"]['all'] * invoiceElemtList[claimServiceElmt.service.packagetype][claimServiceElmt.service.id]["tarif"]
            else :
                # if claimServiceElmt.service.manualPrice == True :
                #     invoiceElemtList[claimServiceElmt.service.packagetype][claimServiceElmt.service.id]["MontantRecue"] += invoiceElemtList[claimServiceElmt.service.packagetype][claimServiceElmt.service.id]["qty"]['all'] * claimServiceElmt.service.price
                # else :
                claimSs = ClaimServiceService.objects.filter(
                    claimlinkedService = claimServiceElmt
                )
                tarifLocal = 0
                for claimSsElement in claimSs:
                    tarifLocal += claimSsElement.qty_displayed * claimSsElement.price_asked
                #    print(tarifLocal)
                claimSi = ClaimServiceItem.objects.filter(
                    claimlinkedItem = claimServiceElmt
                )
                for claimSiElement in claimSi:
                    tarifLocal += claimSiElement.qty_displayed * claimSiElement.price_asked
                    #print(tarifLocal)
                #print(type(tarifLocal))
                invoiceElemtList[claimServiceElmt.service.packagetype][claimServiceElmt.service.id]["MontantRecue"] += tarifLocal
            
            
            if claimServiceElmt.service.packagetype not in invoiceElemtTotal :
                invoiceElemtTotal[claimServiceElmt.service.packagetype] = defaultdict(int)

            ### Sum of all line at footer of table
            invoiceElemtTotal[claimServiceElmt.service.packagetype+"QtyTotalV"] += int(claimServiceElmt.qty_provided)
            MtnNotValideV = 0
            if int(invoiceElemtTotal[claimServiceElmt.service.packagetype+"MontantRecueTotalV"] - invoiceElemtTotal[claimServiceElmt.service.packagetype+"MtnValideV"]) > 0:
                MtnNotValideV = int(invoiceElemtTotal[claimServiceElmt.service.packagetype+"MontantRecueTotalV"] - invoiceElemtTotal[claimServiceElmt.service.packagetype+"MtnValideV"])
            invoiceElemtTotal[claimServiceElmt.service.packagetype+"MtnNotValideV"] = MtnNotValideV
            invoiceElemtTotal["QtyTotalV"] += int(claimServiceElmt.qty_provided)

        #Then we calculate on each Item inside a claim
        # claimItem = ClaimItem.objects.filter(
        #     claim = cclaim,
        #     status=1
        # )
        # for claimItemElmt in claimItem:
        #     if claimItemElmt.service.id not in invoiceElemtList[claimItemElmt.service.packagetype]:
        #         invoiceElemtList[claimItemElmt.service.packagetype][claimItemElmt.service.id] = defaultdict(int)

        #     if cclaim.status == "16":
        #         invoiceElemtList[claimItemElmt.service.packagetype][claimItemElmt.service.id]["qty"]['valuated'] += claimItemElmt.qty_provided

        #     invoiceElemtList[claimItemElmt.service.packagetype][claimItemElmt.service.id]["name"] = claimItemElmt.service.name
        #     invoiceElemtList[claimItemElmt.service.packagetype][claimItemElmt.service.id]["code"] = claimItemElmt.service.code
        #     invoiceElemtList[claimItemElmt.service.packagetype][claimItemElmt.service.id]["tarif"] = claimItemElmt.service.price
        #     invoiceElemtList[claimItemElmt.service.packagetype][claimItemElmt.service.id]["qty"]["all"] += claimItemElmt.qty_provided
        #     invoiceElemtList[claimItemElmt.service.packagetype][claimItemElmt.service.id]["MontantRecue"] += invoiceElemtList[claimItemElmt.service.packagetype][claimItemElmt.service.id]["qty"]['all'] * invoiceElemtList[claimItemElmt.service.packagetype][claimItemElmt.service.id]["tarif"]
            
        #     if claimServiceElmt.service.packagetype not in invoiceElemtTotal :
        #         invoiceElemtTotal[claimServiceElmt.service.packagetype] = defaultdict(int)

        #     invoiceElemtTotal[claimItemElmt.service.packagetype+"QtyTotalV"] += claimItemElmt.qty_provided
        #     invoiceElemtTotal[claimItemElmt.service.packagetype+"QtyValuatedV"] += int(invoiceElemtList[claimItemElmt.service.packagetype][claimItemElmt.service.id]["qty"]['valuated'])
        #     invoiceElemtTotal[claimItemElmt.service.packagetype+"MtnValideV"] += invoiceElemtList[claimItemElmt.service.packagetype][claimItemElmt.service.id]["qty"]['sum']
        #     MtnNotValideV = 0
        #     if invoiceElemtTotal[claimItemElmt.service.packagetype+"MontantRecueTotal"] - invoiceElemtTotal[claimItemElmt.service.packagetype+"MtnValide"] > 0:
        #         MtnNotValideV = invoiceElemtTotal[claimItemElmt.service.packagetype+"MontantRecueTotal"] - invoiceElemtTotal[claimItemElmt.service.packagetype+"MtnValide"]
        #     invoiceElemtTotal[claimItemElmt.service.packagetype+"MtnNotValideV"] = MtnNotValideV
        #     invoiceElemtTotal["QtyTotalV"] += claimItemElmt.qty_provided
    
    invoiceElemtTotal["PQtyValuatedV"]=0
    invoiceElemtTotal["PMontantRecueTotalV"] = 0
    invoiceElemtTotal["PMtnNotValideV"] = 0
    invoiceElemtTotal["PMtnValideV"] = 0
    invoiceElemtTotal["FMontantRecueTotalV"] = 0
    invoiceElemtTotal["FQtyValuatedV"] = 0
    invoiceElemtTotal["FMtnNotValideV"] = 0
    invoiceElemtTotal["FMtnValideV"] = 0 
    invoiceElemtTotal["SQtyValuatedV"] = 0
    invoiceElemtTotal["SMontantRecueTotalV"] = 0
    invoiceElemtTotal["SMtnNotValideV"] = 0
    invoiceElemtTotal["SMtnValideV"] = 0
    
    # print ("{:<5} {:<5} {:<40} {:<10} {:<10} {:<10} {:<10} {:<20}".format('type','id','name','Code','tarif','qty', 'Montant Recus','Qty Validated'))
    # print("invoiceElemtList ", invoiceElemtList)
    for typeList,v in invoiceElemtList.items():
        for id in v:
            montantNonValide = 0
            # Correction des chiffres negatif : -- Si un montant est negatif ca veut dire que le montant valuated est superieur a la somme des sous-services / services
            # if v[id]['MontantRecue'] - v[id]['qty']['sum'] > 0 :
            montantNonValide = v[id]['MontantRecue'] - v[id]['qty']['sum']
            if typeList=="P":
                invoiceElemtListP.append(dict(
                    name=v[id]['name'],
                    code=v[id]['code'],
                    tarif=str("{:,.0f}".format(v[id]['tarif'])),
                    nbrFacture = str(int(v[id]['qty']['all'])),
                    mtnFactureRecues= str("{:,.0f}".format(v[id]['MontantRecue'])),
                    nbFactureValides= str(v[id]['qty']['valuated']),
                    montantNonValide = str("{:,.0f}".format(montantNonValide)),
                    montantValide =  str("{:,.0f}".format(v[id]['qty']['sum']))
                    ))
                
                invoiceElemtTotal["PMontantRecueTotalV"] += v[id]['MontantRecue']
                invoiceElemtTotal["PQtyValuatedV"] += v[id]['qty']['valuated']
                PMtnNotValideV = 0
                if v[id]['MontantRecue'] - v[id]['qty']['sum'] > 0:
                    PMtnNotValideV = v[id]['MontantRecue'] - v[id]['qty']['sum']
                invoiceElemtTotal["PMtnNotValideV"] += PMtnNotValideV
                invoiceElemtTotal["PMtnValideV"] += v[id]['qty']['sum']

            if typeList=="F":
                invoiceElemtListF.append(dict(
                    name=v[id]['name'],
                    code=v[id]['code'],
                    tarif=str("{:,.0f}".format(v[id]['tarif'])),
                    nbrFacture = str(int(v[id]['qty']['all'])),
                    mtnFactureRecues= str("{:,.0f}".format(v[id]['MontantRecue'])),
                    nbFactureValides= str(v[id]['qty']['valuated']),
                    montantNonValide = str("{:,.0f}".format(montantNonValide)),
                    montantValide =  str("{:,.0f}".format(v[id]['qty']['sum']))
                    ))
                invoiceElemtTotal["FMontantRecueTotalV"] += v[id]['MontantRecue']
                invoiceElemtTotal["FQtyValuatedV"] += v[id]['qty']['valuated']
                FMtnNotValideV = 0
                if v[id]['MontantRecue'] - v[id]['qty']['sum'] > 0:
                    FMtnNotValideV = v[id]['MontantRecue'] - v[id]['qty']['sum']
                invoiceElemtTotal["FMtnNotValideV"] += FMtnNotValideV
                invoiceElemtTotal["FMtnValideV"] += v[id]['qty']['sum']

            
            if typeList=="S":
                invoiceElemtListS.append(dict(
                    name=v[id]['name'],
                    code=v[id]['code'],
                    tarif=str("{:,.0f}".format(v[id]['tarif'])),
                    nbrFacture = str(int(v[id]['qty']['all'])),
                    mtnFactureRecues= str("{:,.0f}".format(v[id]['MontantRecue'])),
                    nbFactureValides= str(v[id]['qty']['valuated']),
                    montantNonValide = str("{:,.0f}".format(v[id]['MontantRecue'] - v[id]['qty']['sum'])),
                    montantValide =  str("{:,.0f}".format(v[id]['qty']['sum']))
                    ))
                invoiceElemtTotal["SMontantRecueTotalV"] += v[id]['MontantRecue']
                invoiceElemtTotal["SQtyValuatedV"] += v[id]['qty']['valuated']
                invoiceElemtTotal["SMtnNotValideV"] += v[id]['MontantRecue'] - v[id]['qty']['sum']
                invoiceElemtTotal["SMtnValideV"] += v[id]['qty']['sum']

            # print("{:<5} {:<5} {:<40} {:<10} {:<10} {:<10} {:<10} {:<10}".format(
                # typeList, id, v[id]['name'], v[id]['code'], v[id]['tarif'],v[id]['qty']['all'], v[id]['MontantRecue'],v[id]['qty']['valuated']
                # ))

    ## Calcaulating of each invoiceElemtTotal
    # invoiceElemtTotal["NbFactureValideTotal"] = invoiceElemtTotal["FQtyValuatedV"] + invoiceElemtTotal["SQtyValuatedV"] + invoiceElemtTotal["PQtyValuatedV"]
    invoiceElemtTotal["NbFactureValideTotal"] = invoiceElemtTotal["FQtyValuatedV"] + invoiceElemtTotal["PQtyValuatedV"]
    invoiceElemtTotal["NbFactureValideTotal"] = "{:,.0f}".format(invoiceElemtTotal["NbFactureValideTotal"])
    invoiceElemtTotal["FQtyValuated"] = "{:,.0f}".format(invoiceElemtTotal["FQtyValuatedV"])
    invoiceElemtTotal["SQtyValuated"] = "{:,.0f}".format(invoiceElemtTotal["SQtyValuatedV"])
    invoiceElemtTotal["PQtyValuated"] = "{:,.0f}".format(invoiceElemtTotal["PQtyValuatedV"])
    invoiceElemtTotal["FQtyTotal"] = "{:,.0f}".format(invoiceElemtTotal["FQtyTotalV"])
    invoiceElemtTotal["SQtyTotal"] = "{:,.0f}".format(invoiceElemtTotal["SQtyTotalV"])
    invoiceElemtTotal["PQtyTotal"] = "{:,.0f}".format(invoiceElemtTotal["PQtyTotalV"])

    invoiceElemtTotal["MtnValideTotal"] = "{:,.0f}".format(invoiceElemtTotal["FMtnValideV"]+invoiceElemtTotal["SMtnValideV"]+invoiceElemtTotal["PMtnValideV"])
    invoiceElemtTotal_MtnValideTotal += invoiceElemtTotal["FMtnValideV"]+invoiceElemtTotal["SMtnValideV"]+invoiceElemtTotal["PMtnValideV"]
    invoiceElemtTotal["FMtnValide"] = "{:,.0f}".format(invoiceElemtTotal["FMtnValideV"])
    invoiceElemtTotal["SMtnValide"] = "{:,.0f}".format(invoiceElemtTotal["SMtnValideV"])
    invoiceElemtTotal["PMtnValide"] = "{:,.0f}".format(invoiceElemtTotal["PMtnValideV"])
    invoiceElemtTotal["MtnNonValideTotal"] = "{:,.0f}".format(invoiceElemtTotal["FMtnNotValideV"]+invoiceElemtTotal["SMtnNotValideV"]+invoiceElemtTotal["PMtnNotValideV"])
    invoiceElemtTotal["FMtnNotValide"] = "{:,.0f}".format(invoiceElemtTotal["FMtnNotValideV"])
    invoiceElemtTotal["SMtnNotValide"] = "{:,.0f}".format(invoiceElemtTotal["SMtnNotValideV"])
    invoiceElemtTotal["PMtnNotValide"] = "{:,.0f}".format(invoiceElemtTotal["PMtnNotValideV"])

    invoiceElemtTotal["MontantRecueTotal"] =  "{:,.0f}".format(invoiceElemtTotal["PMontantRecueTotalV"]+invoiceElemtTotal["FMontantRecueTotalV"]+invoiceElemtTotal["SMontantRecueTotalV"])
    invoiceElemtTotal_MontantRecueTotal += invoiceElemtTotal["PMontantRecueTotalV"]+invoiceElemtTotal["FMontantRecueTotalV"]+invoiceElemtTotal["SMontantRecueTotalV"]
    invoiceElemtTotal["PMontantRecueTotal"] = "{:,.0f}".format(invoiceElemtTotal["PMontantRecueTotalV"])
    invoiceElemtTotal["SMontantRecueTotal"] = "{:,.0f}".format(invoiceElemtTotal["SMontantRecueTotalV"])
    invoiceElemtTotal["FMontantRecueTotal"] = "{:,.0f}".format(invoiceElemtTotal["FMontantRecueTotalV"])

    invoiceElemtTotal["QtyTotal"] = "{:,.0f}".format(invoiceElemtTotal["QtyTotalV"])

    dictBase["prestationForfaitaire"] = invoiceElemtListF
    dictBase["prestationPlafonnees"] = invoiceElemtListP
    dictBase["prestationsNonMedicales"] = invoiceElemtListS
    dictBase["invoiceElemtTotal"] = invoiceElemtTotal
    dictBase["invoiceElemtTotal"]["MontantRecueTotal"] =  "{:,.0f}".format(invoiceElemtTotal_MontantRecueTotal)
    dictBase["invoiceElemtTotal"]["MtnValideTotal"] =  "{:,.0f}".format(invoiceElemtTotal_MtnValideTotal)
    dictBase["MontnRecueTotal"] =  "{:,.0f}".format(invoiceElemtTotal_MontantRecueTotal)
    dictBase["MtnValideTotal"] =  "{:,.0f}".format(invoiceElemtTotal_MtnValideTotal)
    
    dictBase["texte1"] = "Rapporté à ________ le ..../..../20__"
    dictBase["texte2"] = "Vérifié à _____ le ..../..../20__"
    dictBase["texte3"] = "Validé le ____________"
    dictBase["valeur1"] = "Responsable de l'ONG (Association)\n\n\n\n\n\n\n\n\n\n\n\n"
    dictBase["valeur2"] = "Auditeur TC/GOPA HF Région..."
    dictBase["valeur3"] = "Validation TEAM LEADER COPA/HF"
    print(dictBase)
    
    return dictBase