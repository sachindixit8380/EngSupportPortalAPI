"""Web application responsible for managing state information about the data
pipeline."""

from endpoints import app

#from flask_debugtoolbar import DebugToolbarExtension
#from flask_debugtoolbar_lineprofilerpanel.profile import line_profile

from os import listdir
from os.path import isfile, join

from endpoints.late_data import HTMLLateDataEndpoint
from endpoints.ignore_late_data import IgnoreLateData
from endpoints.job_control import JobControl
from endpoints.state import StateEndpoint
from endpoints.index import IndexEndpoint
from endpoints.status import StatusEndpoint
from endpoints.system_info import SystemInfoEndpoint
from endpoints.job_run import JobRunEndpoint
from endpoints.job_filter import JobFilterEndpoint
from endpoints.job_detail import JobDetailEndpoint
from endpoints.job_edit import JobEdit
from endpoints.job_schedule_edit import JobScheduleEdit
from endpoints.schedule_job import ScheduleJob
from endpoints.job_delete import JobDelete
from endpoints.job_schedule_delete import JobScheduleDelete
from endpoints.load_log import LoadLogEndpoint
from endpoints.job_rule import JobRuleEndpoint
from endpoints.permission import PermissionEndpoint
from endpoints.job_conflict import JobConflictEndpoint
from endpoints.mq_message import MQMessageEndpoint
from endpoints.vertica_sessions import VerticaSessionsEndpoint
from endpoints.bad_records import BadRecordsEndpoint
from endpoints.adhoc_job import AdhocJob
from endpoints.hdfs import HdfsOperations
from endpoints.audit_log_search import AuditLogSearchEndpoint
from endpoints.scheduler_dashboard import SchedulerDashboardEndpoint
from endpoints.job_dependencies import JobDependenciesEndpoint, JobDependentsEndpoint
from endpoints.artifacts import ArtifactsEndpoint
from endpoints.niteowl_rule_results import NiteOwlRuleResultsEndpoint
from endpoints.dependency_graph import DependencyGraphEndpoint
from endpoints.continuous_job import ContinuousJob
from endpoints.ajax_ebee import AjaxEbeeEndpoint
from endpoints.alerts import AlertsEndpoint
from endpoints.alert_constraints import AlertConstraintsEndpoint
from endpoints.alert_filters import AlertFiltersEndpoint
from endpoints.help_dialogs import HelpDialogEndpoints

# XXX Set global variables, not actually an endpoint
from endpoints.globals import inject_template_globals


def get_application():
    return app

if __name__ == '__main__':
    import endpoints.database

    app.debug = True
    # app.config['DEBUG_TB_PANELS'] = [
    #     'flask_debugtoolbar.panels.versions.VersionDebugPanel',
    #     'flask_debugtoolbar.panels.timer.TimerDebugPanel',
    #     'flask_debugtoolbar.panels.headers.HeaderDebugPanel',
    #     'flask_debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
    #     'flask_debugtoolbar.panels.template.TemplateDebugPanel',
    #     'flask_debugtoolbar.panels.sqlalchemy.SQLAlchemyDebugPanel',
    #     'flask_debugtoolbar.panels.logger.LoggingPanel',
    #     'flask_debugtoolbar.panels.profiler.ProfilerDebugPanel',
    #     # Add the line profiling
    #     'flask_debugtoolbar_lineprofilerpanel.panels.LineProfilerPanel'
    # ]
    # app.config['DEBUG_TB_TEMPLATE_EDITOR_ENABLED'] = True
    # toolbar = DebugToolbarExtension(app)
    scss_path = 'endpoints/static/scss/'
    scss_files = [scss_path+f for f in listdir(scss_path) if isfile(join(scss_path, f)) and f.endswith(".scss")]
    scss_files.append("endpoints/static/scss/templates/base.scss")
    app.run(host='0.0.0.0',
            port=5000,
            extra_files=tuple(scss_files))
