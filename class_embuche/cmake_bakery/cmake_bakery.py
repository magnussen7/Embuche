import os
from jinja2 import Environment, FileSystemLoader

class cmake_bakery():
    def __init__(self, project_path, project_name, options, template_name):
        # Set the name of the template to use
        self.__set_template_name(template_name)
        # Create the Jinja environment
        self.__set_template_env()
        # Create path to the final CMake
        self.__set_cmake_path(project_path)
        # Create the options to fill the CMake template
        self.__set_template_dict(project_path, project_name, options)
        # Fill the Cmake with the options
        self.__set_render_template()

    def __set_template_env(self):
        # Create the template environment
        self.__file_loader = FileSystemLoader(os.path.dirname(os.path.realpath(__file__)) + '/templates')
        self.__file_loader_env = Environment(loader=self.__file_loader)
        self.__initial_cmake_template = self.__file_loader_env.get_template(self.get_template_name())

    def get_template_env(self):
        # Return the Jinja template environment
        return {
            'file_loader': self.__file_loader,
            'file_loader_env': self.__file_loader_env,
            'initial_cmake_template': self.__initial_cmake_template
        }

    def get_initial_template(self):
        # Return the template object
        return self.__initial_cmake_template

    def __set_cmake_path(self, cmake_path):
        # Create the path to the CMake file in the project directory
        self.__cmake_path = cmake_path + '/CMakeLists.txt'

    def get_cmake_path(self):
        # Return the path to the CMake (in the project)
        return self.__cmake_path

    def __set_template_dict(self, project_path, project_name, conf):
        # Create dict with the path to;
        # - the main source code
        # - path to the project directory
        # - path to ELF hacks scripts
        # - path to packer scripts
        # - Dictionnary of options to use
        # - Filename to compile as well
        self.__template_values = {
            'binary_path': project_path,
            'project_name': project_name,
            'hellf_script_path': os.path.dirname(os.path.realpath(__file__)) + '/hellf_scripts',
            'packer_path': os.path.dirname(os.path.realpath(__file__)) + '/packer',
            'options': conf['options'],
            'files': conf['files']
        }

    def get_template_dict(self):
        # Return the dictionnary with all the options to use for create the CMake
        return self.__template_values

    def __set_render_template(self):
        # Create the template filled with the options to use for the compilation
        self.__render_template = self.get_initial_template().render(values=self.get_template_dict())

    def get_render_template(self):
        # Return the template filled with the options to use for the compilation
        return self.__render_template

    def __set_template_name(self, template_name):
        # Set the name of the template to use
        self.__template_name = template_name

    def get_template_name(self):
        # Return the name of the template
        return self.__template_name

    def create_cmakelist_file(self):
        # Create the CMake file with the options of Embuche and write it in the project directory
        with open(self.get_cmake_path(), 'w') as target:
            target.write(self.get_render_template())
