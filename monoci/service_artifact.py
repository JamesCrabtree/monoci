import os
import docker
from abc import ABC, abstractmethod

class Artifact(ABC):
    @abstractmethod
    def build_artifact(self):
        pass

    @abstractmethod
    def version_artifact(self, version):
        pass


class DockerImage(Artifact):
    def __init__(self, image_name, dockerfile_path):
        self.client = docker.from_env()
        self.image_name = image_name
        self.dockerfile_path = dockerfile_path
        self.image = None

    def build_artifact(self):
        image_name = self.image_name + ':latest'
        path = os.path.dirname(self.dockerfile_path)
        filename = self.dockerfile_path.split('/')[-1]
        image = self.client.images.build(path=path, dockerfile=filename, tag=image_name)
        self.image = image[0]
        return image[1]

    def run_image(self):
        return self.client.containers.run(image=self.image_name, detach=True)

    def version_artifact(self, version):
        nums = version.split('.')
        nums[2] = str(int(nums[2]) + 1)
        version = '.'.join(nums)

        image_name = self.image_name + ':' + version
        self.image.tag(image_name)
        return version