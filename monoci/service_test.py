import os
import yaml
import docker
from abc import ABC, abstractmethod
from monoci.service_artifact import DockerImage

class TestService(ABC):
    def __init__(self, service):
        self.service = service

    @abstractmethod
    def test_service(self):
        pass


class DockerTestService(TestService):
    def __init__(self, service, image_name, dockerfile_path):
        super().__init__(service)
        self.image_name = image_name
        self.dockerfile_path = dockerfile_path
        self.test_image = DockerImage(image_name, dockerfile_path)

    def create_dockerfile_text(self):
        image_name = self.service['build']['image name']
        test_command = self.service['test']['command']
        dockerfile_text = ('FROM {service_image}\n'
                           '{additional_content}\n'
                           'CMD {test_command}\n')       
        commands = list('\"%s\"' % command for command in test_command.split(" "))
        test_command = '[' + ', '.join(commands) + ']'
        additional_content = self.get_additional_content()
        return dockerfile_text.format(service_image=image_name, additional_content=additional_content,
                                      test_command=test_command)

    def get_additional_content(self):
        return ''

    def test_service(self):
        dockerfile_text = self.create_dockerfile_text()
        self.build_test_image(dockerfile_text)
        container = self.test_image.run_image()
        result = container.wait()
        output = container.logs()
        status = result["StatusCode"]
        container.remove()
        return {"output": output, "success": status == 0}

    def build_test_image(self, dockerfile_text):
        with open(self.dockerfile_path, 'w+') as f:
            f.write(dockerfile_text)
        return self.test_image.build_artifact()


class NpmTestService(DockerTestService):
    def __init__(self, service, image_name, dockerfile_path):
        super().__init__(service, image_name, dockerfile_path)

    def get_additional_content(self):
        return ('ENV NODE_ENV dev\n'
                'RUN npm update && \\\n'
                '    npm install -g mocha\n')


class PythonTestService(DockerTestService):
    def __init__(self, service, image_name, dockerfile_path):
        super().__init__(service, image_name, dockerfile_path)
    
    def get_additional_content(self):
        return ''