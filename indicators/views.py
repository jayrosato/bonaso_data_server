from django.shortcuts import render, redirect
from django.forms.models import model_to_dict
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from users.restrictviewset import RoleRestrictedViewSet
from rest_framework.decorators import action
from indicators.models import Indicator, IndicatorSubcategory
from indicators.serializers import IndicatorSerializer, IndicatorListSerializer, ChartSerializer
from projects.models import ProjectIndicator, Project
from respondents.models import Interaction
from rest_framework import status

def topological_sort(indicators):
    from collections import defaultdict, deque

    graph = defaultdict(list)
    in_degree = defaultdict(int)

    for indicator in indicators:
        if indicator.prerequisite:
            graph[indicator.prerequisite.id].append(indicator.id)
            in_degree[indicator.id] += 1
        else:
            in_degree[indicator.id] += 0

    id_map = {indicator.id: ind for ind in indicators}

    queue = deque([id for id in in_degree if in_degree[id] == 0])
    sorted_ids = []

    while queue:
        current = queue.popleft()
        sorted_ids.append(current)
        for dependent in graph[current]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    if len(sorted_ids) != len(indicators):
        raise Exception("Cycle detected in prerequisites")

    return [id_map[i] for i in sorted_ids]

class IndicatorViewSet(RoleRestrictedViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Indicator.objects.all()
    serializer_class = IndicatorSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['project', 'prerequisite', 'status']
    ordering_fields = ['code', 'name']
    search_fields = ['name', 'code', 'description'] 
    def get_queryset(self):
        queryset = super().get_queryset() 
        user = self.request.user
        if user.role != 'admin' and user.role !='client':
            queryset = queryset.filter(status=Indicator.Status.ACTIVE)
            queryset = queryset.filter(
                projectindicator__project__organizations__id=user.organization.id
            )
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(projectindicator__project__id=project_id)
        prereq_id = self.request.query_params.get('prerequisite')
        if prereq_id:
            queryset = queryset.filter(prerequisite__id = prereq_id)
        return queryset

    @action(detail=False, methods=['get'], url_path='chart-data')
    def chart_data(self, request):
        queryset = self.get_queryset()

        # Optional filters from query parameters
        indicator_id = request.query_params.get('indicator')
        organization_id = request.query_params.get('organization')
        project_id = request.query_params.get('project')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if indicator_id:
            queryset = queryset.filter(id=indicator_id)

        queryset = queryset.distinct()

        # Skip pagination
        self.pagination_class = None
        serializer = ChartSerializer(queryset, context={'organization_id': organization_id, 'project_id': project_id}, many=True)
        return Response(serializer.data)

    def paginate_queryset(self, queryset):
        # Disable pagination only for this specific action
        if self.action == 'chart_data':
            return None
        return super().paginate_queryset(queryset)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return IndicatorListSerializer
        else:
            return IndicatorSerializer
        
    def create(self, request, *args, **kwargs):
        if request.user.role != 'admin':
            raise PermissionDenied("Only admins can create indicators.")
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        if request.user.role != 'admin':
            raise PermissionDenied("Only admins can create indicators.")
        return super().update(request, *args, **kwargs)


    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user) 

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user) 

    def destroy(self, request, *args, **kwargs):
        user = request.user
        instance = self.get_object()

        if user.role != 'admin':
            return Response(
                {"detail": "You do not have permission to delete an indicator."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if instance.status == Indicator.Status.ACTIVE:
            return Response(
                {"detail": "You cannot delete an active indicator. Consider marking this as deprecated instead."},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Prevent deletion if indicator has interactions
        if Interaction.objects.filter(task__indicator__id=instance.id).exists():
            return Response(
                {"detail": "You cannot delete an indicator that has interactions associated with it."},
                status=status.HTTP_400_BAD_REQUEST
            )

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='meta')
    def filter_options(self, request):
        statuses = [status for status, _ in Indicator.Status.choices]
        return Response({
            'statuses': statuses,
        })

'''
class GetIndicator(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk, resp):
        from respondents.models import Respondent, Interaction
        from projects.models import Task
        user=self.request.user
        org = user.organization
        indicator = Indicator.objects.filter(id=pk, status='Active').first()
        options = IndicatorSubcategory.objects.filter(indicator=indicator)
        tasks = Task.objects.filter(indicator=indicator)
        preReqTasks = Task.objects.filter(indicator=indicator.prerequisite)
        respondent = Respondent.objects.filter(id=resp).first()
        prereqInteractions = Interaction.objects.filter(task__in=preReqTasks, respondent=respondent)
        data=({
            'indicator': {
                'id': indicator.id,
                'code': indicator.code,
                'name': indicator.name,
                'description': indicator.description,
                'prerequisite': None,
                'options': [],
                'interactions':[],
            }
        })
        if indicator.prerequisite:
            data['indicator']['prerequisite'] = {
                'id': indicator.prerequisite.id,
                'code': indicator.prerequisite.code,
                'name': indicator.prerequisite.name,
                'prerequisite_interactions': [],
            }
            for interaction in prereqInteractions:
                data['indicator']['prerequisite']['prerequisite_interactions'].append({
                    'id': interaction.id,
                    'respondent': interaction.respondent.id,
                    'category': interaction.subcategory.id,
                    'date': interaction.interaction_date,
                })
        for option in options:
            data['indicator']['options'].append({
                'id': option.id,
                'name': option.name,
                'code': option.code,
            })
        print(data)
        twelve_months_ago = timezone.now() - timedelta(days=365)
        for task in tasks:
            interactions = Interaction.objects.filter(task=task, interaction_date__gte=twelve_months_ago, respondent=respondent)
            for interaction in interactions:
                if interaction.prerequisite:
                    prereq = {
                        'code': interaction.task.indicator.prerequisite.code,
                        'name': interaction.task.indicator.prerequisite.name,
                        'id': interaction.prerequisite.id,
                        'date': interaction.prerequisite.interaction_date,
                    }
                else: prereq = None
                if interaction.created_by:
                    org = interaction.created_by.organization.name
                else:
                    org=None
                if interaction.subcategory:
                    categoryID =  interaction.subcategory.id
                    categoryName = interaction.subcategory.name
                else:
                    categoryID = None
                    categoryName = None
                data['indicator']['interactions'].append({
                    'id': interaction.id,
                    'date': interaction.interaction_date,
                    'category_id': categoryID,
                    'category_name': categoryName, 
                    'organization': org,
                    'prerequisite': prereq,
                })
        return JsonResponse(data, safe=False)
'''