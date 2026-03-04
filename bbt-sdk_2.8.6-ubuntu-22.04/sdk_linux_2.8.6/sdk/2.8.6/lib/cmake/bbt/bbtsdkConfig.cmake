get_filename_component(bbtsdk_CMAKE_DIR "${CMAKE_CURRENT_LIST_FILE}" PATH)
include(CMakeFindDependencyMacro)

list(APPEND CMAKE_MODULE_PATH ${bbtsdk_CMAKE_DIR})

if(NOT TARGET bbt::sdk)
    include("${bbtsdk_CMAKE_DIR}/bbtsdkTargets.cmake")
endif()

set(BBTSDK_lIBRARIES bbt::sdk)
