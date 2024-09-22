from typing import Optional

import datetime
import inspect
import io
import os
import runpy
import textwrap
import unittest

import pstest.constant as constant
from pstest.context import redirect_stdin, redirect_stdout, nullcontext, timeout, memory_limit


class Time(datetime.timedelta):
    pass


class MemorySize:
    def __init__(self,
                 b: int = None,
                 kb: float = None,
                 mb: float = None,
                 gb: float = None) -> None:
        self._size = 0
        self._size += b if b else 0
        self._size += int(kb * 1024**1) if kb else 0
        self._size += int(mb * 1024**2) if mb else 0
        self._size += int(gb * 1024**3) if gb else 0

    @property
    def size(self) -> int:
        return self._size


class PSTestCase(unittest.TestCase):
    problem_url: Optional[str]
    time_limit: Optional[Time] = None
    memory_limit: Optional[MemorySize] = None
    main: str

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        if not hasattr(cls, 'main'):
            cls.main = cls._get_default_main()

    def assertTC(self, module: str,
                 input: Optional[str] = None,
                 output: Optional[str] = None) -> None:
        input = self.refine(input) if input is not None else None
        output = self.refine(output) if output is not None else None

        output_stream = io.StringIO()
        with (redirect_stdin(io.StringIO(input)),
              redirect_stdout(output_stream),
              timeout(self.time_limit.total_seconds()) if self.time_limit else nullcontext(),
              memory_limit(self.memory_limit.size) if self.memory_limit else nullcontext()):
            runpy.run_path(module, run_name="__main__")
        result = self.refine(output_stream.getvalue())

        if output is not None:
            self.assertEqual(result, output)

    def refine(self, s: str) -> str:
        return textwrap.dedent(s).strip()

    @classmethod
    def _get_default_main(cls) -> str:
        if constant.MAIN:
            return constant.MAIN

        test_path = inspect.getfile(cls)
        test_dir, problem_name, file_ext = _parse_test_path(test_path)

        main_prefix = constant.MAIN_PREFIX or ""
        main_suffix = constant.MAIN_SUFFIX or ""
        main_filename = f"{main_prefix}{problem_name}{main_suffix}{file_ext}"
        return os.path.join(test_dir, main_filename)


def _parse_test_path(filepath: str) -> tuple[str, str, str]:
    dir_path = os.path.dirname(filepath)
    filename, file_ext = os.path.splitext(os.path.basename(filepath))
    if constant.TEST_PREFIX or constant.TEST_SUFFIX:
        problem_name = _strip_test_affix(filename)
    else:
        problem_name = _infer_problem_name(filename)
    return dir_path, problem_name, file_ext


def _strip_test_affix(filename: str) -> str:
    if constant.TEST_PREFIX and filename.startswith(constant.TEST_PREFIX):
        filename = filename[len(constant.TEST_PREFIX):]
    if constant.TEST_SUFFIX and filename.endswith(constant.TEST_SUFFIX):
        filename = filename[:-len(constant.TEST_SUFFIX)]
    return filename


def _infer_problem_name(filename: str) -> str:
    if filename.startswith("test_"):
        return filename[len("test_"):]
    elif filename.endswith("_test"):
        return filename[:-len("_test")]
    elif filename.endswith("test"):
        return filename[:-len("test")]
    elif filename.startswith("test"):
        return filename[len("test"):]
    elif "test" in filename:
        return filename.replace("test", "", 1)
