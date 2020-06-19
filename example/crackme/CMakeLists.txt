project(crackme)
cmake_minimum_required(VERSION 3.0)

set(EXECUTABLE_OUTPUT_PATH "../bin")
set(hellf_script_path /home/magnussen/Documents/Cours/ENSIBS/2A/Compilateur_Anti_Reverse/Embuche/v2/class_embuche/cmake_bakery/hellf_scripts)



set(CMAKE_C_FLAGS "-Wall -Wextra -Wshadow -g0 -fstack-protector-all -std=gnu11")

add_executable(${PROJECT_NAME} src/${PROJECT_NAME}.c src/anti_debug.c )



