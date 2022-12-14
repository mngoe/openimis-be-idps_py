import graphene
from graphene_django import DjangoObjectType
from idps.models import PerformanceCriteria
from core.schema import TinyInt, SmallInt, OpenIMISMutation
from graphene import InputObjectType
from django.core.exceptions import ValidationError, PermissionDenied
from django.contrib.auth.models import AnonymousUser
from django.utils.translation import gettext as _
from core.utils import TimeUtils
from location import models as location_models

class PerformanceCriteriaGQLType(DjangoObjectType):

    class Meta:
        model = PerformanceCriteria
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "id":["exact"],
            "health_facility":["exact"],
            "date_from":["exact","lt","lte","gt","gte"],
            "date_to":["exact","lt","lte","gt","gte"]
        }
class Query(graphene.ObjectType):
    all_criteria = graphene.List(PerformanceCriteriaGQLType)
    health_facility_filter = graphene.List(PerformanceCriteriaGQLType, hfid= graphene.Int())
    interval_filter = graphene.List(PerformanceCriteriaGQLType, start_date=graphene.Date())

    def resolve_all_criteria(self,info, **kwargs):
        return PerformanceCriteria.objects.all()

    def resolve_health_facility_filter(self,info,hfid,**kwargs):
        return PerformanceCriteria.objects.filter(health_facility = hfid)

    def resolve_interval_filter(self,info,start_date,hfid,**kwarg):
        return PerformanceCriteria.objects.filter(date_from=start_date,health_facility=hfid)




class CriteriaInputType(OpenIMISMutation.Input):
    id = graphene.Int(required=False)
    date_from = graphene.Date(required=False)
    date_to = graphene.Date(required=False)
    health_facility = graphene.Int(required=False)
    promptness =  graphene.Int(required=False)
    medecine_availability = graphene.Int(required=False)
    qualified_personnel =  graphene.Int(required=False)
    garbagecan_availability = graphene.Int(required=False)
    rooms_cleaness = graphene.Int(required=False)
    waste_separation = graphene.Int(required=False)
    functionals_toilets =  graphene.Int(required=False)
    sterilization_tools = graphene.Int(required=False)
    is_validated = graphene.Boolean(required=False)
    

class CreateCriteriaMutation(OpenIMISMutation):
    """
    Create a new criteria, preventing duplicate
    """
    _mutation_module = "idps"
    _mutation_class = "CreateCriteriaMutation"

    class Input(CriteriaInputType):
        pass

    @classmethod
    def async_mutate(cls, user, **data):
        errors = []
        criteria_range = PerformanceCriteria.objects.filter(
        date_from = data['date_from'],
        date_to = data['date_to'],
        health_facility = data['health_facility'])
        try:
            if criteria_range :
                errors.append({
                    'message','duplicate records not allowed on the same period'
                })
                return errors
            else:
                data['audit_user_id'] = user.id_for_audit 
                data['record_date'] = TimeUtils.now()
                criteria = PerformanceCriteria.objects.create(**data)
                criteria.save()
                return criteria  
        except Exception as exc:
            return [{
                'message': _("idps.mutation.failed_to_create_criteria"),
                'detail': str(exc)}]
 

class UpdateCriteriaMutation(OpenIMISMutation):
    """
    This mutation will update a criteria, 
    and ensure that for a define period only 1 criteria  is set as validated
    """
    _mutation_module = "idps"
    _mutation_class = "UpdateCriteriaMutation"

    class Input(CriteriaInputType):
        pass

    @classmethod
    def async_mutate(cls, user, **data): 
        range_date_from = data['date_from'] 
        range_year_from = range_date_from.year
        range_month_from = range_date_from.month 

        criteria_to_update = PerformanceCriteria.objects.get(pk=data['id'])
       

        period_criteria  = PerformanceCriteria.objects.filter(
            date_from__year=range_year_from,
            date_from__month=range_month_from)
        try:
            if data['is_validated'] == True:
                for criteria in period_criteria:
                    if criteria.is_validated == True:
                        criteria.is_validated = False
                        criteria.record_date = TimeUtils.now()
                        criteria.save()
                    else: None
            data['audit_user_id'] = user.id_for_audit 
            criteria_to_update.record_date = TimeUtils.now()
            criteria_to_update.is_validated = data['is_validated']
            criteria_to_update.save()

            return  criteria_to_update 
        except Exception as exc:
            return [{
                'message': ("idps.mutation.failed_to_update_criteria"),
                'detail': str(exc)}]

class Mutation(graphene.ObjectType):
    create_criteria = CreateCriteriaMutation.Field()
    update_criteria = UpdateCriteriaMutation.Field()



