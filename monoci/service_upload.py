import os
import subprocess
from abc import ABC, abstractmethod


class UploadService(ABC):
    def __init__(self, service):
        self.service = service

    @abstractmethod
    def upload_service(self):
        pass


class GoogleContainerRegistry(UploadService):
    def __init__(self, service):
        super().__init__(service)

    def upload_service(self, version):
        image_name = self.service['build']['image name']

        os.environ['IMAGE_NAME'] = image_name
        os.environ['VERSION'] = version

        path = os.path.dirname(os.path.abspath(__file__))
        script = os.path.join(path, 'scripts/gcloud-upload.sh')
        subprocess.run(['/bin/bash', script])