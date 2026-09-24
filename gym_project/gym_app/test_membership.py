from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from .models import PerfilUsuario


class MembershipTests(TestCase):
    def test_selection_persists_and_validates(self):
        user = User.objects.create_user(username='membership-test')
        self.client.force_login(user)
        for plan in ('mensual', 'semestral', 'premium_anual'):
            response = self.client.post(reverse('precios'), {'plan_precio': plan})
            self.assertEqual(response.status_code, 302)
            self.assertEqual(PerfilUsuario.objects.get(user=user).plan_precio, plan)
        self.assertEqual(self.client.post(reverse('precios'), {'plan_precio': 'pagado'}).status_code, 400)
        self.assertEqual(PerfilUsuario.objects.get(user=user).plan_precio, 'premium_anual')

    def test_guest_choice_is_retained_without_activating_membership(self):
        response = self.client.post(reverse('precios'), {'plan_precio': 'semestral'})
        self.assertRedirects(response, reverse('registrarse'), fetch_redirect_response=False)
        self.assertEqual(self.client.session['plan_precio_pendiente'], 'semestral')
        self.assertEqual(PerfilUsuario.objects.count(), 0)
