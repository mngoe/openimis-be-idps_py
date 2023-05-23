from core import ExtendedConnection
from core.schema import TinyInt, SmallInt, OpenIMISMutation, OrderedDjangoFilterConnectionField
from core.utils import TimeUtils
from django.db.models import Q
import graphene
from graphene import InputObjectType
import graphene_django_optimizer as gql_optimizer
from graphene_django import DjangoObjectType
from idps.models import PerformanceCriteria
from django.core.exceptions import ValidationError, PermissionDenied
from django.contrib.auth.models import AnonymousUser
from django.utils.translation import gettext as _
from location import models as location_models


class PerformanceCriteriaGQLType(DjangoObjectType):

    class Meta:
        model = PerformanceCriteria
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "id":["exact"],
            "health_facility":["exact"],
            "period":["exact","lt","lte","gt","gte"],
            "hf_score":["exact"]
        }
        interfaces = (graphene.relay.Node,)
        connection_class = ExtendedConnection

class Query(graphene.ObjectType):
    all_criteria = OrderedDjangoFilterConnectionField(PerformanceCriteriaGQLType)

    def resolve_all_criteria(self, info, **kwargs):
        filters = []
        ids = kwargs.get('id', None)
        if ids:
            filters.append(Q(id=ids))
        return gql_optimizer.query(PerformanceCriteria.objects.filter(*filters).all(), info)





class CriteriaInputType(OpenIMISMutation.Input):
    id = graphene.Int(required=False)
    period = graphene.String(required=False)
    health_facility = graphene.Int(required=False)
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
        data.pop('client_mutation_label', None)
        data.pop('client_mutation_id', None)
        criteria_filter = PerformanceCriteria.objects.filter(
        period = data["period"],
        health_facility = data['health_facility'])
        try:
            if criteria_filter :
                for criteria in  criteria_filter:
                    if criteria.is_validated == True:
                        criteria.is_validated = False
                        criteria.save()
                    else: None
                
                data['audit_user_id'] = user.id_for_audit
                data['record_date'] = TimeUtils.now()
                new_criteria = PerformanceCriteria.objects.create(**data)
                new_criteria.save()

                return None
            else:
                data['audit_user_id'] = user.id_for_audit
                data['record_date'] = TimeUtils.now()
                criteria = PerformanceCriteria.objects.create(**data)
                criteria.save()
                return None  
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
        data.pop('client_mutation_label', None)
        data.pop('client_mutation_id', None)
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
