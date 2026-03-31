cmake_minimum_required(VERSION 3.10)
project(TestProject)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Source files
set(SOURCES
    base.cpp
    derived.cpp
    function_pointers.cpp
    operators.cpp
    std_function.cpp
    macros.cpp
    static_file1.cpp
    static_file2.cpp
    templates.cpp
    edge_cases.cpp
    main.cpp
)

# Create executable
add_executable(test_project ${SOURCES})

# Install target (optional)
install(TARGETS test_project DESTINATION bin)