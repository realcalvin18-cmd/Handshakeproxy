cmake_minimum_required(VERSION 3.10)
project(HandshakeProxy VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -Wall -Wextra")

# Find required packages
find_package(CURL REQUIRED)
find_package(OpenSSL REQUIRED)

# nlohmann/json header-only library
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

# Proxy Engine Library
add_library(handshake_proxy_lib SHARED
    cpp/proxy_engine.cpp
)

target_link_libraries(handshake_proxy_lib
    PRIVATE
        CURL::libcurl
        OpenSSL::SSL
        OpenSSL::Crypto
)

# Set output directory
set_target_properties(handshake_proxy_lib PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib
)

# Python binding executable
add_executable(proxy_engine_wrapper
    cpp/proxy_engine_wrapper.c
)

target_link_libraries(proxy_engine_wrapper
    PRIVATE
        handshake_proxy_lib
)

# Installation
install(TARGETS handshake_proxy_lib
    LIBRARY DESTINATION lib
    RUNTIME DESTINATION bin
)

install(TARGETS proxy_engine_wrapper
    RUNTIME DESTINATION bin
)
