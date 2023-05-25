from idps.reports import indicator_report 
from idps.reports.indicator_report import indicator_report_query

report_definitions = [
    {
        "name": "indicator_report",
        "engine": 0,
        "default_report": indicator_report.template,
        "description": "indicator report",
        "module": "idps",
        "python_query": indicator _report_query,
        "permission": ["131215"],
    },
    ]