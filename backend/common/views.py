from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    """
    Endpoint de salud simple para validar que la API está operativa.
    Responde con un JSON plano y código 200.
    """

    def get(self, request):
        return Response({"status": "ok"})
