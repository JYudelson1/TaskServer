from TaskServer import TaskClient

def doubler(x: int) -> int:
    if x == 8:
        raise Exception
    return 2 * x

tc = TaskClient(handler=doubler,
                host="Josephs-MBP-2.home",
                threads=4,
                verbose=True)

tc.start()