from typing import Callable, Optional, TypeVar, Dict, Union, Any, List

import requests

from pprint import pprint

# Create types
GenericTask = TypeVar("GenericTask")
GenericResponse = TypeVar("GenericResponse")
GenericJSONResponse = Dict[str, Union[GenericResponse, GenericTask]]

class TaskClient():
    def __init__(self, 
                handler: Callable[[GenericTask], GenericResponse],
                host: str,
                port: int = 5000,
                threads: int = 1,
                verbose: bool = False) -> None:
        """A class that wraps various distributing processing features
            from the client side.

        Arguments:
            handler -- The function that will be called on the task to process it
            host -- The hostname of the TaskServer's running machine

        Keyword Arguments:
            port -- The port to request to (default: {5000})
            threads -- The number of threads to run processing on (default: {1})
            verbose -- Whether to log various statuses (default: {False})
        """
        self.handler = handler
        self.host = host
        self.port = port
        self.threads = threads
        self.verbose = verbose

        self.endpoint = f'http://{self.host}:{self.port}/'

        self.finished = False

    def _get(self) -> Optional[GenericTask]:
        """Gets a new task from the TaskServer.

        Returns:
            A task, if a task was served.
            None, if no task was served. 
                (This implies the Server is empty)
        """
        server_task = requests.get(self.endpoint + "get_task")
        task = server_task.json()

        if self.verbose:
            pprint(f'Got task: {task}')

        if task["task"] is None:
            self.finished = True
            return None

        return task["task"]

    def _report(self, task: GenericTask, processed: GenericResponse) -> None:
        """Report one response to the TaskServer"""

        response: GenericJSONResponse = {
            "task": task,
            "response": processed
        }

        requests.post(self.endpoint + "report_task", json=response)

    def _target(self) -> None:
        """Continually receives and processes tasks"""
        while True:
            task = self._get()
            if task is None:
                return
            response = self.handler(task)
            self._report(task, response)

    def start(self) -> None:
        """Spins up processing threads"""

        if self.threads == 1:
            self._target()
        else:
            import threading
            threads: List[threading.Thread] = []

            # Spin up threads
            for i in range(self.threads):
                threads.append(threading.Thread(target=self._target))
                threads[i].start()

            # Wait for threads to stop
            for i in range(self.threads):
                threads[i].join()

        print("Finished processing tasks!")


    