cmake_minimum_required(VERSION 3.10)
project(LunarMouse)

add_library(lunar_mouse SHARED lunar_mouse.cpp)

# Ensure exports work correctly
set_target_properties(lunar_mouse PROPERTIES WINDOWS_EXPORT_ALL_SYMBOLS ON)
