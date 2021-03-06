from django.test import TestCase

from accounts.models import User


class TestDashboard(TestCase):

    def login_as_admin(self):
        self.user = User.objects.create_superuser('admin', password='admin',
                                                  email='admin@example.com')
        return self.client.login(username='admin', password='admin')

    def test_anonymous_access(self):
        response = self.client.get('/dashboard', follow=True)
        self.assertContains(response, 'password')

    def test_login_as_superuser(self):
        self.login_as_admin()
        response = self.client.get('/dashboard', follow=True)
        self.assertContains(response, 'Structures')

    def test_link_to_dashboard_on_homepage(self):
        self.login_as_admin()
        response = self.client.get('/', follow=True)
        self.assertContains(response, 'Tableau de bord')

    def test_non_superuser_cannot_see_link_to_dashboard(self):
        User.objects.create_user('bob', password='foo')
        self.client.login(username='bob', password='foo')
        response = self.client.get('/', follow=True)
        self.assertNotContains(response, 'Tableau de bord')
