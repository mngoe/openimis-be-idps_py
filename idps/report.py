from distutils.command import upload
from idps.models import invoice_report_query

from idps.report_templates import invoiceReport

report_definitions = [
    {
        "name": "invoice_report",
        "engine": 0,
        "default_report": invoiceReport.template,
        "description": "Etat de paiements",
        "module": "idps",
        "python_query": invoice_report_query,
        "permission": ["131215"],
    },
    # {
    #     "name": "indicator_report",
    #     "engine": 0,
    #     "default_report": invoiceReport.template,
    #     "description": "Rapport des indicateurs",
    #     "module": "idps",
    #     "python_query": invoice_report_query,
    #     "permission": ["131215"],
    # }
]