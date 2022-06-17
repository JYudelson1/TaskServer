from optparse import Option
from typing import Any, Callable, Dict, Iterable, Optional, TypeVar

from flask import Flask, request
from waitress import serve
import socket
import atexit

from pprint import pprint

# Create types
GenericTask = TypeVar("GenericTask")
GenericServe = Dict[str, Optional[GenericTask]]
GenericJSONResponse = Dict[str, Any]
CleanupFunction = Callable[[Dict[GenericTask, Any]], None]

class TaskServer():
    def __init__(self, 
                tasks: Iterable[GenericTask],
                response_handler : Callable[[GenericTask], None] = print,
                cleanup_fn: Optional[CleanupFunction] = None,
                store_responses: bool = False,
                verbose: bool = False) -> None:
        """
        Arguments:
            tasks -- A list of tasks that will be served to clients
                        on the network.
                        (NOTE: Duplicate tasks will be processed twice, 
                               but stored only once in internal dicts)

        Keyword Arguments:
            response_handler -- A function to be called on every incoming response.
                                    By default, prints response (default: {print})
            cleanup_fn -- A function called when the app is closed by Ctrl+C
                            It will get as input a mapping of every task to
                            every response. NOTE: If this is None, and
                            store_responses is False, this mapping
                            will not be stored, and each response will be 
                            processed and then discarded (default: {None})
            verbose -- Whether to store all client responses (default: {False})
            verbose -- Whether to log various statuses (default: {False})

        """
        self.tasks = (t for t in tasks)
        self.response_handler = response_handler
        self.cleanup_fn = cleanup_fn
        self.store_responses = store_responses
        self.verbose = verbose

        self.responses: Dict[GenericTask, Any] = {}
        self.was_processed = { t: False for t in tasks }

        app = Flask(__name__)
        self.app = app

        @app.route("/get_task")
        def get_task() -> GenericServe:
            try:
                task : Optional[GenericTask] = next(self.tasks)
            except StopIteration:
                task = None

            if self.verbose:
                print(f'Serving {task} to {request.remote_addr}')

            return { "task": task }

        @app.route("/report_task", methods=["POST"])
        def report_task() -> str:
            response: Optional[GenericJSONResponse] = request.json
            if self.verbose:
                print(f'Incoming report from {request.remote_addr}')
            if not response:
                return ""

            # Assert valid task is being reported
            assert self.was_processed.get(response["task"]) is not None

            # If the TaskServe uses a cleanup fn, save task/report pair
            if self.cleanup_fn or self.store_responses:
                self.responses[response["task"]] = response["response"]

            # Mark down which tasks were completed
            self.was_processed[response["task"]] = True

            if self.verbose:
                pprint(response)
                # If response handler is print, and verbose=True,
                # don't bother calling the response handler
                if self.response_handler == print:
                    return ""

            self.response_handler(response["response"])
            return ""

    def _cleanup(self) -> None:
        """Calls cleanup function"""
        if self.cleanup_fn:
            self.cleanup_fn(self.responses)

        print("Unprocessed tasks:")
        pprint([k for k,v in self.was_processed.items() if not v])

    def run(self,
            host: str = "0.0.0.0",
            port: int = 5000) -> None:
        """Start the running app

        Keyword Arguments:
            host -- hostname to pass to waitress.serve (default: {"0.0.0.0"})
            port -- port     to pass to waitress.serve (default: {5000})
        """
    
        # registers internal cleanup fn
        atexit.register(self._cleanup)

        # Print IP
        host_name = socket.gethostname()
        host_ip = socket.gethostbyname(host_name)
        print(f'Spinning up server (host={host_name})')

        #NOTE: threads=1 bc app.tasks is not thread-safe
        serve(self.app, host=host, port=port, threads=1)

        
