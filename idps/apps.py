from django.apps import AppConfig

MODULE_NAME = "idps"

# The performance criteria evaluate a health facility and idps has no right of its
# own: reading them defaults to the health-facility read right, recording or
# validating them to the health-facility edit right. Override through
# ModuleConfiguration("idps") when dedicated rights are created.
DEFAULT_CFG = {
    "gql_query_criteria_perms": ["121101"],
    "gql_mutation_create_criteria_perms": ["121103"],
    "gql_mutation_update_criteria_perms": ["121103"],
}


class IdpsConfig(AppConfig):
    name = MODULE_NAME

    gql_query_criteria_perms = []
    gql_mutation_create_criteria_perms = []
    gql_mutation_update_criteria_perms = []

    def __load_config(self, cfg):
        for field in cfg:
            if hasattr(IdpsConfig, field):
                setattr(IdpsConfig, field, cfg[field])

    def ready(self):
        from core.models import ModuleConfiguration

        cfg = ModuleConfiguration.get_or_default(MODULE_NAME, DEFAULT_CFG)
        self.__load_config(cfg)
