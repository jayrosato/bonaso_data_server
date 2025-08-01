from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views import View
from django.db.models import Q
from rest_framework.viewsets import ModelViewSet
from rest_framework import filters
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework import generics
from rest_framework.decorators import action
from rest_framework import status
from django.db import transaction
from users.restrictviewset import RoleRestrictedViewSet
from organizations.models import Organization
from projects.models import Project
from django.shortcuts import get_object_or_404
from indicators.models import Indicator
from django.contrib.auth import get_user_model
from analysis.serializers import DashboardSettingSerializer, DashboardSettingListSerializer, DashboardIndicatorChartSerializer
from analysis.models import DashboardSetting, IndicatorChartSetting, ChartField, DashboardIndicatorChart, ChartFilter, ChartIndicator
from events.models import DemographicCount
from respondents.utils import get_enum_choices
from datetime import date
import csv
from django.utils.timezone import now
from datetime import datetime
from analysis.utils.aggregates import aggregates_switchboard, prep_csv
from io import StringIO
User = get_user_model()

#we may potentially need to rethink the user perms if we have to link this to other sites
class AnalysisViewSet(RoleRestrictedViewSet):
    @action(detail=False, methods=["get"], url_path='aggregate/(?P<indicator_id>[^/.]+)')
    def indicator_aggregate(self, request, indicator_id=None):
        '''
        Action that pulls indicators and gets the counts as a JSON object.
        '''
        user = request.user
        if user.role not in ['client', 'admin', 'meofficer', 'manager']:
            return Response(
                {"detail": "You do not have permission to view aggregated counts."},
                status=status.HTTP_403_FORBIDDEN
            )

        '''
        Get the indicator
        '''
        indicator = Indicator.objects.filter(id=indicator_id).first()
        if not indicator:
            return Response(
                {"detail": "Please provide a valid indicator id to view aggregate counts."},
                status=status.HTTP_400_BAD_REQUEST
            )
        '''
        Get any filter params
        '''
        project_id = request.query_params.get('project')
        organization_id = request.query_params.get('organization')
        start = request.query_params.get('start')
        end = request.query_params.get('end')
        project = Project.objects.filter(id=project_id).first() if project_id else None
        organization = Organization.objects.filter(id=organization_id) if organization_id else None

        params = {}
        for cat in ['age_range', 'sex', 'kp_type', 'disability_type', 'citizenship', 'hiv_status', 'pregnancy', 'subcategory']:
            params[cat] = request.query_params.get(cat) in ['true', '1']
        #special social media param
        platform = request.query_params.get('platform') in ['true', '1']
        
        #split, i.e. time period
        split = request.query_params.get('split')
        #aggregator function from anlysis.utils
        aggregate = aggregates_switchboard(user, indicator, params, split, project, organization, start, end, None, platform)
        return Response(
                {"counts": aggregate},
                status=status.HTTP_200_OK
            )
    
    @action(detail=False, methods=["get"], url_path='download-indicator-aggregate/(?P<indicator_id>[^/.]+)')
    def download_indicator_aggregate(self, request, indicator_id=None):
        '''
        Very similar to the above action but takes the extra step to conver the data to csv format with a header row.
        '''
        user = request.user
        if user.role not in ['client', 'admin', 'meofficer', 'manager']:
            return Response(
                {"detail": "You do not have permission to view aggregated counts."},
                status=status.HTTP_403_FORBIDDEN
            )

        indicator = Indicator.objects.filter(id=indicator_id).first()
        if not indicator:
            return Response(
                {"detail": "Please provide a valid indicator id to view aggregate counts."},
                status=status.HTTP_400_BAD_REQUEST
            )

        params = {}
        for cat in ['age_range', 'sex', 'kp_type', 'disability_type', 'citizenship', 'hiv_status', 'pregnancy']:
            params[cat] = request.query_params.get(cat) in ['true', '1']
        split = request.query_params.get('split')
        aggregates = aggregates_switchboard(user, indicator, params, split)

        if not aggregates:
            return Response(
                {"detail": "No aggregate data found for this indicator."},
                status=status.HTTP_404_NOT_FOUND
            )

        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f'aggregates_{indicator.code}_{timestamp}.csv'

        #convert tot csv
        rows = prep_csv(aggregates, params)
        fieldnames = rows[0]
        buffer = StringIO()
        writer = csv.DictWriter(buffer, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows[1:]:
            row_dict = dict(zip(fieldnames, row))
            writer.writerow(row_dict)

        response = HttpResponse(buffer.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

class DashboardSettingViewSet(RoleRestrictedViewSet):
    serializer_class = DashboardSettingSerializer  # default

    def get_serializer_class(self):
        if self.action == 'list':
            return DashboardSettingListSerializer #for panel showing list of dashboards
        else:
            return DashboardSettingSerializer #for dedicated views
        
    def get_queryset(self):
        return DashboardSetting.objects.filter(created_by=self.request.user) #only see your dashboards
    
    @action(detail=False, methods=['get'], url_path='meta')
    def get_meta(self, request):
        '''
        Get labels for the front end to assure consistency.
        '''
        return Response({
            "chart_types": get_enum_choices(IndicatorChartSetting.ChartType),
            "fields": get_enum_choices(ChartField.Field),
            "axes": get_enum_choices(IndicatorChartSetting.AxisOptions)
        })

    @action(detail=True, methods=['patch'], url_path='charts')
    @transaction.atomic
    def create_update_chart(self, request, pk=None):
        '''
        Custom action for creating/updating chart settings. Controlled action allows for real time simple updates
        and logic.
        '''
        dashboard = self.get_object()
        user = request.user
        #indicator(s) and chart type is required. It is a chart after all
        existing_id = request.data.get('chart_id')
        indicator_ids = request.data.get('indicators')

        if not indicator_ids:
            return Response(
                    {"detail": f'At least one indicator is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        #get indicator objects and make sure no bad IDs were provided
        indicators = []
        for ii in indicator_ids:
            indicator = Indicator.objects.filter(id=ii).first()
            if not indicator:
                return Response(
                    {"detail": f'"{ii}" is not a valid indicator id.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            indicators.append(indicator)

        chart_type = request.data.get('chart_type')
        if not chart_type:
            return Response(
                {"detail": "A valid chart type is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        #get the fields
        legend = request.data.get('legend') #chart legend
        axis = request.data.get('axis') #chart axis
        stack = request.data.get('stack') #stack (for bar charts)
        use_target = str(request.data.get('use_target')).lower() in ['true', '1'] #show targets if provided
        tabular = str(request.data.get('tabular')).lower() in ['true', '1'] #show a data table underneath
        order = request.data.get('order', DashboardIndicatorChart.objects.filter(dashboard=dashboard).count())
        width = request.data.get('width')
        height = request.data.get('height')
        
        
        #if multiple indicators were provided, that's the legend, so remove an existing settings
        if len(indicators) > 1:
            legend=None
            stack=None
            use_target=False

        if len(indicators) ==1:
            #validate that subcategories exist if chosen
            if legend == 'subcategory' and not indicators[0].subcategories.exists():
                legend=None
            if stack == 'subcategory' and not indicators[0].subcategories.exists():
                stack=None

        #remove legend/stack for use_target (since targets are not demographically split)
        if legend and use_target:
                legend = None
        if stack and use_target:
            stack=None

        #if the chart exists, update it
        if existing_id:    
            chart_link = get_object_or_404(DashboardIndicatorChart, id=existing_id)
            chart = chart_link.chart
            chart.chart_type = chart_type
            chart.axis = axis
            chart.use_target = use_target
            chart.legend = legend
            chart.stack = stack
            chart.tabular = tabular
            chart.save()

            chart_link.width = width
            chart_link.height = height
            chart_link.order = order
            chart_link.save()
        #else create a new one
        else:
            chart = IndicatorChartSetting.objects.create(
                chart_type = chart_type,
                tabular = tabular,
                axis = axis,
                legend = legend,
                stack=stack,
                use_target = use_target,
                created_by=user,
            )
            chart_link = DashboardIndicatorChart.objects.create(
                dashboard=dashboard,
                chart = chart,
                width = width,
                height = height,
                order = order,
            )

        #clear then bulk create indicators
        ChartIndicator.objects.filter(chart=chart).delete()
        bulk_links = [
        ChartIndicator(chart=chart, indicator=indicator)
            for indicator in indicators
        ]
        ChartIndicator.objects.bulk_create(bulk_links)

        #serialize the data
        serializer = DashboardIndicatorChartSerializer(chart_link)
        msg = "Dashboard chart created." if not existing_id else "Dashboard chart updated."
        return Response({"detail": msg, "chart_data": serializer.data}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='filters/(?P<chart_link_id>[^/.]+)')
    @transaction.atomic
    def update_chart_filters(self, request, pk=None, chart_link_id=None):
        chart_link = get_object_or_404(DashboardIndicatorChart, id=chart_link_id)
        chart = chart_link.chart
        filters_map = request.data.get('filters', {})
        if not isinstance(filters_map, dict):
            return Response({"detail": "Invalid filters format, expected an object."}, status=status.HTTP_400_BAD_REQUEST)

        # Delete existing filters for this chart
        ChartFilter.objects.filter(chart=chart).delete()

        # Create new filters
        for field_name, values in filters_map.items():
            print(field_name, values)
            try:
                field_obj = ChartField.objects.get(name=field_name)
            except ChartField.DoesNotExist:
                return Response({"detail": f"Invalid filter field: '{field_name}'"}, status=status.HTTP_400_BAD_REQUEST)

            if not isinstance(values, list):
                return Response({"detail": f"Values for field '{field_name}' must be a list."}, status=status.HTTP_400_BAD_REQUEST)

            for val in values:
                ChartFilter.objects.create(field=field_obj, value=val, chart=chart)

        #serialize the data
        serializer = DashboardIndicatorChartSerializer(chart_link)
        msg = "Filters updated!"
        return Response({"detail": msg, "chart_data": serializer.data}, status=status.HTTP_200_OK)


    @action(detail=True, methods=['delete'], url_path='remove-chart/(?P<chart_link_id>[^/.]+)')
    def remove_chart(self, request, pk=None, chart_link_id=None):
        '''
        Delete your chart.
        '''
        dashboard = self.get_object()
        user = request.user
        IndicatorChartSetting.objects.filter(id=chart_link_id).delete()
        return Response({"detail": f"Removed chart from dashboard.", "id": chart_link_id}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='breakdowns')
    def get_breakdowns_meta(self, request):
        '''
        Map the front end can use to get prettier names for the user.
        '''
        breakdowns = {}

        # Loop over desired choice fields
        choice_fields = ['sex', 'age_range', 'kp_type', 'disability_type', 'citizenship', 'hiv_status', 'pregnancy']

        for field_name in choice_fields:
            field = DemographicCount._meta.get_field(field_name)
            if field.choices:
                breakdowns[field_name] = {
                    choice: label for choice, label in field.choices
                }

        return Response(breakdowns)