import os
import unittest
from unittest import mock

import responses

from gitlab import Gitlab
from gitlab.exceptions import HttpError
from response_data.users import *


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.user = os.environ.get('gitlab_user', 'root')
        self.password = os.environ.get('gitlab_password', '5iveL!fe')
        self.host = os.environ.get('gitlab_host', 'http://localhost:10080')
        self.gitlab = Gitlab(host=self.host, verify_ssl=False)
        self.gitlab.host = self.host


class TestLogin(BaseTest):
    def test_login(self):
        self.assertTrue(self.gitlab.login(user=self.user, password=self.password))

    def test_login_email(self):
        self.assertRaises(
            HttpError, self.gitlab.login, email='test@test.com', password='test')

    def test_login_with_no_values(self):
        self.assertRaises(ValueError, self.gitlab.login)


class TestGet(BaseTest):
    def setUp(self):
        super(TestGet, self).setUp()
        self.gitlab.login(user=self.user, password=self.password)

    @responses.activate
    def test_get_with_200(self):
        responses.add(
            responses.GET,
            self.gitlab.api_url + '/users',
            json=get_users,
            status=200,
            content_type='application/json')

        self.assertEqual(get_users, self.gitlab.get('/users'))

    @responses.activate
    def test_get_with_404(self):
        responses.add(
            responses.GET,
            self.gitlab.api_url + '/users',
            body='{"error": "Not here"}',
            status=404,
            content_type='application/json')

        self.assertRaises(HttpError, self.gitlab.get, '/users')


class TestPost(BaseTest):
    def setUp(self):
        super(TestPost, self).setUp()
        self.gitlab.login(user=self.user, password=self.password)

    @responses.activate
    def test_post_with_201(self):
        responses.add(
            responses.POST,
            self.gitlab.api_url + '/users',
            json=post_users,
            status=201,
            content_type='application/json')
        data = {
            'name': 'test',
            'username': 'test1',
            'password': 'MyTestPassword1',
            'email': 'example@example.com'
        }

        self.assertEqual(post_users, self.gitlab.post('/users', **data))

    @responses.activate
    def test_get_with_404(self):
        responses.add(
            responses.POST,
            self.gitlab.api_url + '/users',
            body=post_users_error,
            status=409,
            content_type='application/json')
        data = {
            'name': 'test',
            'username': 'test1',
            'password': 'MyTestPassword1',
            'email': 'example@example.com'
        }

        self.assertRaises(HttpError, self.gitlab.post, '/users', **data)


class TestDelete(BaseTest):
    def setUp(self):
        super(TestDelete, self).setUp()
        self.gitlab.login(user=self.user, password=self.password)

    @responses.activate
    def test_delete(self):
        responses.add(
            responses.DELETE,
            self.gitlab.api_url + '/users/5',
            json=None,
            status=204,
            content_type='application/json')

        self.assertEqual({}, self.gitlab.delete('/users/5'))

    @responses.activate
    def test_delete_404(self):
        responses.add(
            responses.POST,
            self.gitlab.api_url + '/users',
            body=post_users_error,
            status=409,
            content_type='application/json')

        self.assertRaises(HttpError, self.gitlab.post, '/users')


class TestSuccessOrRaise(BaseTest):
    def setUp(self):
        super(TestSuccessOrRaise, self).setUp()
        self.gitlab.login(user=self.user, password=self.password)

    def test_success_or_raise_without_error(self):
        response = mock.MagicMock()
        response_config = {
            'status_code': 200,
            'json.return_value': post_users_error
        }
        response.configure_mock(**response_config)

        self.gitlab.success_or_raise(response, [200])

    def test_success_or_raise_with_error(self):
        response = mock.MagicMock()
        response_config = {
            'status_code': 404,
            'text': post_users_error
        }
        response.configure_mock(**response_config)

        self.assertRaises(HttpError, self.gitlab.success_or_raise, response, [200])
