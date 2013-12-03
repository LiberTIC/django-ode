# -*- encoding: utf-8 -*-
from django.http import HttpResponseForbidden
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render

from django_custom_datatables_view.base_datatable_view import BaseDatatableView
from frontend.api_client import APIClient


def data_list_to_dict(data_list):
    result = {}
    for data_field in data_list:
        key = data_field['name']
        new_value = data_field['value']
        if key in result:
            existing_value = result[key]['value']
            if isinstance(existing_value, list):
                existing_value.append({'value': new_value})
            else:
                result[key]['value'] = [{'value': existing_value},
                                        {'value': new_value}]
        else:
            result[key] = {'value': new_value}
    return result


def error_list_to_dict(api_errors):
    """
    Convert error list returned by the API into a dictionary of error messages
    indexed by field names.
    """
    result = {}
    for error in api_errors:
        name = error['name']
        # Error names returned by the API look like
        # collection.items.<error_index>.data.<field_name>
        field_name = name.split('.')[4]
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

    def prepare_api_input(self, dict_data):

        formatted_data = []
        for key, value in dict_data.items():
            formatted_data.append(
                {'name': key, 'value': value}
            )

        post_data = {
            'template': {
                'data': formatted_data
            }
        }

        return post_data

    def post(self, request, *args, **kwargs):

        user_input = request.POST.dict()
        user_input.pop('csrfmiddlewaretoken', None)
        api_input = dict(user_input)

        post_data = self.prepare_api_input(api_input)
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

    endpoint = None
    api_columns = None

    def get_sort_by(self):
        raise NotImplementedError()

    def get_xpath_ind(self, xpath_value):

        try:
            ind = int(xpath_value)
        except ValueError:
            ind = xpath_value

        return ind

    def get_data_from_field(self, data, field):
        data = data_list_to_dict(data)

        xpath = field.split(".")

        xelement = self.get_xpath_ind(xpath[0])

        if len(xpath) == 1:
            return data[xelement]['value']
        else:
            return self.get_data_from_field(
                data[xelement],
                ".".join(xpath[1:]))

    def get_index_from_column_label(self, field_name):

        for i, column in enumerate(self.column_labels):

            if column == field_name:
                return i

        return None

    def get_index_for(self, field_name):

        for i, column in enumerate(self.api_columns):

            column_splitted = column.split(".")
            if len(column_splitted) > 1:
                field_to_compare = column_splitted[-1]
            else:
                field_to_compare = column_splitted[0]

            if field_to_compare == field_name:
                return i

        return None

    def get_sort_direction(self):

        s_sort_dir = self.request.REQUEST.get('sSortDir_0', 'desc')

        return s_sort_dir

    def get_limit_value(self):

        limit = min(int(self.request.REQUEST.get('iDisplayLength', 10)),
                    self.max_display_length)

        return limit

    def get_offset_value(self):

        offset = int(self.request.REQUEST.get('iDisplayStart', 0))

        return offset

    def get_api_values(self, **kwargs):

        # Call distant API to get corresponding data
        api = APIClient(self.endpoint)
        response_data = api.get(self.request.user.id, **kwargs)

        return response_data

    def convert_api_to_datatable_data(self, api_data):

        converted_data = []
        collection = api_data['collection']

        for source in collection['items']:

            data = source['data']
            raw_data = []
            for field in self.api_columns:
                raw_value = self.get_data_from_field(data, field)
                raw_data.append(raw_value)

            converted_data.append(raw_data)

        return converted_data

    def total_records(self, api_data):
        return api_data['collection']['total_count']

    def returned_records(self, api_data):
        return api_data['collection']['total_count']

    def prepare_results(self, api_data):
        return api_data

    def get_context_data(self, *args, **kwargs):

        sort_by = self.get_sort_by()
        sort_direction = self.get_sort_direction()
        limit = self.get_limit_value()
        offset = self.get_offset_value()

        get_args = dict(sort_by=sort_by,
                        limit=limit,
                        offset=offset,
                        sort_direction=sort_direction)
        response_data = self.get_api_values(**get_args)

        api_data = self.convert_api_to_datatable_data(response_data)

        aaData = self.prepare_results(api_data)

        ret = {'sEcho': int(self.request.REQUEST.get('sEcho', 0)),
               'iTotalRecords': self.total_records(response_data),
               'iTotalDisplayRecords': self.returned_records(response_data),
               'aaData': aaData
               }

        return ret
