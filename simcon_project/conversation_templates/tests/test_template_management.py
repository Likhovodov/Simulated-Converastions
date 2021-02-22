from django.test import TestCase, RequestFactory
from django.utils import timezone
from django.shortcuts import reverse
from datetime import date
from users.models import Researcher, Student, Assignment, SubjectLabel
from conversation_templates.models import *
from conversation_templates.forms import FolderCreationForm
from conversation_templates.views.template_management import route_to_current_folder, FolderEditView


class TemplateManagementTests(TestCase):
    def setUp(self):
        self.researcher = Researcher.objects.create_researcher(email="researcher@pdx.edu", password="abc123")
        self.template1 = ConversationTemplate.objects.create(name="test_template", researcher=self.researcher,
                                                             creation_date=timezone.now())
        self.template2 = ConversationTemplate.objects.create(name="another_template", researcher=self.researcher,
                                                             creation_date=timezone.now())
        self.folder = TemplateFolder.objects.create(name="folder")
        self.folder.templates.set([self.template1, self.template2])
        self.factory = RequestFactory()

    # =============== UNIT TESTS ===================
    def test_folder_creation_form_valid_data(self):
        form = FolderCreationForm(data={'name': "test_folder", 'templates': [self.template1]})
        self.assertTrue(form.is_valid())

    def test_folder_creation_form_invalid_data(self):
        form = FolderCreationForm(data={'name': "", 'templates': [self.template1]})
        self.assertFalse(form.is_valid())

    def test_folder_name_exceeds_max_length(self):
        name = "This is a long string"
        max_len = TemplateFolder._meta.get_field('name').max_length
        for x in range(max_len):
            name = name + 'a'
        form = FolderCreationForm(data={"name": name, "templates": []})
        expected = [f'Ensure this value has at most {max_len} characters (it has {len(name)}).']
        self.assertEqual(form.errors["name"], expected)

    def test_folder_name_already_exists(self):
        name = "folder"
        form = FolderCreationForm(data={"name": name, "templates": []})
        expected = ['Template folder with this Name already exists.']
        self.assertEqual(form.errors["name"], expected)

    def test_route_to_existing_url_with_folder(self):
        request = self.factory.get(reverse('management:folder-view', args=[self.folder.id]))
        response = route_to_current_folder(request.get_full_path())
        self.assertEqual(response, reverse('management:folder-view', args=[self.folder.id]))

    def test_route_to_existing_url_no_folder(self):
        request = self.factory.get(reverse('management:main'))
        response = route_to_current_folder(request.get_full_path())
        self.assertEqual(response, reverse('management:main'))

    def test_main_view(self):
        response = self.client.get(reverse('management:main'))
        self.assertIn('AllTemplateTable', str(type(response.context['templateTable'])))
        self.assertEqual(response.status_code, 200)

    def test_folder_view(self):
        response = self.client.get(reverse('management:folder-view', args=[self.folder.id]))
        self.assertIn('FolderTemplateTable', str(type(response.context['templateTable'])))
        self.assertEqual(response.context['folder_pk'], self.folder.id)
        self.assertEqual(response.status_code, 200)

    def test_edit_folder(self):
        data = {"name": "changed_folder", "templates": []}
        prev_request = self.factory.get(reverse('management:main'))
        request = self.factory.post(reverse('management:edit-folder', args=[self.folder.id]), data=data)
        request.META['HTTP_REFERER'] = prev_request
        response = FolderEditView.as_view()(request, pk=self.folder.id)
        self.assertEqual(response.status_code, 302)

    def test_create_folder(self):
        response = self.client.post(reverse('management:create-folder'), data={
            "name": "new_folder",
            "templates": self.template1})
        self.assertEqual(response.status_code, 200)

    def test_delete_folder(self):
        folder_count = TemplateFolder.objects.count()
        response = self.client.post(reverse('management:delete-folder', args=[self.folder.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(TemplateFolder.objects.count(), folder_count - 1)

    def test_delete_template(self):
        template_count = ConversationTemplate.objects.count()
        response = self.client.post(reverse('management:delete-template', args=[self.template1.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ConversationTemplate.objects.count(), template_count - 1)

    def test_delete_template_cascades(self):
        student = Student.objects.create_user(password='abc123', email='student@pdx.edu', added_by=self.researcher)
        start_node = TemplateNode.objects.create(description='Node', parent_template=self.template1, start=True,
                                                 video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        node1 = TemplateNode.objects.create(description='Node', parent_template=self.template1
                                            , video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        node2 = TemplateNode.objects.create(description='Node', parent_template=self.template1
                                            , video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        TemplateNodeChoice.objects.create(parent_template_node=start_node, destination_node=node1)
        TemplateNodeChoice.objects.create(parent_template_node=start_node, destination_node=node2)
        label = SubjectLabel.objects.create(label_name='label', researcher=self.researcher)
        label.students.set([student])
        assignment1 = Assignment.objects.create(name='assignment', date_assigned=date.today(),
                                               researcher=self.researcher)
        assignment1.subject_labels.set([label])
        assignment1.conversation_templates.set([self.template1])
        assignment2 = Assignment.objects.create(name='assignment2', date_assigned=date.today(),
                                                researcher=self.researcher)
        assignment2.subject_labels.set([label])
        assignment2.conversation_templates.set([self.template1, self.template2])
        response = TemplateResponse.objects.create(student=student, template=self.template1, assignment=assignment1
                                                   , completion_date=timezone.now(), feedback='Not bad kid')
        TemplateNodeResponse.objects.create(transcription='Hello', template_node=node1,
                                            parent_template_response=response, position_in_sequence=0,
                                            audio_response='notanaudio.txt')

        self.assertEqual(TemplateNode.objects.count(), 3)
        self.assertEqual(TemplateNodeChoice.objects.count(), 2)
        self.assertEqual(TemplateResponse.objects.count(), 1)
        self.assertEqual(TemplateNodeResponse.objects.count(), 1)
        self.assertEqual(self.template1.name, assignment1.conversation_templates.get(name=self.template1.name).name)

        self.client.post(reverse('management:delete-template', args=[self.template1.id]))

        with self.assertRaises(ConversationTemplate.DoesNotExist):
            assignment1.conversation_templates.get(name=self.template1.name)
            assignment2.conversation_templates.get(name=self.template1.name)
        self.assertNotIn(str(assignment2.conversation_templates.all()), self.template1.name)

        self.assertEqual(TemplateNode.objects.count(), 0)
        self.assertEqual(TemplateNodeChoice.objects.count(), 0)
        self.assertEqual(TemplateResponse.objects.count(), 0)
        self.assertEqual(TemplateNodeResponse.objects.count(), 0)
