from datetime import datetime
from dotenv import load_dotenv
from tqdm import trange
import os
import sys
import time
import threading
import docker
import json

load_dotenv()
DOCKER_HOST_API= os.getenv('DOCKER HOST_API')
DURATION = os.getenv('DURATION_IN_SEC')
LOGFILE_PREFIX = os.getenv('LOGFILE_PREFIX')
number_of_measurements = 0

# variables for concurrent use
isAlive = 0

# getCPUusage
threads={}
measurements = {}
numberOfContainer = 0
isCPUAlive = 0
all_m =[]

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def cpu_perc(d, id ) :
    """_summary_

    Args:
        d (_type_): _description_
        number (_type_): _description_

    Returns:
        _type_: _description_
    """
    if("system_cpu_usage" in d["precpu_stats"]) :
        cpuDelta = float (d["cpu_stats"]["cpu_usage"]["total_usage"]) - float (d["precpu_stats"]["cpu_usage"]["total_usage"])
        systemDelta= float (d["cpu_stats"]["system_cpu_usage"]) - float(d["precpu_stats"]["system_cpu_usage" ])
        output = cpuDelta / systemDelta * 100
        global measurements
        measurements[id]["totalCPU"] = measurements[id]["totalCPU"]+ output
        measurements[id]["counterCPU"] = measurements[id]["counterCPU"]+1
        return output
    else:
        return 0
    
def ram_perc(d, id ) :
    """_summary_

    Args:
        d (_type_): _description_
        id (_type_): _description_

    Returns:
        _type_: _description_
    """
    if("usage" in d["memory_stats"]) :
        cpuDelta= float (d["memory_stats"]["usage"])
        systemDelta= float (d["memory_stats"]["limit" ])
        output = cpuDelta / systemDelta
        global measurements
        measurements[id]["totalRAM"] = measurements[id]["totalRAM"]+ output
        measurements[id]["counterRAM"] = measurements[id]["counterRAM"]+1
        return output
    else:
        return 0
    
def getStatsOfContainer(container,event):
    """_summary_

    Args:
        container (_type_): _description_
        event (_type_): _description_
    """
    output = "time;container_id;cpu_usage%;ram_usage%"
    for times in container.stats(stream=True) :
        data = json.loads(times)
        try:
            output = output + f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")};{container.id};{str(cpu_perc(data,container.id))};{str(ram_perc(data, container.id))}\n'
        except:
            print(bcolors.FAIL +"\nSomething went wrong analyzing the data\n")
        if event.is_set() :
            break
    f = open(f"{LOGFILE_PREFIX}{container.id}.csv", "w")
    f.write(output)
    f.close()
    
    
def run_measurment():
    """_summary_
    """
    try:
        client = docker.APIClient(base_url=DOCKER_HOST_API)
        client = docker.from_env()
    except:
        print(bcolors.FAIL +"\nConnection cannot be established\n")
        sys.exit(1)

    event = threading.Event()
    i = 0
    # ####################### Array for all Container - Resources ############################
    print(bcolors.OKBLUE + "Logging is started\n")
    for container in client.containers.list() :
        measurements[container.id] = {}
        measurements[container.id]["totalCPU"] = 0 
        measurements[container.id]["totalRAM"] = 0
        measurements[container.id]["counterCPU"] = 0
        measurements[container.id]["counterRAM"] = 0
    
        threads[container.id] = threading.Thread( target = getStatsOfContainer, args =( container , event ,) )
        threads[container.id].start()
    
    for i in trange(int(DURATION)*10):
        time.sleep(.1)
    event.set()
    print(bcolors.OKGREEN +"\nLogging is finished\n")
   


if __name__ == "__main__":

    run_measurment()


