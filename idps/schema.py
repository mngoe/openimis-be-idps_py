import graphene
from graphene_django import DjangoObjectType
from idps.models import PerformanceCriteria

#lecture des donnes 

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

    def resolve_interval_filter(self,info,start_date ,**kwarg):
        return PerformanceCriteria.objects.filter(date_from=start_date)