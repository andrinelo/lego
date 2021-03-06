from django.utils.timezone import is_aware, make_naive
from pytz import utc
from stream_framework.activity import Activity as SFActivity
from stream_framework.activity import AggregatedActivity as SFAggregatedActivity
from stream_framework.utils import make_list_unique


class Activity(SFActivity):
    """
    Custom activity class
    Stores actor, object and target as a content_identifier string.

    Actor - The user or object that performs an action.
    Object - The object the feed activity represents, this could be a comment.
    Target - The object the activity relates to, this is typically the object that was commented on.
    """

    def __init__(self, actor, verb, object, target=None, time=None, extra_context=None):
        # Make time native if it is timezone aware.
        if time and is_aware(time):
            time = make_naive(time, timezone=utc)
        super().__init__(actor, verb, object, target, time, extra_context)

    def _set_object_or_id(self, field, object_):
        id_field = '%s_id' % field
        content_type_field = '%s_content_type' % field

        if isinstance(object_, int):
            setattr(self, id_field, int(object_))
            setattr(self, content_type_field, None)
        elif isinstance(object_, str):
            content_type, object_id = object_.split('-')
            setattr(self, id_field, int(object_id))
            setattr(self, content_type_field, content_type)
        elif object_ is None:
            setattr(self, id_field, None)
            setattr(self, content_type_field, None)
        else:
            setattr(self, id_field, int(object_.id))
            setattr(
                self, content_type_field, f'{object_._meta.app_label}.{object_._meta.model_name}'
            )

    @property
    def actor(self):
        if self.actor_content_type and self.actor_id:
            return f'{self.actor_content_type}-{self.actor_id}'

    @property
    def object(self):
        if self.object_content_type and self.object_id:
            return f'{self.object_content_type}-{self.object_id}'

    @property
    def target(self):
        if self.target_content_type and self.target_id:
            return f'{self.target_content_type}-{self.target_id}'

    @property
    def activity_id(self):
        return str(self.serialization_id)


class AggregatedActivity(SFAggregatedActivity):
    max_aggregated_activities_length = 10

    def __init__(self, group, activities=None, created_at=None, updated_at=None, **kwargs):
        super().__init__(group, activities, created_at, updated_at)

    @property
    def actor_ids(self):
        return make_list_unique([a.actor for a in self.activities])

    @property
    def activity_id(self):
        return str(self.serialization_id)


class NotificationActivity(AggregatedActivity):
    def __init__(
        self, group, activities=None, created_at=None, updated_at=None, read_at=None, seen_at=None
    ):

        super().__init__(
            group=group, activities=activities, created_at=created_at, updated_at=updated_at
        )

        self.read_at = read_at
        self.seen_at = seen_at
