from django.test import TestCase

from lego.apps.users.models import AbakusGroup, Membership, User


class AbakusGroupTestCase(TestCase):
    fixtures = ['initial_abakus_groups.yaml']

    def setUp(self):
        self.non_committee = AbakusGroup(name='testgroup')
        self.non_committee.save()

    def test_is_commitee(self):
        committee = AbakusGroup.objects.get(name='Webkom')
        self.assertTrue(committee.is_committee)
        self.assertFalse(self.non_committee.is_committee)

    def test_natural_key(self):
        found_group = AbakusGroup.group_objects.get_by_natural_key(self.non_committee.name)
        self.assertEqual(self.non_committee, found_group)


class AbakusGroupHierarchyTestCase(TestCase):
    fixtures = ['initial_abakus_groups.yaml']

    def setUp(self):
        self.abakom = AbakusGroup.objects.get(name='Abakom')

    def test_find_all_children(self):
        committees = AbakusGroup.objects.filter(parent=self.abakom.pk)
        children = self.abakom.get_children()
        self.assertEqual(len(committees), len(children))

    def test_abakom_is_root(self):
        abakus = AbakusGroup.objects.get(name='Abakus')
        self.assertTrue(abakus.is_root_node())

    def test_get_ancestors(self):
        abakus = AbakusGroup.objects.get(name='Abakus')
        webkom = AbakusGroup.objects.get(name='Webkom')

        ancestors = set(webkom.get_ancestors())

        self.assertEqual(len(ancestors), 2)
        self.assertTrue(abakus in ancestors)
        self.assertTrue(self.abakom in ancestors)

    def test_get_ancestors_include_self(self):
        abakus = AbakusGroup.objects.get(name='Abakus')
        webkom = AbakusGroup.objects.get(name='Webkom')

        ancestors = set(webkom.get_ancestors(include_self=True))

        self.assertEqual(len(ancestors), 3)
        self.assertTrue(webkom in ancestors)
        self.assertTrue(abakus in ancestors)
        self.assertTrue(self.abakom in ancestors)

    def test_get_descendants(self):
        webkom = AbakusGroup.objects.get(name='Webkom')
        first = AbakusGroup.objects.create(name='first', parent=webkom)
        second = AbakusGroup.objects.create(name='second', parent=first)

        descendants = webkom.get_descendants()
        self.assertEqual(len(descendants), 2)
        self.assertTrue(first in descendants)
        self.assertTrue(second in descendants)

    def test_get_descendants_include_self(self):
        abakus = AbakusGroup.objects.get(name='Abakus')
        self.assertEqual(set(AbakusGroup.objects.all()),
                         set(abakus.get_descendants(include_self=True)))


class UserTestCase(TestCase):
    fixtures = ['initial_abakus_groups.yaml', 'test_users.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=1)

    def test_full_name(self):
        full_name = '{0} {1}'.format(self.user.first_name, self.user.last_name)
        self.assertEqual(full_name, self.user.get_full_name())

    def test_short_name(self):
        self.assertEqual(self.user.get_short_name(), self.user.first_name)

    def test_all_groups(self):
        abakus = AbakusGroup.objects.get(name='Abakus')
        abakom = AbakusGroup.objects.get(name='Abakom')
        webkom = AbakusGroup.objects.get(name='Webkom')

        webkom.add_user(self.user)
        abakus_groups = self.user.all_groups

        self.assertEqual(len(abakus_groups), 3)
        self.assertTrue(webkom in abakus_groups)
        self.assertTrue(abakom in abakus_groups)
        self.assertTrue(abakus in abakus_groups)

    def test_number_of_users(self):
        abakus = AbakusGroup.objects.get(name='Abakus')
        abakom = AbakusGroup.objects.get(name='Abakom')
        webkom = AbakusGroup.objects.get(name='Webkom')

        abakus.add_user(self.user)
        abakom.add_user(User.objects.get(pk=2))
        webkom.add_user(User.objects.get(pk=3))

        self.assertEqual(abakus.number_of_users, 3)
        self.assertEqual(abakom.number_of_users, 2)
        self.assertEqual(webkom.number_of_users, 1)

    def test_add_remove_user(self):
        abakus = AbakusGroup.objects.get(name='Abakus')

        abakus.add_user(self.user)
        self.assertEqual(abakus.number_of_users, 1)

        abakus = AbakusGroup.objects.get(name='Abakus')
        abakus.remove_user(self.user)
        self.assertEqual(abakus.number_of_users, 0)

    def test_add_user_to_two_groups(self):
        AbakusGroup.objects.get(name='Abakus').add_user(self.user)
        self.assertEqual(AbakusGroup.objects.get(name='Abakus').number_of_users, 1)
        self.assertEqual(AbakusGroup.objects.get(name='Webkom').number_of_users, 0)

        AbakusGroup.objects.get(name='Webkom').add_user(self.user)
        self.assertEqual(AbakusGroup.objects.get(name='Abakus').number_of_users, 1)
        self.assertEqual(AbakusGroup.objects.get(name='Webkom').number_of_users, 1)

    def test_natural_key(self):
        found_user = User.objects.get_by_natural_key(self.user.username)
        self.assertEqual(self.user, found_user)


class MembershipTestCase(TestCase):
    fixtures = ['initial_abakus_groups.yaml', 'test_users.yaml']

    def setUp(self):
        self.test_committee = AbakusGroup.objects.get(name='Webkom')
        self.test_user = User.objects.get(pk=1)
        self.test_membership = Membership(
            user=self.test_user,
            abakus_group=self.test_committee,
            role=Membership.TREASURER
        )
        self.test_membership.save()

    def test_to_string(self):
        self.assertEqual(
            str(self.test_membership),
            '{0} is {1} in {2}'.format(
                self.test_membership.user,
                self.test_membership.get_role_display(),
                self.test_membership.abakus_group
            )
        )

    def test_natural_key(self):
        found_membership = Membership.objects.get_by_natural_key(self.test_user.username,
                                                                 self.test_committee.name)
        self.assertEqual(self.test_membership, found_membership)