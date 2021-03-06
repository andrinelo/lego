from __future__ import absolute_import

import os
import sys

import celery  # noqa
from cassandra.cqlengine import connection
from cassandra.cqlengine.connection import cluster as cql_cluster
from cassandra.cqlengine.connection import session as cql_session
from celery.schedules import crontab
from celery.signals import beat_init, eventlet_pool_started, setup_logging, worker_process_init
from django.conf import settings
from structlog import get_logger

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lego.settings')

app = celery.Celery('lego')
logger = get_logger()


@eventlet_pool_started.connect()
@worker_process_init.connect()
@beat_init.connect()
def celery_init(*args, **kwargs):
    """
    Initialize a clean Cassandra connection.
    """
    try:
        if cql_cluster is not None:
            cql_cluster.shutdown()
        if cql_session is not None:
            cql_session.shutdown()
        connection.setup(
            hosts=settings.STREAM_CASSANDRA_HOSTS,
            consistency=settings.STREAM_CASSANDRA_CONSISTENCY_LEVEL,
            default_keyspace=settings.STREAM_DEFAULT_KEYSPACE, **settings.CASSANDRA_DRIVER_KWARGS
        )
    except Exception:  # noqa
        logger.exception('celery_cassandra_signal_failure')
        sys.exit(1)

    from lego.apps.stats import analytics_client
    analytics_client.default_client = None
    analytics_client.setup_analytics()


@app.on_configure.connect()
def on_configure(*args, **kwargs):

    import raven
    from raven.contrib.celery import register_signal, register_logger_signal

    client = raven.Client()

    # register a custom filter to filter out duplicate logs
    register_logger_signal(client)

    # hook into the Celery error handler
    register_signal(client)


@setup_logging.connect()
def on_setup_logging(**kwargs):
    """
    This prevents celery from tampering with our logging config.
    """
    pass


app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
schedule = {
    'check-for-bump-after-penalty-expiration': {
        'task': 'lego.apps.events.tasks.check_events_for_registrations_with_expired_penalties',
        'schedule': crontab(minute='*/5')
    },
    'bump-users-to-new-pools-before-activation': {
        'task': 'lego.apps.events.tasks.bump_waiting_users_to_new_pool',
        'schedule': crontab(minute='*/30')
    },
    'notify_user_when_payment_soon_overdue': {
        'task': 'lego.apps.events.tasks.notify_user_when_payment_soon_overdue',
        'schedule': crontab(hour=9, minute=0)
    },
    'notify_event_creator_when_payment_overdue': {
        'task': 'lego.apps.events.tasks.notify_event_creator_when_payment_overdue',
        'schedule': crontab(hour=9, minute=0)
    },
    'sync-external-systems': {
        'task': 'lego.apps.external_sync.tasks.sync_external_systems',
        'schedule': crontab(hour='*', minute=0)
    },
    'check-that-pool-counters-match-registration-number': {
        'task': 'lego.apps.events.tasks.check_that_pool_counters_match_registration_number',
        'schedule': crontab(hour='*', minute=0)
    },
    'notify_user_about_new_survey': {
        'task': 'lego.apps.surveys.tasks.send_survey_mail',
        'schedule': crontab(minute='*/10')
    }
}

app.conf.update(
    beat_schedule=schedule, result_backend=None, task_track_started=True, task_serializer='pickle',
    worker_disable_rate_limits=True, task_ignore_result=True, task_acks_late=False,
    worker_hijack_root_logger=False, worker_redirect_stdouts=False,
    accept_content=['pickle', 'json']
)
