import os
import git
import yaml
import argparse
import sys
import traceback
import subprocess
from monoci.services import DefaultServices


class MonoCI:
    def __init__(self, services):
        self.services = services

    def get_changed_files(self, repo):
        if 'master-green' in repo.tags:
            return [item.a_path for item in repo.head.commit.diff('master-green')]
        return None

    def get_changed_services(self, changed_files, service_paths):
        if not changed_files:
            return [name for name in service_paths]

        services = []
        for filename in changed_files:
            for name, path in service_paths.items():
                if path in filename and name not in services:
                    services.append(name)
        return services

    def load_services_yaml(self, services_yaml):
        with open(services_yaml) as f:
            return yaml.load(f)

    def dump_services_yaml(self, data, services_yaml):
        with open(services_yaml, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def get_service_paths(self, services):
        return {name: service['path'] for name, service in services.items()}

    def set_environment(self, environment):
        for key, val in environment:
            os.environ[key] = val

    def log(self, output):
        print(output, flush=True)

    def run(self, test, upload):
        passed = True
        try:
            repo = git.Repo(search_parent_directories=True)
        except:
            self.log('Command must be run from a git repository')
            return -1

        repo_root = repo.git.rev_parse("--show-toplevel")
        os.chdir(repo_root)

        services_yaml = '%s/services.yaml' % repo_root
        data = self.load_services_yaml(services_yaml)
        if 'environment' in data:
            self.set_environment(data['environment'])
        services = data['services']
        service_paths = self.get_service_paths(services)

        self.log('Looking for changed files in %s' % repo_root.split('/')[-1])
        self.log('------------------------------------------------------------')
        changed_files = self.get_changed_files(repo)
        if changed_files:
            if 'services.yaml' in changed_files:
                changed_files.remove('services.yaml')
            for _, service in services.items():
                test_docker_path = os.path.join(service['path'], service['test']['path'])
                if test_docker_path in changed_files:
                    changed_files.remove(test_docker_path)
            if len(changed_files) < 1:
                self.log('No Projects Modified')
                self.log('SUCCESS')
                return 0
            self.log('Found modified files...')
            self.log('------------------------------------------------------------')
            for file in changed_files:
                self.log('  %s\n' % file)
            self.log('------------------------------------------------------------')

        changed_services = self.get_changed_services(changed_files, service_paths)
        if len(changed_services) < 1:
            self.log('No Projects Modified')
            self.log('SUCCESS')
            return 0
        self.log('Builiding Services...')
        self.log('------------------------------------------------------------')
        for service in changed_services:
            self.log('  %s\n' % service)
        self.log('------------------------------------------------------------')

        for service in changed_services:
            changed_service = services[service]
            self.log('Building Service: %s' % service)
            self.log('------------------------------------------------------------')
            service_artifact = self.services.get_artifact_service(changed_service)
            try:
                image = service_artifact.build_artifact()
            except Exception:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                traceback.print_exception(exc_type, exc_value, exc_traceback,
                              limit=2, file=sys.stdout)
                passed = False
                self.log('BUILD FAILED')
                continue
            for line in image:
                if 'stream' in line:
                    self.log(line['stream'])
            if test:
                self.log('------------------------------------------------------------')
                self.log('Testing Service: %s' % service)
                self.log('------------------------------------------------------------')
                service_test = self.services.get_test_service(changed_service)
                result = service_test.test_service()
                self.log(result['output'].decode('utf-8'))

        if upload and passed:
            for service in changed_services:
                changed_service = services[service]
                self.log('------------------------------------------------------------')
                self.log('Versioning image: %s' % service)
                self.log('------------------------------------------------------------')
                version = changed_service['build']['version']
                version = service_artifact.version_artifact(version)
                self.log('Successfully applied version %s to artifact\n' % version)
                data['services'][service]['build']['version'] = version
                self.log('------------------------------------------------------------')
                self.log('Uploading image: %s' % service)
                self.log('------------------------------------------------------------')
                service_upload = self.services.get_upload_service(changed_service)
                service_upload.upload_service(version)

            self.dump_services_yaml(data, services_yaml)
            repo.git.add("-A")
            repo.index.commit("[MonoCI] Automated version change.")
            repo.git.push('--set-upstream', 'origin', 'master')
            repo.create_tag('master-green')
            repo.git.push('--tags')

        if passed:
            self.log('SUCCESS')
            return 0
        else:
            self.log('FAILED')
            return -1

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action='store_true', help="Run project tests")
    parser.add_argument("--upload", action='store_true', help="Upload project artifact to repository")
    args = parser.parse_args()

    services = DefaultServices()
    monoci = MonoCI(services)
    ret_code = monoci.run(args.test, args.upload)
    exit(ret_code)