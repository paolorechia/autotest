from typing import Optional, Callable, Any, Dict
from dataclasses import dataclass
import logging
from multiprocessing import Process, TimeoutError, Queue
import random

TIMEOUT = 0.2

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@dataclass(frozen=True)
class AutoTestResult:
    passed: bool
    error: Optional[str] = None


@dataclass(frozen=True)
class ExecutionResult:
    finished: bool
    result: Any


def unsafe_exec(code: str, q: Queue):
    locals_: Dict[str, Any] = {}
    exec(code, {}, locals_)
    q.put(locals_["result"])
    return


def execute_function(
    code: str, func_name: str, python_func: Callable, **kwargs
) -> ExecutionResult:
    logger.info("Executing func: %s, kwargs=%s", func_name, kwargs)
    func_call_str = f"result = {func_name}("
    for key, item in kwargs.items():
        func_call_str += f"{key}={item}, "
    func_call_str = func_call_str[:-2]
    func_call_str += ")"
    logger.info("Built function call: %s", func_call_str)

    code_to_exec = code + "\n" + func_call_str

    q: Queue = Queue()

    p = Process(
        target=unsafe_exec,
        args=(
            code_to_exec,
            q,
        ),
    )
    p.start()

    result = None
    try:
        logger.info("Reading value from queue")
        result = q.get(timeout=TIMEOUT)
        logger.info("Got back: %s", result)
    except Exception as excp:
        logger.error(excp)

    p.join(timeout=TIMEOUT)
    if p.is_alive():
        p.kill()
        return ExecutionResult(finished=False, result=result)
    return ExecutionResult(finished=True, result=result)


def autotest(code: str):
    logger.info("Auto testing code...")
    try:
        pre_exec_keys = set(locals().keys())
        logger.info("EXEC")
        exec(code)
        post_exec_locals = locals()
        post_exec_keys = set(post_exec_locals.keys())
        new_locals = post_exec_keys - pre_exec_keys
        logger.info("Pre exec keys: %s", pre_exec_keys)
        logger.info("Post exec keys: %s", post_exec_keys)
        new_locals.remove("pre_exec_keys")
        logger.info("New locals: %s", new_locals)
        func_name = list(new_locals)[0]
        func = post_exec_locals[func_name]
        logger.info(func)
        logger.info(type(func))
        logger.info(dir(func))
        logger.info(func.__annotations__)

        types = func.__annotations__
        return_type = type(None)

        if "return" in types:
            return_type = types.pop("return")  # type: ignore
        kwargs = {}
        for key, item in types.items():
            logger.info("%s %s", item, int)
            if item == int:
                logger.info("Found int")
                val = random.randint(-255, 255)
                kwargs[key] = val
        execution_result = execute_function(code, func_name, func, **kwargs)
        logger.info(
            "Execution result: %s (type: %s)",
            execution_result,
            type(execution_result.result),
        )
        if not execution_result.finished:
            raise TimeoutError
        if return_type != type(execution_result.result):  # noqa
            raise TypeError
    except (SyntaxError, TimeoutError, TypeError) as excp:
        logger.info(excp)
        return AutoTestResult(False, str(excp))
    return AutoTestResult(True)
