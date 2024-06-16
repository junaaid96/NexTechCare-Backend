from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from .models import Contact
from .serializers import ContactTextSerializer


class ContactTextCreateView(generics.CreateAPIView):
    serializer_class = ContactTextSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'success': 'Message sent successfully.'}, status=status.HTTP_201_CREATED)


class ContactTextListView(generics.ListAPIView):
    queryset = Contact.objects.all()
    serializer_class = ContactTextSerializer
