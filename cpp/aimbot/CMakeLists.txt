cmake_minimum_required(VERSION 3.10)
project(lunar_aimbot_v17)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(lunar_aimbot_v17 SHARED lunar_aimbot.cpp)

target_include_directories(lunar_aimbot_v17 PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})

target_link_libraries(lunar_aimbot_v17 PRIVATE user32 winmm setupapi hid)

set_target_properties(lunar_aimbot_v17 PROPERTIES
    WINDOWS_EXPORT_ALL_SYMBOLS OFF
    RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_BINARY_DIR}/Release"
)
