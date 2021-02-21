from django import forms
from django.db.models.functions import Lower
from .models import TemplateFolder, TemplateNodeChoice, ConversationTemplate
from bootstrap_modal_forms.forms import BSModalModelForm


class SelectTemplates(forms.SelectMultiple):
    """
    Function needed to make the multiple templates selectable within the form.
    """
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        return option


class FolderCreationForm(BSModalModelForm):
    """
    Form to create a TemplateFolder object
    Uses BSModalModelForm which is needed for bootstrap_modal_forms to work properly
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show templates unique to each user in the form.
        if self.request.user:
            templates = ConversationTemplate.objects.filter(researcher=self.request.user.id)
            self.fields['templates'].queryset = templates.all()
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
        fields = ['name', 'templates']
        widgets = {'templates': SelectTemplates}


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
            select_text_initial = split_creation_date(str(initial.creation_date))
            template_list = [(initial.id, f"{initial.name}: {select_text_initial}")]
            for template in templates:
                select_text = split_creation_date(str(template.creation_date))
                template_list.append((template.id, f"{template.name}: {select_text}"))
            self.fields['templates'] = forms.ChoiceField(choices=template_list)


def split_creation_date(creation_date):
    creation_date = creation_date.split('+')[0]
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
        choice_html = f'<ul id="id_{name}">'
        for idx, choice in enumerate(self._list):
            choice_html += f'<li><label for="id_choice-{idx}"><input type="radio" id="id_choice-{idx}"' \
                            f'name={name} value="{choice.id}" class="node-choice"> {choice.choice_text}  </label></li>'

        choice_html += f'<li><label for="id_choice-custom"><input type="radio" id="id_choice-custom"' \
                       f'name={name} value="custom-response" class="node-choice"><input name="custom-text" type="text"'\
                       f'placeholder="Enter Custom Response" id="id_custom-input"></label></li>'

        choice_html += '</ul>'

        return choice_html


class TemplateNodeChoiceForm(forms.Form):
    """
    Form to display choices related to a TemplateNode
    """
    choices = forms.ModelChoiceField(
        queryset=None,
        widget=forms.RadioSelect,
    )

    def __init__(self, *args, **kwargs):
        ct_node = kwargs.pop('ct_node', None)
        choice_list = TemplateNodeChoice.objects.filter(parent_template_node=ct_node)
        super(TemplateNodeChoiceForm, self).__init__(*args, **kwargs)
        self.fields['choices'].queryset = TemplateNodeChoice.objects.filter(parent_template_node=ct_node)
        self.fields['choices'].widget = CustomChoiceRadioSelectWidget(name="choice-widget", data_list=choice_list)

    def is_valid(self):
        valid = super(TemplateNodeChoiceForm, self).is_valid()

        # Return True if the custom response choice is selected and the input box is filled out
        if not valid:
            if 'choices' in self.data and self.data['custom-text'].strip() != '':
                return True
            return False

        return True
