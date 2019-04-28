import os
from monoci.service_artifact import DockerImage
from monoci.service_test import PythonTestService, NpmTestService
from monoci.service_upload import GoogleContainerRegistry
from abc import ABC, abstractmethod

class Services(ABC):
    @abstractmethod
    def get_artifact_service(self):
        pass
    
    @abstractmethod
    def get_test_service(self):
        pass

    @abstractmethod
    def get_upload_service(self):
        pass


class DefaultServices(Services):
    def get_build_settings(self, service):
        return service['build']
    
    def get_test_settings(self, service):
        return service['test']
    
    def get_image_name(self, service):
        return service['image name']

    def get_path(self, root, service):
        return os.path.join(root, service['path'])

    def get_artifact_service(self, service):
        artifact_type = service['artifact type']
        if artifact_type == 'docker':
            build_settings = self.get_build_settings(service)
            image_name = self.get_image_name(build_settings)
            service_path = os.path.abspath(service['path'])
            dockerfile_path = self.get_path(service_path, build_settings)
            return DockerImage(image_name, dockerfile_path)
        return None

    def get_test_service(self, service):
        service_type = service['language']
        if service_type == 'python':
            test_settings = self.get_test_settings(service)
            image_name = self.get_image_name(test_settings)
            service_path = os.path.abspath(service['path'])
            dockerfile_path = self.get_path(service_path, test_settings)
            return PythonTestService(service, image_name, dockerfile_path)
        if service_type == 'nodejs':
            test_settings = self.get_test_settings(service)
            image_name = self.get_image_name(test_settings)
            service_path = os.path.abspath(service['path'])
            dockerfile_path = self.get_path(service_path, test_settings)
            return NpmTestService(service, image_name, dockerfile_path)
        return None

    def get_upload_service(self, service):
        upload_type = service['upload type']
        if upload_type == 'gcr':
            return GoogleContainerRegistry(service)
