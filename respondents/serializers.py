from rest_framework import serializers
from respondents.models import Respondent, Interaction, Pregnancy, HIVStatus, KeyPopulation, DisabilityType
from respondents.exceptions import DuplicateExists
from projects.models import Task, Target
from projects.serializers import TaskSerializer
from indicators.models import IndicatorSubcategory
from indicators.serializers import IndicatorSubcategorySerializer
from datetime import datetime, date
from django.db.models import Q
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
User = get_user_model()

class RespondentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Respondent
        fields = ['id', 'uuid', 'is_anonymous', 'first_name', 'last_name', 'sex', 
                  'village', 'district', 'citizenship', 'comments']

class KPSerializer(serializers.ModelSerializer):
    class Meta:
        model = KeyPopulation
        fields = ['id', 'name']

class DisabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DisabilityType
        fields = ['id', 'name']

class SensitiveInfoSerializer(serializers.ModelSerializer):
    is_pregnant = serializers.BooleanField(write_only=True, required=False, default=False)
    hiv_positive = serializers.BooleanField(write_only=True, required=False, default=False)
    term_began = serializers.DateField(write_only=True, required=False, allow_null=True)
    term_ended = serializers.DateField(write_only=True, required=False, allow_null=True)
    date_positive = serializers.DateField(write_only=True, required=False, allow_null=True)

    pregnancy_info = serializers.SerializerMethodField(read_only=True)
    hiv_status_info = serializers.SerializerMethodField(read_only=True)

    kp_status = KPSerializer(read_only=True, many=True)
    kp_status_names = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
    
    disability_status = DisabilitySerializer(read_only=True, many=True)
    disability_status_names = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
    
    def get_pregnancy_info(self, obj):
        pregnancy = obj.pregnancy_set.order_by('-term_began').first()
        if pregnancy and not pregnancy.term_ended:
            return {
                "is_pregnant": pregnancy.is_pregnant,
                "term_began": pregnancy.term_began,
                "term_ended": pregnancy.term_ended,
            }
        return None

    def get_hiv_status_info(self, obj):
        hiv_status = obj.hivstatus_set.order_by('-date_positive').first()
        if hiv_status:
            return {
                "hiv_positive": hiv_status.hiv_positive,
                "date_positive": hiv_status.date_positive,
            }
        return None
    
    class Meta:
        model = Respondent
        fields = ['id', 'is_pregnant', 'term_began', 'term_ended', 'hiv_positive', 'date_positive',
                  'kp_status', 'kp_status_names', 'pregnancy_info', 'hiv_status_info', 'disability_status', 
                  'disability_status_names', 'created_by', 'updated_by']
        
    def create(self, validated_data):
        today = date.today()
        term_began = validated_data.pop('term_began', None)
        term_ended = validated_data.pop('term_ended', None)
        is_pregnant = validated_data.pop('is_pregnant', False)
        kp_status_names = validated_data.pop('kp_status_names', [])
        disability_status_names = validated_data.pop('disability_status_names', [])
        hiv_positive = validated_data.pop('hiv_positive', False)
        date_positive = validated_data.pop('date_positive', None)

        respondent = Respondent.objects.create(**validated_data)

        if is_pregnant in ['true', 'True', True, '1']:
            is_pregnant = True
        else:
            is_pregnant = False

        existing_pregnancy = Pregnancy.objects.filter(respondent=respondent, term_ended__isnull=True).order_by('-term_began').first()

        if is_pregnant:
            if not term_began:
                term_began = today
            if existing_pregnancy:
                existing_pregnancy.is_pregnant = True
                existing_pregnancy.term_began = term_began
                existing_pregnancy.term_ended = None
                existing_pregnancy.save()
            else:
                Pregnancy.objects.create(respondent=respondent, is_pregnant=True, term_began=term_began)
        else:
            if existing_pregnancy and not term_ended:
                term_ended = term_ended or today
            if existing_pregnancy:
                existing_pregnancy.is_pregnant = False
                existing_pregnancy.term_ended = term_ended
                existing_pregnancy.save()
        
        if hiv_positive in ['true', 'True', True, '1']:
            hiv_positive = True
        else:
            hiv_positive = False
        existing_status = HIVStatus.objects.filter(respondent=respondent).first()
        if existing_status:
            existing_status.hiv_positive = hiv_positive
            existing_status.date_positive = date_positive if hiv_positive else None
            existing_status.save()
        else:
            if not date_positive:
                date_positive = date.today()
            HIVStatus.objects.create(
                respondent=respondent,
                hiv_positive=hiv_positive,
                date_positive=date_positive if hiv_positive else None
            )

        kp_types = []
        valid_names = [name for name, _ in KeyPopulation.KeyPopulations.choices]
        for name in kp_status_names:
            if name in valid_names:
                kp, _ = KeyPopulation.objects.get_or_create(name=name)
                kp_types.append(kp)
        respondent.kp_status.set(kp_types)

        disability_types = []
        valid_names = [name for name, _ in DisabilityType.DisabilityTypes.choices]
        for name in disability_status_names:
            if name in valid_names:
                dis, _ = DisabilityType.objects.get_or_create(name=name)
                disability_types.append(dis)
        respondent.disability_status.set(disability_types)
        return respondent

    def update(self, instance, validated_data):
        today = date.today()
        term_began = validated_data.pop('term_began', None)
        term_ended = validated_data.pop('term_ended', None)
        is_pregnant = validated_data.pop('is_pregnant', False)
        hiv_positive = validated_data.pop('hiv_positive', False)
        date_positive = validated_data.pop('date_positive', None)
        kp_status_names = validated_data.pop('kp_status_names', [])
        disability_status_names = validated_data.pop('disability_status_names', [])
        respondent = instance
        if is_pregnant in ['true', 'True', True, '1']:
            is_pregnant = True
        else:
            is_pregnant = False

        existing_pregnancy = Pregnancy.objects.filter(respondent=instance, term_ended__isnull=True).order_by('-term_began').first()

        if is_pregnant:
            if not term_began:
                term_began = today
            if existing_pregnancy:
                existing_pregnancy.is_pregnant = True
                existing_pregnancy.term_began = term_began
                existing_pregnancy.term_ended = None
                existing_pregnancy.save()
            else:
                Pregnancy.objects.create(respondent=instance, is_pregnant=True, term_began=term_began)
        else:
            if existing_pregnancy and not term_ended:
                term_ended = term_ended or today
            if existing_pregnancy:
                existing_pregnancy.is_pregnant = False
                existing_pregnancy.term_ended = term_ended
                existing_pregnancy.save()
        
        
        if hiv_positive in ['true', 'True', True, '1']:
            hiv_positive = True
        else:
            hiv_positive = False
        existing_status = HIVStatus.objects.filter(respondent=respondent).first()
        if existing_status:
            existing_status.hiv_positive = hiv_positive
            existing_status.date_positive = date_positive if hiv_positive else None
            existing_status.save()
        else:
            if not date_positive:
                date_positive = date.today()
            HIVStatus.objects.create(
                respondent=respondent,
                hiv_positive=hiv_positive,
                date_positive=date_positive if hiv_positive else None
            )

        kp_types = []
        valid_names = [name for name, _ in KeyPopulation.KeyPopulations.choices]
        for name in kp_status_names:
            if name in valid_names:
                kp, _ = KeyPopulation.objects.get_or_create(name=name)
                kp_types.append(kp)
        instance.kp_status.set(kp_types)

        disability_types = []
        valid_names = [name for name, _ in DisabilityType.DisabilityTypes.choices]
        for name in disability_status_names:
            if name in valid_names:
                dis, _ = DisabilityType.objects.get_or_create(name=name)
                disability_types.append(dis)
        respondent.disability_status.set(disability_types)
        return instance
    
class RespondentSerializer(serializers.ModelSerializer):
    id_no = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    dob = serializers.DateField(required=False, allow_null=True)
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()

    def get_created_by(self, obj):
        print(obj.created_by)
        if obj.created_by:
            return {
                "id": obj.created_by.id,
                "username": obj.created_by.username,
                "first_name": obj.created_by.first_name,
                "last_name": obj.created_by.last_name,
            }

    def get_updated_by(self, obj):
        if obj.updated_by:
            return {
                "id": obj.updated_by.id,
                "username": obj.updated_by.username,
                "first_name": obj.updated_by.first_name,
                "last_name": obj.updated_by.last_name,
            }
        
    class Meta:
        model=Respondent
        fields = [
            'id','id_no', 'uuid', 'is_anonymous', 'first_name', 'last_name', 'sex', 'ward',
            'village', 'district', 'citizenship', 'comments', 'email', 'phone_number', 'dob',
            'age_range', 'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
    def validate(self, attrs):
        user = self.context['request'].user
        role = getattr(user, 'role', None)
        if role == 'client':
            raise PermissionDenied("You do not have permission to make edits to interactions.")
        
        id_no = attrs.get('id_no')
        if id_no:
            if self.instance:
                existing = Respondent.objects.filter(id_no=id_no).exclude(id=self.instance.id)
            else:
                existing = Respondent.objects.filter(id_no=id_no)
            if existing.exists():
                raise DuplicateExists(
                    detail="This respondent already exists.",
                    existing_id=existing.first().id
                )
        return attrs
    

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)

        if instance.is_anonymous:
            instance.first_name = None
            instance.dob = None
            instance.ward = None
            instance.id_no = None
            instance.email = None
            instance.phone_number = None

            instance.save()  # Ensure changes are persisted
        return instance

class SimpleInteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model=Interaction
        fields = [
            'id', 'interaction_date', 'flagged'
        ]

class InteractionSerializer(serializers.ModelSerializer):
    respondent = serializers.PrimaryKeyRelatedField(queryset=Respondent.objects.all())
    task = serializers.PrimaryKeyRelatedField(queryset=Task.objects.all(), write_only=True)
    task_detail = TaskSerializer(source='task', read_only=True)
    subcategories = IndicatorSubcategorySerializer(many=True, read_only=True)
    subcategory_names = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False
    )
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()

    def get_created_by(self, obj):
        print(obj.created_by)
        if obj.created_by:
            return {
                "id": obj.created_by.id,
                "username": obj.created_by.username,
                "first_name": obj.created_by.first_name,
                "last_name": obj.created_by.last_name,
            }

    def get_updated_by(self, obj):
        if obj.updated_by:
            return {
                "id": obj.updated_by.id,
                "username": obj.updated_by.username,
                "first_name": obj.updated_by.first_name,
                "last_name": obj.updated_by.last_name,
            }
    class Meta:
        model=Interaction
        fields = [
            'id', 'respondent', 'subcategories','subcategory_names', 'task', 'task_detail',
            'interaction_date', 'numeric_component', 'created_by', 'updated_by', 'created_at', 'updated_at',
            'comments', 'flagged',
        ]
    
    def to_internal_value(self, data):
        subcat = data.get('subcategory_names', None)
        if subcat == '':
            data['subcategory_names'] = []
        return super().to_internal_value(data)

    def validate(self, data):
        from organizations.models import Organization
        user = self.context['request'].user
        if user.role == 'client':
                raise PermissionDenied('You do not have permission to perform this action.')
        task = data.get('task') or getattr(self.instance, 'task', None)
        respondent = data.get('respondent') or getattr(self.instance, 'respondent', None)
        subcategory_names = data.get('subcategory_names', [])
        interaction_date = data.get('interaction_date')
        number = data.get('numeric_component')
        role = getattr(user, 'role', None)
        org = getattr(user, 'organization', None)

        if role == 'client':
            raise PermissionDenied("You do not have permission to make edits to interactions.")
        if role != 'admin':
            if not org:
                raise PermissionDenied("User must belong to an organization.")

            # Ensure the task is part of the user's org or child orgs
            if role in ['meofficer', 'manager']:
                allowed_org_ids = Organization.objects.filter(
                    Q(parent_organization=org) | Q(id=org.id)
                ).values_list('id', flat=True)
            else:
                allowed_org_ids = [org.id]

            if task.organization_id not in allowed_org_ids:
                raise PermissionDenied(
                    "You may not create or edit interactions not related to your organization or its child organizations."
                )
    
        if not interaction_date:
            raise serializers.ValidationError("Interaction date is required.")
        #parsed_date = datetime.fromisoformat(interaction_date).date()
        if interaction_date > date.today():
            raise serializers.ValidationError("Interaction date may not be in the future.")
        if interaction_date < task.project.start or interaction_date > task.project.end:
            raise serializers.ValidationError("This interaction is set for a date outside of the project boundaries.")
        

        requires_number = task.indicator.require_numeric
        if requires_number:
            try:
                if number in [None, '']:
                    raise ValueError
                int(number) 
            except (ValueError, TypeError):
                raise serializers.ValidationError("Task requires a valid number.")
        else:
            if number in ['', '0']:
                data['numeric_component'] = None
            elif number not in [None, 0, '0']:
                raise serializers.ValidationError("Task does not expect a number.")

        if task.indicator.subcategories.exists():
            if not subcategory_names or subcategory_names in [None, '', []]:
                raise serializers.ValidationError("Subcategories required for this task.")
        else:
            if not subcategory_names or subcategory_names in [None, '', []]:
                data['subcategory_names'] = []

        prereq = task.indicator.prerequisite
        if prereq:
            parent_qs = Interaction.objects.filter(
                task__indicator=prereq,
                interaction_date__lte=interaction_date,
                respondent=respondent,
            )
            if not parent_qs.exists():
                raise serializers.ValidationError(f"Task '{task.indicator.name}' requires that a prerequisite interaction {task.indicator.prerequisite.name} occured prior to or on the date of this interaction. If you are editing dates, please make sure you are not placing this interaciton prior to the prerequisite one.")
            most_recent = parent_qs.order_by('-interaction_date').first()
            if most_recent.subcategories.exists():
                parent_ids = set(most_recent.task.indicator.subcategories.values_list('id', flat=True))
                if set(task.indicator.subcategories.values_list('id', flat=True)) == parent_ids:
                    current_ids = set(
                        IndicatorSubcategory.objects.filter(name__in=subcategory_names).values_list('id', flat=True)
                    )
                    previous_ids = set(most_recent.subcategories.values_list('id', flat=True))
                    if not current_ids.issubset(previous_ids):
                        raise serializers.ValidationError(
                            "Subcategories must be consistent with the prerequisite interaction."
                        )
        return data
    
    def validate_interaction_date(self, value):
        if not value:
            raise serializers.ValidationError('Date is required.')
        return value
    
    def create(self, validated_data):
        user = self.context['request'].user
        respondent = validated_data.pop('respondent', None) or self.context.get('respondent')

        subcategory_names = validated_data.pop('subcategory_names', [])
        interaction = Interaction.objects.create(
            respondent=respondent,
            created_by=user,
            **validated_data
        )
        subcategories = [
            IndicatorSubcategory.objects.get_or_create(name=name)[0]
            for name in subcategory_names
        ]
        interaction.subcategories.set(subcategories)
        
        return interaction
    
    def update(self, instance, validated_data):
        user = self.context['request'].user
        created_by = instance.created_by
        if user.role not in ['meofficer', 'manager', 'admin']:
            if instance.created_by != user:
                raise PermissionDenied("You may only edit your interactions.")

        subcategory_names = validated_data.pop('subcategory_names', [])
        subcategories = [
            IndicatorSubcategory.objects.get_or_create(name=name)[0]
            for name in subcategory_names
        ]
        instance.subcategories.set(subcategories)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.updated_by = user
        instance.save()
        return instance



