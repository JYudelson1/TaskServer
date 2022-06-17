from TaskServer import TaskServer
from pprint import pprint

tasks = (1,2,3,5,8,13)
server = TaskServer(tasks, cleanup_fn=pprint, verbose=True)
server.run()