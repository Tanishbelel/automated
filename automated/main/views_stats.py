from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Avg, Sum
from .models import FileAnalysis, MetadataEntry
from datetime import timedelta
from django.utils import timezone

class StatsView(APIView):
    
    def get(self, request):
        user = request.user if request.user.is_authenticated else None
        
        queryset = FileAnalysis.objects.all()
        if user:
            queryset = queryset.filter(user=user)
        
        total_files = queryset.count()
        avg_risk_score = queryset.aggregate(Avg('risk_score'))['risk_score__avg'] or 0
        total_metadata_removed = queryset.filter(status='cleaned').aggregate(
            Sum('metadata_count')
        )['metadata_count__sum'] or 0
        
        platform_stats = queryset.values('platform').annotate(
            count=Count('id'),
            avg_risk=Avg('risk_score')
        )
        
        risk_distribution = {
            'critical': queryset.filter(risk_score__gte=75).count(),
            'high': queryset.filter(risk_score__gte=50, risk_score__lt=75).count(),
            'medium': queryset.filter(risk_score__gte=25, risk_score__lt=50).count(),
            'low': queryset.filter(risk_score__lt=25).count(),
        }
        
        last_30_days = timezone.now() - timedelta(days=30)
        recent_files = queryset.filter(created_at__gte=last_30_days).count()
        
        return Response({
            'total_files_analyzed': total_files,
            'average_risk_score': round(avg_risk_score, 2),
            'total_metadata_removed': total_metadata_removed,
            'files_last_30_days': recent_files,
            'platform_statistics': list(platform_stats),
            'risk_distribution': risk_distribution
        })


class MetadataCategoryStatsView(APIView):
    
    def get(self, request):
        user = request.user if request.user.is_authenticated else None
        
        queryset = MetadataEntry.objects.all()
        if user:
            queryset = queryset.filter(file_analysis__user=user)
        
        category_stats = queryset.values('category').annotate(
            count=Count('id'),
            removed=Count('id', filter=Count('is_removed'))
        )
        
        risk_level_stats = queryset.values('risk_level').annotate(
            count=Count('id')
        )
        
        most_common_keys = queryset.values('key').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        return Response({
            'category_statistics': list(category_stats),
            'risk_level_statistics': list(risk_level_stats),
            'most_common_metadata_keys': list(most_common_keys)
        })