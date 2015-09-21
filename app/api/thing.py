from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet
from app.models import Thing


class ThingSerializer(ModelSerializer):
    class Meta:
        model = Thing
        fields = ('id', 'name', )


class ThingViewSet(ModelViewSet):
    serializer_class = ThingSerializer
    queryset = Thing.objects.all()

    class Meta:
        model = Thing
