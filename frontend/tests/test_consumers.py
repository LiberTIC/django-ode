# -*- encoding: utf-8 -*-

import json

from django.utils.encoding import force_text
from django.test import TestCase

from accounts.tests.base import LoginTestMixin
from accounts.tests.test_factory import ConsumerUserFactory


class TestConsumers(LoginTestMixin, TestCase):

    def setUp(self):
        self.login_as_provider()

    def test_has_consumer_listing(self):

        response = self.client.get('/consumer_list/')
        self.assertContains(response, "Liste des réutilisateurs")
        self.assertContains(response, "datatable-listing")

    def test_has_provider_view(self):

        user = ConsumerUserFactory.create(
            username='bob2', confirmation_code='s3cr3t', email="bob2@mc.com")
        user.is_active = True
        user.save()

        response = self.client.get('/consumer/1/')
        self.assertNotContains(response, "modal")
        self.assertContains(response, "Type de structure")

    def test_provider_ajax_view(self):

        user = ConsumerUserFactory.create(
            username='bob2', confirmation_code='s3cr3t', email="bob2@mc.com")
        user.is_active = True
        user.save()

        response = self.client.get('/consumer/1/',
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, "modal")
        self.assertContains(response, "Type de structure")

    def test_datatable_has_consumer(self):

        ConsumerUserFactory.create(username='bob2', confirmation_code='s3cr3t',
                                   email="bob2@mc.com", is_active=True)
        ConsumerUserFactory.create(username='bob3', confirmation_code='s3cr3t',
                                   email="bob3@mc.com", is_active=True)

        response = self.client.get('/consumer_json_list/')

        response_json = json.loads(force_text(response.content))

        # aaData is Datatable mandatory key for displayed data
        self.assertIn('aaData', response_json.keys())
        datas = response_json['aaData']

        self.assertEqual(len(datas), 2)
