# Build the existing workspace C ABI per ABI; no source copying or rewriting.
get_filename_component(CHATCRAFT_ROOT "${CMAKE_CURRENT_LIST_DIR}/../../../.." ABSOLUTE)
find_program(CHATCRAFT_CARGO cargo REQUIRED)
if(ANDROID_ABI STREQUAL "arm64-v8a")
    set(chatcraft_target aarch64-linux-android)
    set(chatcraft_clang aarch64-linux-android)
elseif(ANDROID_ABI STREQUAL "armeabi-v7a")
    set(chatcraft_target armv7-linux-androideabi)
    set(chatcraft_clang armv7a-linux-androideabi)
elseif(ANDROID_ABI STREQUAL "x86")
    set(chatcraft_target i686-linux-android)
    set(chatcraft_clang i686-linux-android)
elseif(ANDROID_ABI STREQUAL "x86_64")
    set(chatcraft_target x86_64-linux-android)
    set(chatcraft_clang x86_64-linux-android)
else()
    message(FATAL_ERROR "Unsupported Chatcraft ABI: ${ANDROID_ABI}")
endif()
get_filename_component(chatcraft_toolchain "${CMAKE_C_COMPILER}" DIRECTORY)
set(chatcraft_linker "${chatcraft_toolchain}/${chatcraft_clang}23-clang")
if(CMAKE_HOST_WIN32)
    string(APPEND chatcraft_linker ".cmd")
endif()
string(TOUPPER "${chatcraft_target}" chatcraft_env_target)
string(REPLACE "-" "_" chatcraft_env_target "${chatcraft_env_target}")
set(chatcraft_cargo_output "${CMAKE_CURRENT_BINARY_DIR}/chatcraft-rust")
set(chatcraft_archive "${chatcraft_cargo_output}/${chatcraft_target}/release/libchatcraft_ffi.a")
# A phony target lets Cargo itself check all workspace/lockfile dependencies.
add_custom_target(chatcraft_rust_build
    COMMAND "${CMAKE_COMMAND}" -E env
        "CARGO_TARGET_${chatcraft_env_target}_LINKER=${chatcraft_linker}"
        "${CHATCRAFT_CARGO}" build --locked --release -p chatcraft-ffi
        --manifest-path "${CHATCRAFT_ROOT}/Cargo.toml"
        --target "${chatcraft_target}" --target-dir "${chatcraft_cargo_output}"
    BYPRODUCTS "${chatcraft_archive}"
    VERBATIM)
add_library(chatcraft_rust STATIC IMPORTED)
set_target_properties(chatcraft_rust PROPERTIES IMPORTED_LOCATION "${chatcraft_archive}")
add_dependencies(chatcraft_rust chatcraft_rust_build)
target_sources(${NATIVE_LIB} PRIVATE ChatcraftBridge.cpp)
target_link_libraries(${NATIVE_LIB} chatcraft_rust dl m)
add_dependencies(${NATIVE_LIB} chatcraft_rust_build)
