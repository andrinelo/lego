from rest_framework.reverse import reverse

from lego.apps.users.models import User
from lego.utils.test_utils import BaseAPITestCase


class JSONWebTokenTestCase(BaseAPITestCase):
    fixtures = ['initial_files.yaml', 'test_users.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.user_data = {'username': self.user.username, 'password': 'test'}

    def check_user(self, user):

        # Pulled from DetailedUserSerializer
        fields = (
            'id', 'username', 'first_name', 'last_name', 'full_name', 'email', 'is_staff',
            'is_active', 'penalties'
        )
        for field in fields:
            if field == 'penalties':
                self.assertEqual(len(self.user.penalties.valid()), len(user['penalties']))
            else:
                self.assertEqual(getattr(self.user, field), user[field])

    def test_authenticate(self):
        response = self.client.post(reverse('jwt:obtain_jwt_token'), self.user_data)
        self.assertContains(response, 'token')
        self.assertContains(response, 'user')

    def test_refresh(self):
        token_response = self.client.post(reverse('jwt:obtain_jwt_token'), self.user_data)
        token_data = {'token': token_response.data['token']}
        refresh_response = self.client.post(reverse('jwt:refresh_jwt_token'), token_data)

        self.assertContains(refresh_response, 'token')
        self.assertContains(token_response, 'user')
