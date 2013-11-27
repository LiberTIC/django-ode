# -*- encoding: utf-8 -*-
from django.http import HttpResponseForbidden
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.shortcuts import render

from django_custom_datatables_view.base_datatable_view import BaseDatatableView
from frontend.api_client import APIClient


def error_list_to_dict(api_errors):
    """
    Convert error list returned by the API into a dictionary of error messages
    indexed by field names.
    """
    result = {}
    for error in api_errors:
        name = error['name']
        # Error names returned by the API look like
        # <resource_name>.<error_index>.<field_name>
        field_name = name.split('.')[2]
        result[field_name] = error['description']
    return result


class LoginRequiredMixin(object):
    """
    View mixin which requires that the user is authenticated.
    """
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(request, *args,
                                                        **kwargs)


class ProviderLoginRequiredMixin(object):
    """
    View mixin which requires that the user is authenticated AND is a provider
    """
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):

        if not request.user.organization.is_provider:
            return HttpResponseForbidden()
        else:
            return super(ProviderLoginRequiredMixin, self).dispatch(
                request, *args, **kwargs)


class APIForm(LoginRequiredMixin, View):

    def __init__(self, *args, **kwargs):
        super(APIForm, self).__init__(*args, **kwargs)
        self.api = APIClient(self.endpoint)

    def _update_context_data(self, context=None):

        if context is None:
            context = {}

        defined_context = self.add_context()
        new_context = dict(list(context.items()) +
                           list(defined_context.items()))

        return new_context

    def add_context(self):
        return {}

    def prepare_api_input(self, data):
        pass

    def post(self, request, *args, **kwargs):
        user_input = request.POST.dict()
        user_input.pop('csrfmiddlewaretoken', None)
        api_input = dict(user_input)
        self.prepare_api_input(api_input)
        post_data = {
            self.resource_name_plural: [api_input]
        }
        response_data = self.api.post(post_data, self.request.user.id)
        if response_data.get('status') == 'error':
            context = dict(response_data)
            context['input'] = user_input
            context['errors'] = error_list_to_dict(response_data['errors'])
            messages.error(request, self.error_message, extra_tags='danger')

            new_context = self._update_context_data(context)
            return render(request, self.template_name, new_context)
        else:
            new_context = self._update_context_data()
            messages.success(request, self.success_message)
            return render(request, self.template_name, new_context)

    def get(self, request, *args, **kwargs):
        new_context = self._update_context_data()
        return render(self.request, self.template_name, new_context)


class APIDatatableBaseView(BaseDatatableView):

    def get_sorting_col(self):

        i_sorting_cols = int(self.request.REQUEST.get('iSortingCols', 0))

        return i_sorting_cols

    def get_limit_value(self):

        limit = min(int(self.request.REQUEST.get('iDisplayLength', 10)),
                    self.max_display_length)

        return limit

    def get_offset_value(self):

        offset = int(self.request.REQUEST.get('iDisplayStart', 0))

        return offset

    def get_api_values(self, **kwargs):

        # Call distant API to get corresponding data
        api = APIClient(settings.SOURCES_ENDPOINT)
        response_data = api.get(self.request.user.id, **kwargs)

        return response_data

    def total_records(self, api_data):

        return api_data['total_count']

    def returned_records(self, api_data):

        raise NotImplemented()

    def prepare_results(self, api_data):

        raise NotImplemented()

    def get_context_data(self, *args, **kwargs):

        sorting = self.get_sorting_col()
        limit = self.get_limit_value()
        offset = self.get_offset_value()

        get_args = dict(sort_by=sorting,
                        limit=limit,
                        offset=offset,
                        sort_direction=sorting)
        response_data = self.get_api_values(**get_args)

        aaData = self.prepare_results(response_data)

        ret = {'sEcho': int(self.request.REQUEST.get('sEcho', 0)),
               'iTotalRecords': self.total_records(response_data),
               'iTotalDisplayRecords': self.returned_records(response_data),
               'aaData': aaData
               }

        return ret
