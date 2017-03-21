from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from lego.apps.events.models import Event, Registration
from lego.apps.events.tasks import (async_register, bump_waiting_users_to_new_pool,
                                    check_events_for_registrations_with_expired_penalties)
from lego.apps.events.tests.utils import get_dummy_users
from lego.apps.users.models import AbakusGroup, Penalty


class PoolActivationTestCase(APITestCase):
    fixtures = ['initial_abakus_groups.yaml',
                'test_users.yaml',
                'test_events.yaml',
                'test_companies.yaml']

    _test_pools_data = [
        {
            'name': 'TESTPOOL1',
            'capacity': 2,
            'activation_date': timezone.now(),
            'permission_groups': [1]
        },
    ]

    def setUp(self):
        self.event = Event.objects.get(title='POOLS_NO_REGISTRATIONS')
        self.event.start_time = timezone.now() + timedelta(days=1)
        self.event.merge_time = timezone.now() + timedelta(hours=12)
        self.event.save()

        self.pool_one = self.event.pools.get(name='Abakusmember')
        self.pool_two = self.event.pools.get(name='Webkom')

        self.pool_one.activation_date = timezone.now() - timedelta(days=1)
        self.pool_one.capacity = 1
        self.pool_one.save()

        self.pool_two.activation_date = timezone.now() + timedelta(minutes=30)
        self.pool_two.capacity = 2
        self.pool_two.save()

    def tearDown(self):
        from django_redis import get_redis_connection
        get_redis_connection("default").flushall()

    def test_users_are_bumped_before_pool_activation(self):
        """" Tests that users are bumped right before pool activation """
        users = get_dummy_users(3)

        for user in users:
            AbakusGroup.objects.get(name='Webkom').add_user(user)
            registration = Registration.objects.get_or_create(event=self.event,
                                                              user=user)[0]
            self.event.register(registration)

        self.assertEqual(self.pool_two.registrations.count(), 0)
        bump_waiting_users_to_new_pool()
        self.assertEqual(self.pool_two.registrations.count(), 2)

    def test_users_are_bumped_after_pool_activation(self):
        """ Tests that users are bumped right after pool activation. """
        users = get_dummy_users(3)

        for user in users:
            AbakusGroup.objects.get(name='Webkom').add_user(user)
            registration = Registration.objects.get_or_create(event=self.event,
                                                              user=user)[0]
            self.event.register(registration)

        self.pool_two.activation_date = timezone.now() - timedelta(minutes=30)
        self.pool_two.save()

        bump_waiting_users_to_new_pool()

        self.assertEqual(self.pool_two.registrations.count(), 2)

    def test_too_many_users_waiting_for_bump(self):
        """ Tests that only 2 users are bumped to a new pool with capacity = 2. """
        users = get_dummy_users(4)
        registrations = []

        for user in users:
            AbakusGroup.objects.get(name='Webkom').add_user(user)
            registration = Registration.objects.get_or_create(event=self.event,
                                                              user=user)[0]
            self.event.register(registration)
            registrations.append(Registration.objects.get(id=registration.id))

        bump_waiting_users_to_new_pool()

        self.assertEqual(self.pool_two.registrations.count(), 2)
        self.assertIsNone(registrations[3].pool)

    def test_isnt_bumped_without_permission(self):
        """ Tests that a waiting user isnt bumped to a pool it cant access. """
        users = get_dummy_users(2)

        for user in users:
            AbakusGroup.objects.get(name='Abakus').add_user(user)
            registration = Registration.objects.get_or_create(event=self.event,
                                                              user=user)[0]
            self.event.register(registration)

        bump_waiting_users_to_new_pool()

        self.assertEqual(self.pool_two.registrations.count(), 0)
        self.assertEqual(self.event.waiting_registrations.count(), 1)

    def test_isnt_bumped_with_penalties(self):
        """ Users should not be bumped if they have 3 penalties. """
        self.event.start_time = timezone.now() + timedelta(days=1)
        self.event.merge_time = timezone.now() + timedelta(hours=12)
        self.event.save()

        self.pool_one.activation_date = timezone.now() - timedelta(days=1)
        self.pool_one.save()

        self.pool_two.activation_date = timezone.now() + timedelta(minutes=30)
        self.pool_two.save()

        users = get_dummy_users(2)

        Penalty.objects.create(
            user=users[1], reason='test', weight=3, source_event=self.event,
        )

        for user in users:
            AbakusGroup.objects.get(name='Webkom').add_user(user)
            registration = Registration.objects.get_or_create(event=self.event,
                                                              user=user)[0]
            self.event.register(registration)

        bump_waiting_users_to_new_pool()

        self.assertEqual(self.pool_two.registrations.count(), 0)
        self.assertEqual(self.event.waiting_registrations.count(), 1)

    def test_isnt_bumped_if_activation_is_far_into_the_future(self):
        """ Users should not be bumped if the pool is activated more than
            35 minutes in the future. """
        self.pool_two.activation_date = timezone.now() + timedelta(minutes=40)
        self.pool_two.save()

        users = get_dummy_users(2)

        for user in users:
            AbakusGroup.objects.get(name='Webkom').add_user(user)
            registration = Registration.objects.get_or_create(event=self.event,
                                                              user=user)[0]
            self.event.register(registration)

        bump_waiting_users_to_new_pool()

        self.assertEqual(self.pool_two.registrations.count(), 0)
        self.assertEqual(self.event.waiting_registrations.count(), 1)

    def test_isnt_bumped_if_activation_is_far_into_the_past(self):
        """ Users should not be bumped if the pool is activated more than
            35 minutes in the past. """
        users = get_dummy_users(2)

        for user in users:
            AbakusGroup.objects.get(name='Abakus').add_user(user)
            registration = Registration.objects.get_or_create(event=self.event,
                                                              user=user)[0]
            self.event.register(registration)

        self.pool_two.activation_date = timezone.now() - timedelta(minutes=40)
        self.pool_two.save()
        AbakusGroup.objects.get(name='Webkom').add_user(users[1])

        bump_waiting_users_to_new_pool()

        self.assertEqual(self.pool_two.registrations.count(), 0)
        self.assertEqual(self.event.waiting_registrations.count(), 1)


class PenaltyExpiredTestCase(TestCase):
    fixtures = ['initial_abakus_groups.yaml',
                'test_users.yaml',
                'test_events.yaml',
                'test_companies.yaml']

    def setUp(self):
        self.event = Event.objects.get(title='POOLS_NO_REGISTRATIONS')
        self.event.heed_penalties = True
        self.event.start_time = timezone.now() + timedelta(days=1)
        self.event.merge_time = timezone.now() + timedelta(hours=12)
        self.event.save()
        for pool in self.event.pools.all():
            pool.activation_time = timezone.now() - timedelta(days=1)
            pool.capacity = 1
            pool.save()

    def tearDown(self):
        from django_redis import get_redis_connection
        get_redis_connection("default").flushall()

    def make_penalty_expire(self, penalty):
        penalty.created_at = timezone.now() - timedelta(days=365)
        penalty.save()

    def test_is_automatically_bumped_after_penalty_expiration(self):
        """ Tests that the user that registered with penalties is bumped
            by the task after penalty expiration"""

        user = get_dummy_users(1)[0]
        AbakusGroup.objects.get(name='Abakus').add_user(user)

        p1 = Penalty.objects.create(user=user, reason='test', weight=3, source_event=self.event)

        registration = Registration.objects.get_or_create(event=self.event, user=user)[0]
        async_register(registration.id)

        self.make_penalty_expire(p1)
        check_events_for_registrations_with_expired_penalties.delay()

        self.assertIsNotNone(Registration.objects.get(id=registration.id).pool)
        self.assertEqual(self.event.number_of_registrations, 1)

    def test_is_bumped_with_multiple_penalties(self):
        """ Tests that a user is bumped when going from 4 to 2 active penalties"""

        user = get_dummy_users(1)[0]
        AbakusGroup.objects.get(name='Abakus').add_user(user)

        p1 = Penalty.objects.create(user=user, reason='test', weight=2, source_event=self.event)
        Penalty.objects.create(user=user, reason='test2', weight=2, source_event=self.event)

        registration = Registration.objects.get_or_create(event=self.event, user=user)[0]
        async_register(registration.id)

        self.make_penalty_expire(p1)
        check_events_for_registrations_with_expired_penalties.delay()

        self.assertIsNotNone(Registration.objects.get(id=registration.id).pool)
        self.assertEqual(self.event.number_of_registrations, 1)

    def test_isnt_bumped_with_too_many_penalties(self):
        """ Tests that a user isn't bumped when going from 4 to 3 active penalties """

        user = get_dummy_users(1)[0]
        AbakusGroup.objects.get(name='Abakus').add_user(user)

        p1 = Penalty.objects.create(user=user, reason='test', weight=1, source_event=self.event)
        Penalty.objects.create(user=user, reason='test2', weight=3, source_event=self.event)

        registration = Registration.objects.get_or_create(event=self.event, user=user)[0]
        async_register(registration.id)

        self.make_penalty_expire(p1)
        check_events_for_registrations_with_expired_penalties.delay()

        self.assertIsNone(Registration.objects.get(id=registration.id).pool)
        self.assertEqual(self.event.number_of_registrations, 0)

    def test_isnt_bumped_when_full(self):
        """ Tests that a user isnt bumped when the event is full when penalties expire. """

        users = get_dummy_users(2)
        for user in users:
            AbakusGroup.objects.get(name='Abakus').add_user(user)

        p1 = Penalty.objects.create(
            user=users[1], reason='test', weight=3, source_event=self.event
        )

        for user in users:
            registration = Registration.objects.get_or_create(event=self.event, user=user)[0]
            async_register(registration.id)

        self.make_penalty_expire(p1)
        check_events_for_registrations_with_expired_penalties.delay()

        self.assertIsNone(Registration.objects.get(user=users[1]).pool)
        self.assertEqual(self.event.number_of_registrations, 1)

    def test_isnt_bumped_when_not_first_in_line(self):
        """ Tests that a user isnt bumped when not first in the waiting list.
            In practice, this should never happen, because the only reason someone
            is in front of you in the list is if the event is full, which is tested above.
        """

        users = get_dummy_users(3)
        for user in users:
            AbakusGroup.objects.get(name='Abakus').add_user(user)

        p1 = Penalty.objects.create(
            user=users[2], reason='test', weight=3, source_event=self.event
        )

        for user in users:
            registration = Registration.objects.get_or_create(event=self.event, user=user)[0]
            async_register(registration.id)

        self.make_penalty_expire(p1)
        check_events_for_registrations_with_expired_penalties.delay()

        self.assertIsNone(Registration.objects.get(user=users[1]).pool)
        self.assertIsNone(Registration.objects.get(user=users[2]).pool)
        self.assertEqual(self.event.number_of_registrations, 1)

    def test_async_bump_post_merge(self):
        """ Tests that a waiting user with penalties is bumped to any pool after merge"""
        self.event.merge_time = timezone.now()
        self.event.save()

        users = get_dummy_users(2)
        for user in users:
            AbakusGroup.objects.get(name='Abakus').add_user(user)

        p1 = Penalty.objects.create(
            user=users[1], reason='test', weight=3, source_event=self.event
        )

        for user in users:
            registration = Registration.objects.get_or_create(event=self.event, user=user)[0]
            async_register(registration.id)

        self.make_penalty_expire(p1)
        check_events_for_registrations_with_expired_penalties.delay()

        self.assertIsNotNone(Registration.objects.get(user=users[1]).pool)
        self.assertEqual(self.event.number_of_registrations, 2)