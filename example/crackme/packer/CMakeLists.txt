cmake_minimum_required(VERSION 3.0)
project(unloaded C)

find_library(CRYPTO_LIB libcrypto.so REQUIRED)

set(hellf_script_path /home/magnussen/Documents/Cours/ENSIBS/2A/Compilateur_Anti_Reverse/Embuche/v2/class_embuche/cmake_bakery/hellf_scripts)

set(HELLF scripts/packer.py)

execute_process(COMMAND python3.8 ${CMAKE_SOURCE_DIR}/${HELLF} ../bin/crackme OUTPUT_VARIABLE TO_BE_PACKED_SIZE)

set(CMAKE_C_STANDARD 99)
set(CMAKE_C_FLAGS "-Wall  -pedantic -std=c99 -no-pie -DBIN_SIZE=${TO_BE_PACKED_SIZE} -g")
set(CMAKE_C_FLAGS_DEBUG "-DDEBUG")

find_package(OpenSSL REQUIRED)

if ( OpenSSL_FOUND )
    include_directories(${OPENSSL_INCLUDE_DIRS})
    link_directories(${OPENSSL_LIBRARIES})
    message(STATUS "Using OpenSSL ${OPENSSL_VERSION}")
endif()

include_directories(includes)

add_executable(unloaded
        includes/consts.h
        includes/cryptage.h
        includes/utils.h
        src/cryptage.c
        src/utils.c
        src/v0_packer.c
        )


add_custom_target(addLDS
        COMMAND sed -i -e 's,-o,${CMAKE_CURRENT_SOURCE_DIR}/src/layout.lds -o,g' ./CMakeFiles/unloaded.dir/link.txt)

add_dependencies(unloaded addLDS)

target_link_libraries(unloaded ${OPENSSL_LIBRARIES})

add_custom_target(crackme_packed ALL
        COMMAND python3.8 ${CMAKE_SOURCE_DIR}/${HELLF} ${CMAKE_BINARY_DIR}/unloaded ../bin/crackme ${CMAKE_SOURCE_DIR}/../bin/crackme_packed
        COMMAND chmod +x ${CMAKE_SOURCE_DIR}/../bin/crackme_packed )

add_dependencies(crackme_packed unloaded)

