from idps.reports import indicator_report 
from idps.reports.indicator_report import indicator_report_query
from idps.reports import invoice_report 
from idps.reports.invoice_report import invoice_report_query

report_definitions = [
    {
        "name": "indicator_report",
        "engine": 0,
        "default_report": indicator_report.template,
        "description": "indicator report",
        "module": "idps",
        "python_query": indicator_report_query,
        "permission": ["131215"],
    },
    {
        "name": "invoice_report",
        "engine": 0,
        "default_report": invoice_report.template,
        "description": "invoice_report",
        "module": "idps",
        "python_query": invoice_report_query,
        "permission": ["131215"],
    }
    ]