from rest_framework import viewsets

from lego.apps.interest_groups.models import InterestGroup
from lego.apps.interest_groups.serializers import InterestGroupSerializer


class InterestGroupViewSet(viewsets.ModelViewSet):
    queryset = InterestGroup.objects.all()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CompanyCreateAndUpdateSerializer

        elif self.action in ['retrieve', 'destroy']:
            return CompanyReadDetailedSerializer

        return CompanyReadSerializer


class SemesterStatusViewSet(viewsets.ModelViewSet):
    queryset = SemesterStatus.objects.all()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SemesterStatusCreateAndUpdateSerializer

        return SemesterStatusReadSerializer

    def get_queryset(self):

        if self.action in ['retrieve', 'destroy']:
            company_id = self.kwargs.select_related('company').get('company_pk', None)
            return SemesterStatus.objects.filter(company=company_id)
        return self.queryset


class CompanyContactViewSet(viewsets.ModelViewSet):
    queryset = CompanyContact.objects.all()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CompanyContactCreateAndUpdateSerializer

        return CompanyContactReadSerializer

    def get_queryset(self):

        if self.action in ['retrieve', 'destroy']:
            company_id = self.kwargs.select_related('company').get('company_pk', None)
            return CompanyContact.objects.filter(company=company_id)
        return self.queryset