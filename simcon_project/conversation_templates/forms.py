from django import forms
from django.contrib import messages
from django.db.models.functions import Lower
from .models import TemplateFolder, TemplateNodeChoice, ConversationTemplate
from bootstrap_modal_forms.forms import BSModalModelForm
from django_select2 import forms as s2forms


class FolderCreationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request')
        super().__init__(*args, **kwargs)
        if request:
            self.request = request

    attrs = {'placeholder': 'Folder Name', 'required': "", "autocomplete": "off"}
    folder_name = forms.CharField(max_length=TemplateFolder._meta.get_field('name').max_length,
                                  widget=forms.TextInput(attrs=attrs), label='')

    def clean(self):
        data = self.cleaned_data
        name = data['folder_name']

        if TemplateFolder.objects.filter(name=name, researcher=self.request.user.id):
            # self.add_error is still needed because of unique constraint
            self.add_error('folder_name', f'Cannot create Folder. {name} already exists.')
            messages.error(self.request, f'Cannot create Folder. {name} already exists.')

        return data


class FolderEditForm(BSModalModelForm):
    """
    Form to create a TemplateFolder object
    Uses BSModalModelForm which is needed for bootstrap_modal_forms to work properly
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True

    def clean(self):
        data = self.cleaned_data
        instance = str(self.instance)

        # Validation for when creating a new folder and entering a duplicate name
        if not instance and 'name' in data:
            name = self.cleaned_data['name']
            if TemplateFolder.objects.filter(name=name, researcher=self.request.user.id):
                self.add_error('name', f'{name} already exists. Choose a new folder name.')

        # Validation for when editing a folder and entering a duplicate name
        if instance and 'name' in data and data['name'] != self.initial['name']:
            name = self.cleaned_data['name']
            if TemplateFolder.objects.filter(name=name, researcher=self.request.user.id):
                self.add_error('name', f'{name} already exists. Choose a new folder name.')

        return data

    class Meta:
        model = TemplateFolder
        fields = ['name']


class TemplatesWidget(s2forms.ModelSelect2MultipleWidget):
    search_fields = [
        "name__icontains",
    ]


class AddTemplatesForm(forms.ModelForm):
    class Meta:
        model = TemplateFolder
        fields = ['templates']
        widgets = {
            "templates": TemplatesWidget,
        }


class SelectTemplateForm(forms.Form):
    """
    Form containing a single ChoiceField to select a template.
    The template being viewed right now will be the initial value in the ChoiceField and others
    are ordered in alphabetical order (case insensitive).
    Each choice is a tuple of (template.id, template.name) so template id can be used when the
    form is submitted on a POST request.
    """

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request')
        initial = kwargs.pop('initial')
        super().__init__(*args, **kwargs)
        if request.user and initial:
            if request.COOKIES.get('show_archived') == "True":
                templates = ConversationTemplate.objects.filter(researcher=request.user.id).exclude(
                    id=initial.id).order_by(Lower('name'))
            else:
                templates = ConversationTemplate.objects.filter(researcher=request.user.id, archived=False).exclude(
                    id=initial.id).order_by(Lower('name'))
            select_text_initial = split_creation_date(str(initial.creation_date.astimezone()))
            template_list = [(initial.id, f"{initial.name}: {select_text_initial}")]
            for template in templates:
                select_text = split_creation_date(str(template.creation_date.astimezone()))
                template_list.append((template.id, f"{template.name}: {select_text}"))
            self.fields['templates'] = forms.ChoiceField(choices=template_list, label='')


def split_creation_date(creation_date):
    creation_date = creation_date.rsplit('-', 1)[0]
    if '.' in creation_date:
        creation_date = creation_date.split('.')[0]
    return creation_date


class CustomChoiceRadioSelectWidget(forms.RadioSelect):
    """
    RadioSelect Widget that has a text input box as the last choice
    """
    def __init__(self, name, data_list, *args, **kwargs):
        super(CustomChoiceRadioSelectWidget, self).__init__(*args, **kwargs)
        self._name = name
        self._list = data_list

    def render(self, name, value, attrs=None, renderer=None):
        choice_html = f'<ul id="id_{name}" class="no-bullet-unordered-list">'
        for idx, choice in enumerate(self._list):
            choice_html += f'<li>' \
                           f'<label for="id_choice-{idx}">' \
                           f'<input type="radio" id="id_choice-{idx}" required="" name={name} value="{choice.id}" class="node-choice"> {choice.choice_text}' \
                           f'</label>' \
                           f'</li>'

        choice_html += f'<li>' \
                       f'<label for="id_choice-custom" style="width:100%;">' \
                       f'<input type="radio" id="id_choice-custom" required="" name="{name}" value="custom-response" class="node-choice mb-3">' \
                       f'<textarea rows="1" name="custom-text" placeholder="Enter Custom Response" id="id_custom-input" class="ml-1"  style="width:90%;"></textarea>' \
                       f'</label>' \
                       f'</li>'

        choice_html += '</ul>'

        return choice_html


class TemplateNodeChoiceForm(forms.Form):
    """
    Form to display choices related to a TemplateNode
    """
    choices = forms.ModelChoiceField(
        queryset=None,
        widget=forms.RadioSelect(attrs={'class': "no-bullet-unordered-list"}),
    )

    def __init__(self, *args, **kwargs):
        ct_node = kwargs.pop('ct_node', None)
        allow_typed_response = kwargs.pop('allow_typed_response', None)
        choice_list = TemplateNodeChoice.objects.filter(parent_template_node=ct_node)
        super(TemplateNodeChoiceForm, self).__init__(*args, **kwargs)
        self.fields['choices'].queryset = TemplateNodeChoice.objects.filter(parent_template_node=ct_node)
        if allow_typed_response:
            self.fields['choices'].widget = CustomChoiceRadioSelectWidget(name="choice-widget", data_list=choice_list)

    def is_valid(self):
        valid = super(TemplateNodeChoiceForm, self).is_valid()

        # Return True if the custom response choice is selected and the input box is filled out
        if not valid:
            if 'choices' in self.data and self.data['custom-text'].strip() != '':
                return True
            return False

        return True
