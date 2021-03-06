# -*- encoding: utf-8 -*-
from django.contrib.auth.forms import (
    UserCreationForm,
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm
)
from django.utils.translation import ugettext_lazy as _
from django import forms

from accounts.models import User
from accounts import widgets as custom_widgets
from accounts import fields


class OrganizationValidationMixin(object):

    def ensure_provider(self, field):
        return self.ensure_other_field(field, 'organization_is_provider')

    def ensure_consumer(self, field, default=False):
        return self.ensure_other_field(field, 'organization_is_consumer',
                                       default)

    def clean_organization_is_host(self):
        return self.ensure_provider('organization_is_host')

    def clean_organization_is_performer(self):
        return self.ensure_provider('organization_is_performer')

    def clean_organization_is_creator(self):
        return self.ensure_provider('organization_is_creator')

    def clean_organization_is_media(self):
        return self.ensure_consumer('organization_is_media')

    def clean_organization_media_url(self):
        return self.ensure_consumer('organization_media_url', default='')

    def clean_organization_is_website(self):
        return self.ensure_consumer('organization_is_website')

    def clean_organization_website_url(self):
        return self.ensure_consumer('organization_website_url', default='')

    def clean_organization_is_mobile_app(self):
        return self.ensure_consumer('organization_is_mobile_app')

    def clean_organization_mobile_app_name(self):
        return self.ensure_consumer('organization_mobile_app_name', default='')

    def clean_organization_is_other(self):
        return self.ensure_consumer('organization_is_other')

    def clean_organization_other_details(self):
        return self.ensure_consumer('organization_other_details', default='')


class CustomAuthenticationForm(AuthenticationForm):

    username = forms.CharField(max_length=254,
                               widget=custom_widgets.TextInput)
    password = forms.CharField(label=_("Password"),
                               widget=custom_widgets.PasswordInput)


class CustomPasswordResetForm(PasswordResetForm):

    email = forms.EmailField(label=_("Email"), max_length=254,
                             widget=custom_widgets.EmailInput)


class CustomSetPasswordForm(SetPasswordForm):

    new_password1 = fields.Password1Field(label=_('Mot de passe'))
    new_password2 = fields.Password2Field()


class SignupForm(OrganizationValidationMixin, UserCreationForm):

    username = forms.RegexField(
        max_length=30,
        regex=r'^[\w.@+-]+$',
        help_text=_("Required. 30 characters or fewer. Letters, digits and "
                    "@/./+/-/_ only."),
        error_messages={
            'invalid': _("This value may contain only letters, numbers and "
                         "@/./+/-/_ characters.")},
        widget=custom_widgets.TextInput,
        label=_("Identifiant"))

    password1 = fields.Password1Field(label=_('Mot de passe'))
    password2 = fields.Password2Field()

    organization_list = fields.OrganizationListField()

    organization_activity_field = fields.OrganizationActivityFieldField()
    organization_name = fields.OrganizationNameField()
    organization_price_information = forms.CharField(
        max_length=100, required=False, widget=custom_widgets.TextInput)
    organization_type = fields.OrganizationTypeField()
    organization_address = fields.OrganizationAddressField()
    organization_post_code = fields.OrganizationPostCodeField()
    organization_town = fields.OrganizationTownField()
    organization_url = fields.OrganizationURLField()

    accept_terms_of_service = forms.BooleanField(
        widget=custom_widgets.CheckboxInput
    )

    organization_is_provider = fields.OrganizationIsProviderField()
    organization_is_host = fields.OrganizationIsHostField()
    organization_is_performer = fields.OrganizationIsPerformerField()
    organization_is_media = fields.OrganizationIsMediaField()
    organization_is_creator = fields.OrganizationIsCreatorField()

    organization_is_consumer = fields.OrganizationIsConsumerField()
    organization_is_website = fields.OrganizationIsWebsiteField()
    organization_is_mobile_app = fields.OrganizationIsMobileAppField()
    organization_is_other = fields.OrganizationIsOtherField()
    organization_media_url = fields.OrganizationMediaURLField()
    organization_website_url = fields.OrganizationWebsiteURLField()
    organization_other_details = fields.StandardCharField(label="")
    organization_mobile_app_name = fields.StandardCharField(label="")

    class Meta:
        model = User
        fields = [
            'last_name',
            'first_name',
            'email',
            'phone_number',
            'username',
        ]
        widgets = {field: custom_widgets.TextInput for field in fields}

    def clean_username(self):
        # Since User.username is unique, this check is redundant,
        # but it sets a nicer error message than the ORM. See #13147.
        username = self.cleaned_data["username"]
        try:
            User._default_manager.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(self.error_messages['duplicate_username'])

    def clean_organization_name(self):
        # organization_name is required ONLY if there is no selected
        # organization
        organization_list = self.cleaned_data["organization_list"]
        organization_name = self.cleaned_data["organization_name"]

        if not organization_list and not organization_name:
            raise forms.ValidationError(_('This field is required.'))
        else:
            return organization_name

    def clean(self):
        cleaned_data = super(SignupForm, self).clean()
        organization = cleaned_data.get('organization_list')
        is_provider = cleaned_data.get('organization_is_provider')
        is_consumer = cleaned_data.get('organization_is_consumer')
        if not organization and not is_consumer and not is_provider:
            raise forms.ValidationError(
                _(u"Vous devez indiquer si vous êtes fournisseur ou "
                  u"consommateur de données"))
        return cleaned_data

    def ensure_other_field(self, field, other_field, default=False):
        if self.cleaned_data.get(other_field):
            return self.cleaned_data[field]
        else:
            return default


class ProfileForm(OrganizationValidationMixin, forms.ModelForm):

    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
    }

    class Meta:
        model = User
        fields = [
            'last_name',
            'first_name',
            'email',
            'phone_number',
        ]
        widgets = {field: custom_widgets.TextInput for field in fields}

    password1 = fields.Password1Field(required=False, label=_('Mot de passe'))
    password2 = fields.Password2Field(required=False)

    organization_is_provider = fields.OrganizationIsProviderField()
    organization_is_provider.widget.attrs['disabled'] = 'disabled'
    organization_is_consumer = fields.OrganizationIsConsumerField()
    organization_is_consumer.widget.attrs['disabled'] = 'disabled'
    organization_is_host = fields.OrganizationIsHostField()
    organization_is_performer = fields.OrganizationIsPerformerField()
    organization_is_media = fields.OrganizationIsMediaField()
    organization_is_creator = fields.OrganizationIsCreatorField()
    organization_is_website = fields.OrganizationIsWebsiteField()
    organization_is_mobile_app = fields.OrganizationIsMobileAppField()
    organization_is_other = fields.OrganizationIsOtherField()

    organization_name = fields.OrganizationNameField()
    organization_type = fields.OrganizationTypeField()
    organization_activity_field = fields.OrganizationActivityFieldField()
    organization_address = fields.OrganizationAddressField()
    organization_post_code = fields.OrganizationPostCodeField()
    organization_town = fields.OrganizationTownField()
    organization_url = fields.OrganizationURLField()
    organization_media_url = fields.OrganizationMediaURLField()
    organization_website_url = fields.OrganizationWebsiteURLField()
    organization_other_details = fields.StandardCharField(label="")
    organization_mobile_app_name = fields.StandardCharField(label="")

    organization_price_information = fields.StandardCharField(label=_("Tarif"))
    organization_audience = fields.StandardCharField(label=_("Public"))
    organization_capacity = fields.StandardCharField(
        label=_(u"Capacité de la salle"))

    organization_ticket_contact_name = fields.StandardCharField(
        label=_(u"Nom"))
    organization_ticket_contact_email = fields.StandardCharField(
        label=_(u"Email"))
    organization_ticket_contact_phone_number = fields.StandardCharField(
        label=_(u"Téléphone"))
    organization_press_contact_name = fields.StandardCharField(
        label=_(u"Nom"))
    organization_press_contact_email = fields.StandardCharField(
        label=_(u"Email"))
    organization_press_contact_phone_number = fields.StandardCharField(
        label=_(u"Téléphone"))
    organization_picture = forms.ImageField(
        required=True,
        label=_(u'Remplacer la photo'))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(ProfileForm, self).__init__(*args, **kwargs)

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'])
        return password2

    def clean_organization_is_provider(self):
        return self.instance.organization.is_provider

    def clean_organization_is_consumer(self):
        return self.instance.organization.is_consumer

    def save(self, commit=True):
        if self.cleaned_data['password1']:
            self.user.set_password(self.cleaned_data['password1'])
        if commit:
            self.user.save()
        return self.user

    def ensure_other_field(self, field, other_field, default=False):
        other_field = other_field.replace('organization_', '')
        if getattr(self.user.organization, other_field):
            return self.cleaned_data[field]
        else:
            return default
