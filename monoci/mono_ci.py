import os
import git
import yaml
import argparse
import sys
import traceback
from monoci.services import DefaultServices


class MonoCI:
    def __init__(self, services):
        self.services = services

    def get_changed_files(self, repo):
        return [item.a_path for item in repo.index.diff('HEAD~1')]

    def get_changed_services(self, changed_files, service_paths):
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

    def run(self, test, upload):
        os.environ['PYTHONUNBUFFERED'] = '1'
        passed = True
        try:
            repo = git.Repo(search_parent_directories=True)
        except:
            print('Command must be run from a git repository')
            return -1
        repo.git.pull('origin', 'master')
        repo_root = repo.git.rev_parse("--show-toplevel")
        os.chdir(repo_root)

        services_yaml = '%s/services.yaml' % repo_root
        data = self.load_services_yaml(services_yaml)
        if 'environment' in data:
            self.set_environment(data['environment'])
        services = data['services']
        service_paths = self.get_service_paths(services)

        print('Looking for changed files in %s' % repo_root.split('/')[-1])
        print('------------------------------------------------------------')
        changed_files = self.get_changed_files(repo)
        if 'services.yaml' in changed_files:
            changed_files.remove('services.yaml')
        for _, service in services.items():
            test_docker_path = os.path.join(service['path'], service['test']['path'])
            if test_docker_path in changed_files:
                changed_files.remove(test_docker_path)
        if len(changed_files) < 1:
            print('No Projects Modified')
            print('SUCCESS')
            return 0
        print('Found modified files...')
        print('------------------------------------------------------------')
        for file in changed_files:
            print('  %s\n' % file)
        print('------------------------------------------------------------')
        changed_services = self.get_changed_services(changed_files, service_paths)
        if len(changed_services) < 1:
            print('No Projects Modified')
            print('SUCCESS')
            return 0
        print('Builiding Services...')
        print('------------------------------------------------------------')
        for service in changed_services:
            print('  %s\n' % service)
        print('------------------------------------------------------------')

        for service in changed_services:
            changed_service = services[service]
            print('Building Service: %s' % service)
            print('------------------------------------------------------------')
            service_artifact = self.services.get_artifact_service(changed_service)
            try:
                image = service_artifact.build_artifact()
            except Exception:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                traceback.print_exception(exc_type, exc_value, exc_traceback,
                              limit=2, file=sys.stdout)
                passed = False
                print('BUILD FAILED')
                continue
            for line in image:
                if 'stream' in line:
                    print(line['stream'])
            success = True
            if test:
                print('------------------------------------------------------------')
                print('Testing Service: %s' % service)
                print('------------------------------------------------------------')
                service_test = self.services.get_test_service(changed_service)
                result = service_test.test_service()
                print(result['output'].decode('utf-8'))
                success = result['success']
            if success:
                if upload:
                    print('------------------------------------------------------------')
                    print('Versioning image')
                    print('------------------------------------------------------------')
                    version = changed_service['build']['version']
                    version = service_artifact.version_artifact(version)
                    print('Successfully applied version %s to artifact\n' % version)
                    data['services'][service]['build']['version'] = version
                    print('------------------------------------------------------------')
                    print('Uploading image')
                    print('------------------------------------------------------------')
                    service_upload = self.services.get_upload_service(changed_service)
                    service_upload.upload_service(version)
            else:
                passed = False
                print('TESTS FAILED')
        if upload:
            self.dump_services_yaml(data, services_yaml)
            repo.git.add("services.yaml")
            repo.index.commit("[MonoCI] Automated version change.")
            repo.git.push('--set-upstream', 'origin', 'master')
        if passed:
            print('SUCCESS')
            return 0
        else:
            print('FAILED')
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