from django.test import TestCase

from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model

from projects.models import Project, Client, Task, Target, ProjectOrganization
from respondents.models import Respondent, Interaction
from organizations.models import Organization
from indicators.models import Indicator
from datetime import date
User = get_user_model()


class TaskViewSetTest(APITestCase):
    def setUp(self):
        #set up users for each role
        self.admin = User.objects.create_user(username='admin', password='testpass', role='admin')
        self.manager = User.objects.create_user(username='manager', password='testpass', role='manager')
        self.officer = User.objects.create_user(username='meofficer', password='testpass', role='meofficer')
        self.data_collector = User.objects.create_user(username='data_collector', password='testpass', role='data_collector')
        self.view_user = User.objects.create(username='uninitiated', password='testpass', role='view_only')

        self.client_user = User.objects.create_user(username='client', password='testpass', role='client')
        #set up a parent/child org and an unrelated org
        self.parent_org = Organization.objects.create(name='Parent')
        self.child_org = Organization.objects.create(name='Child')
        self.other_org = Organization.objects.create(name='Other')
        self.loser_org = Organization.objects.create(name='Not Invited')

        self.admin.organization = self.parent_org
        self.manager.organization = self.parent_org
        self.officer.organization = self.child_org
        self.data_collector.organization = self.parent_org
        self.view_user.organization = self.parent_org
        self.client_user.organization = self.other_org

        #set up a client
        self.client_obj = Client.objects.create(name='Test Client', created_by=self.admin)
        self.other_client_obj = Client.objects.create(name='Loser Client', created_by=self.admin)

        self.client_user.client_organization = self.client_obj
        self.project = Project.objects.create(
            name='Alpha Project',
            client=self.client_obj,
            status=Project.Status.ACTIVE,
            start='2024-01-01',
            end='2024-12-31',
            description='Test project',
            created_by=self.admin,
        )
        self.project.organizations.set([self.parent_org, self.child_org, self.other_org])

        child_link = ProjectOrganization.objects.filter(organization=self.child_org, project=self.project).first()
        child_link.parent_organization = self.parent_org
        child_link.save()

        self.project_2 = Project.objects.create(
            name='Beta Project',
            client=self.client_obj,
            status=Project.Status.ACTIVE,
            start='2024-01-01',
            end='2024-12-31',
            description='Not included project',
            created_by=self.admin,
        )
        self.project_2.organizations.set([self.parent_org, self.child_org, self.other_org])

        self.planned_project = Project.objects.create(
            name='Gamme Project',
            client=self.client_obj,
            status=Project.Status.PLANNED,
            start='2024-02-01',
            end='2024-10-31',
            description='Second project',
            created_by=self.admin,
        )

        self.indicator = Indicator.objects.create(code='1', name='Parent')
        self.child_indicator = Indicator.objects.create(code='2', name='Child')
        self.child_indicator.prerequisites.set([self.indicator])

        self.task = Task.objects.create(project=self.project, organization=self.parent_org, indicator=self.indicator)
        self.other_task = Task.objects.create(project=self.project, organization=self.other_org, indicator=self.indicator)
        self.child_task = Task.objects.create(project=self.project, organization=self.child_org, indicator=self.indicator)
        self.inactive_task = Task.objects.create(project=self.planned_project, organization=self.parent_org, indicator=self.indicator)

    def test_task_admin_view(self):
        '''
        Admins should be able to see all tasks.
        '''
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/manage/tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 4)

    def test_task_non_admin(self):
        '''
        Others should only see relevent tasks, their org/child orgs.
        '''
        self.client.force_authenticate(user=self.manager)
        response = self.client.get('/api/manage/tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_task_create(self):
        '''
        Test that a task can be created with the below payload
        '''
        self.client.force_authenticate(user=self.admin)
        valid_payload = {
            'organization_id': self.other_org.id,
            'indicator_id': self.child_indicator.id,
            'project_id': self.project.id,
        }
        response = self.client.post('/api/manage/tasks/', valid_payload, format='json')
        print(response.json())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        task = Task.objects.get(organization=self.other_org, indicator=self.child_indicator, project=self.project)
        self.assertEqual(task.created_by, self.admin)
    
    def test_task_create_wrong_org(self):
        '''
        If an organizaiton is not in a project, you cannot assign them a task for that project.
        '''
        self.client.force_authenticate(user=self.admin)
        valid_payload = {
            'organization_id': self.loser_org.id,
            'indicator_id': self.indicator.id,
            'project_id': self.project.id,
        }
        response = self.client.post('/api/manage/tasks/', valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_task_create_no_prereq(self):
        '''
        Kind of an odd move to assign an indicator a prerequisite then assign it without assigning the 
        prereq first, right?
        '''
        self.client.force_authenticate(user=self.admin)
        valid_payload = {
            'organization_id': self.child_org.id,
            'indicator_id': self.child_indicator.id,
            'project_id': self.project_2.id,
        }
        response = self.client.post('/api/manage/tasks/', valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        valid_payload = {
            'organization_id': self.child_org.id,
            'indicator_id': self.indicator.id,
            'project_id': self.project_2.id,
        }
        response = self.client.post('/api/manage/tasks/', valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        valid_payload = {
            'organization_id': self.child_org.id,
            'indicator_id': self.child_indicator.id,
            'project_id': self.project_2.id,
        }
        response = self.client.post('/api/manage/tasks/', valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_task_create_child(self):
        '''
        Non admins can create tasks for organizations marked as their child for the project
        '''
        self.client.force_authenticate(user=self.manager)
        valid_payload = {
            'organization_id': self.child_org.id,
            'indicator_id': self.child_indicator.id,
            'project_id': self.project.id,
        }
        response = self.client.post('/api/manage/tasks/', valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        #though this is project specific
        valid_payload = {
            'organization_id': self.child_org.id,
            'indicator_id': self.child_indicator.id,
            'project_id': self.project_2.id,
        }
        response = self.client.post('/api/manage/tasks/', valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_task_assign_other_self(self):
        '''
        Non admins also cannot assign tasks to unrelated orgs or themselves
        '''
        self.client.force_authenticate(user=self.manager)
        valid_payload = {
            'organization_id': self.other_org.id,
            'indicator_id': self.child_indicator.id,
            'project_id': self.project.id,
        }
        response = self.client.post('/api/manage/tasks/', valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        valid_payload = {
            'organization_id': self.parent_org.id,
            'indicator_id': self.child_indicator.id,
            'project_id': self.project.id,
        }
        response = self.client.post('/api/manage/tasks/', valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_delete_task(self):
        '''
        Admins should be allowed to delete tasks.
        '''
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f'/api/manage/tasks/{self.other_task.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    
    def test_delete_task_prereq(self):
        '''
        But not if they have downstream tasks.
        '''
        child_task = Task.objects.create(organization=self.parent_org, indicator=self.child_indicator, project=self.project)
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f'/api/manage/tasks/{self.task.id}/')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
    
    def test_delete_task_inter(self):
        '''
        Or if they have an interaction.
        '''
        respondent = Respondent.objects.create(
            is_anonymous=True,
            age_range=Respondent.AgeRanges.ET_24,
            village='Testingplace',
            district=Respondent.District.CENTRAL,
            citizenship='test',
            sex=Respondent.Sex.FEMALE,
        )
        interaction = Interaction.objects.create(task=self.task, respondent=respondent, interaction_date='2025-06-23')
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f'/api/manage/tasks/{self.task.id}/')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
