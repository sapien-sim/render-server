import os
import pathlib
import sapien

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext

current_dir = pathlib.Path(__file__).absolute().parent
sapien_dir = pathlib.Path(sapien.__file__).absolute().parent
sapien_include_dir = sapien_dir / "include"
assert sapien_include_dir.exists(), "failed to locate SAPIEN include"
sapien_library_dir = sapien_dir.parent / "sapien.libs"
assert sapien_library_dir.exists(), "failed to locate SAPIEN library"


class CMakeExtension(Extension):
    def __init__(self, name):
        super().__init__(name, sources=[])


abi_version = sapien.pysapien.abi_version()
assert 1000 <= abi_version <= 9999


class CMakeBuild(build_ext):
    def run(self):
        for ext in self.extensions:
            self.build_cmake(ext)

    def build_cmake(self, ext):
        # these dirs will be created in build_py, so if you don't have
        # any python sources to bundle, the dirs will be missing
        build_temp = pathlib.Path(self.build_temp)
        build_temp.mkdir(parents=True, exist_ok=True)
        extdir = pathlib.Path(self.get_ext_fullpath(ext.name)).absolute().parent
        extdir.mkdir(parents=True, exist_ok=True)

        cxx_flags = (
            f"-DCMAKE_CXX_FLAGS=-fabi-version={abi_version - 1000}"
            f" -D_GLIBCXX_USE_CXX11_ABI={int(sapien.pysapien.compiled_with_cxx11_abi())}"
        )
        if sapien.pysapien.pybind11_use_smart_holder():
            cxx_flags += " -DPYBIND11_USE_SMART_HOLDER_AS_DEFAULT"

        # example of cmake args
        # config = "Debug" if self.debug else "Release"
        config = "Debug"
        cmake_args = [
            "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
            f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={extdir}",
            f"-DCMAKE_BUILD_TYPE={config}",
            f"-DSAPIEN_INCLUDE_DIR={sapien_include_dir}",
            f"-DSAPIEN_LIBRARY_DIR={sapien_library_dir}",
            cxx_flags,
        ]

        # example of build args
        build_args = [
            "--config",
            config,
            "--target",
            "pysapien_render_server",
            "--",
            "-j4",
        ]

        os.chdir(str(build_temp))
        self.spawn(["cmake", str(current_dir)] + cmake_args)
        if not self.dry_run:
            self.spawn(["cmake", "--build", "."] + build_args)
        os.chdir(str(current_dir))


setup(
    name="sapien_render_server",
    version="0.1",
    python_requires=">=3.7",
    packages=["sapien_render_server"],
    ext_modules=[CMakeExtension("sapien_render_server")],
    cmdclass={"build_ext": CMakeBuild},
    install_requires=["sapien"],
)
