from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FileUploadParser

from app.models import DataStore
from django.db import IntegrityError
from django.shortcuts import get_object_or_404

from threading import Thread
from app.worker import Task

global task

STATE_RESPONSES = {
    0: 'Ready to Start!',
    1: 'Uploading...',
    2: 'Paused!',
    3: 'Stopped!'
}


class FileUploadView(APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (FileUploadParser,)

    def put(self, request, filename, format=None):
        file_obj = request.FILES['file']
        dataStore = DataStore(owner=request.user)
        try:
            dataStore.csv = file_obj
            dataStore.save()
        except IntegrityError as e:
            return Response({'error': 'File already exists!'}, status=400)
        
        
        return Response({'message': f'{file_obj.name} successfully uploaded!', 'file_id': f'{dataStore.id}'}, status=201)


class StartUploadTask(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, file_id):
        f = get_object_or_404(DataStore, id=file_id, owner=request.user)
        
        global task
        task = Task(request.user, f.id)

        thread = Thread(task.csv_to_db())
        thread.start()

        return Response({'message': STATE_RESPONSES[task.get_state()]}, status=200)


class UploadTaskState(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, file_id):
        get_object_or_404(DataStore, id=file_id, owner=request.user)
        
        global task

        return Response({'message': STATE_RESPONSES[task.get_state()]}, status=200)


class PauseUploadTask(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, file_id):
        get_object_or_404(DataStore, id=file_id, owner=request.user)
        
        global task
        task.set_state('PAUSED')

        return Response({'message': STATE_RESPONSES[task.get_state()]}, status=200)


class ResumeUploadTask(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, file_id):
        get_object_or_404(DataStore, id=file_id, owner=request.user)
        
        global task
        task.resume()
        
        return Response({'message': STATE_RESPONSES[task.get_state()]}, status=200)


class StopUploadTask(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, file_id):
        get_object_or_404(DataStore, id=file_id, owner=request.user)
        
        global task
        task.stop()
        
        return Response({'message': STATE_RESPONSES[task.get_state()]}, status=200)
