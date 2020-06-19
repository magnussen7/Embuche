import sys
import os
import shutil
import yaml
import subprocess
import glob
from .cmake_bakery.cmake_bakery import cmake_bakery

class embuche():
    def __init__(self, config_file):
        # Supported Embuche options
        self.__supported_options = {
            'compilation_options': {
                                    'strip': { 'value': False, 'flag': 's'},
                                    'symbols_hidden': { 'value': False, 'flag': 'fvisibility'},
                                    'optimize': { 'value': False, 'flag': 'O3'},
                                    'unroll_loops': { 'value': False, 'flag': 'funroll-all-loops'},
                                    'static': { 'value': False, 'flag': 'static'},
                                    'custom': { 'value': [], 'flag': ''}
                                    },
            'file_format': {
                'endianness': { 'value': False },
                'remove_section_header': { 'value': False },
                'flip_sections_flags': { 'value': False },
                'hide_entry_point': { 'value': False },
                'mixing_symbols': { 'value': False }
            },
            'packer': {
                'packer': { 'value': False },
                'packer_embuche': { 'value': False } }
            }
        # Set config file with Embuche options (yaml)
        self.__set_conf(config_file)

        # Set path to main code to compile
        self.__set_source_code()
        # Set project dir (Dir with build, bin, src)
        self.__set_project_directory()
        # Set the name of the project (name of the main source file)
        self.__set_project_name()
        # Check if config file is ok
        self.__parse_config()
        # Prepare directories
        self.__prepare_directories()
        # Prepare CMake for compilation
        self.__cmake_bakery_embuche = cmake_bakery(self.get_project_directory(), self.get_project_name(), self.get_conf(), 'CMakeLists_embuche.txt.Jinja')
        self.__cmake_bakery_packer = cmake_bakery(self.get_project_directory() + '/packer', self.get_project_name(), self.get_conf(), 'CMakeLists_packer.txt.Jinja')

    def __set_conf(self, config_file):
        # Try to load yaml in config file, exit otherwise
        try:
            # Read Conf file
            with open(config_file, 'r') as target:
                self.__conf = yaml.safe_load(target)

            if 'source_code' not in self.__conf:
                print('[-] No source_code defined.')
                exit(1)

            # Add missing options to avoid error
            if 'options' in self.__conf:
                self.__set_default_options()
            else:
                self.__conf['options'] = self.__supported_options

            # Create empty list if no external files, avoid error later
            if 'files' not in self.__conf:
                self.__conf['files'] = []
        except Exception as e:
            print("[-] Error in config file: {}".format(config_file))
            exit(1)

    def get_conf(self):
        # Return config (dictionnary)
        return self.__conf

    def __set_source_code(self):
        # Check if main source code exists and store path to it, exit otherwise
        if os.path.exists(self.get_conf()['source_code']):
            self.__source_code = self.get_conf()['source_code']
        else:
            print("{} doesn't exits".format(self.get_conf()['source_code']))
            exit(1)

    def get_source_code(self):
        # Return path to the main source code
        return self.__source_code

    def __set_project_directory(self):
        # Set path to the project directory
        self.__project_directory = os.path.dirname(os.path.abspath(os.path.join(self.get_source_code(), os.pardir)))

    def get_project_directory(self):
        # Return path to the project directory
        return self.__project_directory

    def __set_project_name(self):
        # Parse path to the main source code to store the filename as project name
        self.__project_name = os.path.splitext(os.path.basename(self.get_source_code()))[0]

    def get_project_name(self):
        # Return the name of the project (Name of the main source code file)
        return self.__project_name

    def __set_default_options(self):
        # Set missing options to avoid errors
        # For each kind of options, check if it's in config, add it if not
        for type in self.__supported_options.keys():
            if type not in self.__conf['options'].keys():
                self.__conf['options'][type] = self.__supported_options[type]
            else:
                # Foreach option in kind of options, check if it's in config, add it if not
                for option in self.__supported_options[type].keys():
                    if option not in self.__conf['options'][type].keys():
                        self.__conf['options'][type][option] = self.__supported_options[type][option]

    def __parse_compilation_options(self, compilation_options):
        # Default compilation option of Embuche
        set_options = ['Wall', 'Wextra', 'Wshadow', 'g', 'std']
        # Check if compilation_options is well configured (True or false value)
        for option in compilation_options:
            # If option doesn't exists in Embuche, exit
            if option not in self.__supported_options['compilation_options'].keys():
                print("[-] Unsupported GCC options (-{}) in config.".format(option))
                exit(1)

            # If options is not custom, check if value is True or False, if not set as False
            if option != 'custom':
                if compilation_options[option]['value'] not in [True, False]:
                    print("[-] Invalid value for compilation_options {}, must be True or False.".format(option))
                    compilation_options[option]['value'] = False

                # Add flag to set_options list, to check if no duplicate GCC flag later
                if compilation_options[option]['value'] is True:
                    set_options.append(self.__supported_options['compilation_options'][option]['flag'])

        # Check if there's no duplicate GCC flags with the custom flags
        if 'custom' in compilation_options:
            for flag in compilation_options['custom']['value']:
                if flag in set_options:
                    print('[-] GCC option (-{}) is already set in Embuche, can\'t be added again.'.format(flag))
                    exit(1)

    def __parse_file_format(self, file_format_options, compilation_options=None):
        # File format options that we'll be use, the list will be used to check if there's no mistake in config
        set_options = []
        # Check if file_format_options is well configured (True or false value)
        for option in file_format_options:
            # If option doesn't exists in Embuche, exit
            if option not in self.__supported_options['file_format'].keys():
                print("[-] Unsupported file_format options: {}".format(option))
                exit(1)
            # If value is not True or False, set it to False
            if file_format_options[option]['value'] not in [True, False]:
                print("[-] Invalid value for file_format {}, must be True or False.".format(option))
                file_format_options[option]['value'] = False

            # If true, add options to set_options to check later if there's error in config
            if file_format_options[option]['value'] is True:
                set_options.append(option)

        # Can't remove section header and mix symbol, print message and exit
        if ('remove_section_header' not in set_options) and (('flip_sections_flags' in set_options) or ('hide_entry_point' in set_options)):
            print('[-] The section header must be removed to use flip_sections_flags or hide_entry_point. Please set the remove_section_header to true.')
            exit(1)

        # Can't remove section header and mix symbol, print message and exit
        if ('remove_section_header' in set_options) and ('mixing_symbols' in set_options):
            print('[-] Can\'t remove section header and mix symbol table, one of this options must be set to false.')
            exit(1)

        # Can't mix symbols if there're hidden, print message and exit
        if compilation_options is not None:
            if ('mixing_symbols' in set_options) and (compilation_options['symbols_hidden']['value'] is True or compilation_options['static']['value'] is True):
                print('[-] .dynsym must be present to mix symbols table, either set mixing_symbols to false or symbols_hidden and static to false.')
                exit(1)

    def __parse_packer(self, packer):
        # Check if packer is well configured (True or false value)
        for option in packer:
            # If option doesn't exists in Embuche, exit
            if option not in self.__supported_options['packer'].keys():
                print("[-] Unsupported packer options: {}".format(option))
                exit(1)
            # If value is not True or False, set it to False
            if packer[option]['value'] not in [True, False]:
                print("[-] Invalid value for packer {}, must be True or False.".format(option))
                packer[option]['value'] = False

        # Exit if packer is not used but packer_embuche is set
        if packer['packer']['value'] is False and packer['packer_embuche']['value'] is True:
            print('[-] Can\'t use file format hacks on the packer if it\'s not enabled.')
            exit(1)

    def __parse_config(self):
        # Check if config is valid
        conf = self.get_conf()

        if 'files' in conf:
            # Check if each file in the 'files' options of the config exists
            for file in conf['files']:
                # Create path to the c_toolbox dir to check if file is in it
                c_tool_file = os.path.dirname(os.path.realpath(__file__)) + '/c_toolbox/' + file
                # Create path to the project dir to check if file is in it
                project_file = self.get_project_directory() + '/' + file

                # Check if file is in c_toolbox dir or project dir, exit otherwise
                if (os.path.exists(c_tool_file) == False) and (os.path.exists(project_file) == False):
                    print("{} doesn't exits".format(file))
                    exit(1)

        if 'options' in conf:
            if 'compilation_options' in conf['options']:
                # Check if compilation_options is well configured (True or false value and no duplicate options)
                self.__parse_compilation_options(conf['options']['compilation_options'])
            else:
                conf['options']['compilation_options'] = self.__supported_options['compilation_options']

            if 'file_format' in conf['options']:
                # Check if file_format is well configured (True or false value and no exclusive options)
                if 'compilation_options' in conf['options']:
                    self.__parse_file_format(conf['options']['file_format'], conf['options']['compilation_options'])
                else:
                    self.__parse_file_format(conf['options']['file_format'])

            if 'packer' in conf['options']:
                # Check if packer is well configured (True or false value)
                self.__parse_packer(conf['options']['packer'])
        else:
            print("[-] Error, no options in yaml, please use the provided template.")
            exit(1)

    def prepare_cmake(self):
        # Create CMake object
        self.__cmake_bakery_embuche.create_cmakelist_file()
        self.__cmake_bakery_packer.create_cmakelist_file()

    def __prepare_directories(self):
        # Create build directory if it doesn't exists in project path
        if not os.path.exists(self.get_project_directory() + '/build'):
            os.makedirs(self.get_project_directory() + '/build')
        else:
            # Clean build directory if it already exists
            for files in os.listdir(self.get_project_directory() + '/build'):
                # If file in build dir is a directory use shutil.rmtree
                if os.path.isdir(self.get_project_directory() + '/build/' + files):
                    shutil.rmtree(self.get_project_directory() + '/build/' + files)
                else:
                    # If file in build dir is file use os.remove
                    os.remove(self.get_project_directory() + '/build/' + files)

        # Create output dir (bin) in project directory if it doesn't exists
        if not os.path.exists(self.get_project_directory() + '/bin'):
            os.makedirs(self.get_project_directory() + '/bin')
        else:
            # If bin directory exists, remove all files in it
            for files in os.listdir(self.get_project_directory() + '/bin'):
                # Foreach file in directory, remove it, if it's dir use shutil.rmtree
                if os.path.isdir(self.get_project_directory() + '/bin/' + files):
                    shutil.rmtree(self.get_project_directory() + '/bin/' + files)
                else:
                    # If it's a file, use os.remove
                    os.remove(self.get_project_directory() + '/bin/' + files)

        # Copy files in c_toolbox to project directory
        for file in glob.glob(os.path.join(os.path.dirname(os.path.realpath(__file__)) + '/c_toolbox/', '*.*')):
            # If file in c_toolbox is not already in src dir, copy it
            if not os.path.exists(self.get_project_directory() + '/src/' + file):
                shutil.copy(file, self.get_project_directory() + '/src/')

        # If packer directory already exists, remove it
        if os.path.exists(self.get_project_directory() + '/packer'):
            shutil.rmtree(self.get_project_directory() + '/packer')

        # Copy the complete packer directory and subdirectories
        shutil.copytree(os.path.join(os.path.dirname(os.path.realpath(__file__)) + '/cmake_bakery/packer'), self.get_project_directory() + '/packer')

    def run(self):
        try:
            # Go to the build directory
            os.chdir(self.get_project_directory() + '/build')
            # Execute CMake
            subprocess.run(['cmake', '..'])
            # Execute make
            subprocess.run(['make'])

            # If packer is wanted
            if self.get_conf()['options']['packer']['packer']['value'] is True:
                # Go to packer directory
                os.chdir(self.get_project_directory() + '/packer')
                # Execute CMake
                subprocess.run(['cmake', '.'])
                # Execute make
                subprocess.run(['make'])
                # Delete packer directory in the program directory
                shutil.rmtree(self.get_project_directory() + '/packer')
                # Rename replace the previously build program by the packed one
                shutil.copy(self.get_project_directory() + '/bin/' + self.get_project_name() + '_packed', self.get_project_directory() + '/bin/' + self.get_project_name())
                # Delete the duplicated packed one
                os.remove(self.get_project_directory() + '/bin/' + self.get_project_name() + '_packed')
        except Exception as e:
            print('[-] Error while executing cmake/make.')
            exit(1)
