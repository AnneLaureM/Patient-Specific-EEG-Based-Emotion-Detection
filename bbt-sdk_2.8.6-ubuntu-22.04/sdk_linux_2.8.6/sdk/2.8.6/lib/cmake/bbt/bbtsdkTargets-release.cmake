#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "bbt::sdk" for configuration "Release"
set_property(TARGET bbt::sdk APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(bbt::sdk PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libsdk-2.8.6.so.2.8.6"
  IMPORTED_SONAME_RELEASE "libsdk-2.8.6.so.2"
  )

list(APPEND _cmake_import_check_targets bbt::sdk )
list(APPEND _cmake_import_check_files_for_bbt::sdk "${_IMPORT_PREFIX}/lib/libsdk-2.8.6.so.2.8.6" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
