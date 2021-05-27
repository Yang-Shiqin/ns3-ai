# should run with ns3 code (cd $YOUR_NS3_CODE; ./waf --run "rl-tcp") simultaneously
import py_interface
from ctypes import *


# This struct is the environment 
# shared between ns-3 and python with the same shared memory
# using the ns3-ai model.
class TcpRlEnv(Structure):
    _pack_ = 1
    _fields_ = [
        ('nodeId', c_uint32),
        ('socketUid', c_uint32),
        ('envType', c_uint8),
        ('simTime_us', c_int64),        # simulation time in microseconds
        ('ssThresh', c_uint32),         # slow start threshold
        ('cWnd', c_uint32),             # size of congestion window
        ('segmentSize', c_uint32),      # length of data segment sent by TCP at one time
        ('segmentsAcked', c_uint32),    # segments that have been acknowledged
        ('bytesInFlight', c_uint32),    # the amount of data that has been sent but not yet acknowledged
    ]

# The TCP RL action calculated by python 
# and put back to ns-3 with the shared memory.
class TcpRlAct(Structure):
    _pack_ = 1
    _fields_ = [
        ('new_ssThresh', c_uint32),
        ('new_cWnd', c_uint32)
    ]

mempool_key = 1234                                  # memory pool key, arbitrary integer large than 1000
mem_size = 4096                                     # memory pool size in bytes
memblock_key = 1234                                 # memory block key, need to keep the same in the ns-3 script
py_interface.Init(mempool_key, mem_size)            # init shared memory pool

var = py_interface.Ns3AIRL(memblock_key, TcpRlEnv, TcpRlAct)    # Link the shared memory block with ns-3 script

# var = py_interface.ShmBigVar(1234, TcpRl)
while not var.isFinish():
    # while var.GetVersion() % 2 != 1:
    #     pass
    # with var as data:
    #     # print(data.env.ssThresh, data.env.cWnd)
    with var as data:
        if data == None:
            break

    # Reinforcement Learning code there
        print(var.GetVersion())
        # get the data from ns-3 through the shared memory
        ssThresh = data.env.ssThresh
        cWnd = data.env.cWnd
        segmentsAcked = data.env.segmentsAcked
        segmentSize = data.env.segmentSize
        bytesInFlight = data.env.bytesInFlight
        print(ssThresh, cWnd, segmentsAcked, segmentSize, bytesInFlight)
        new_cWnd = 1
        new_ssThresh = 1

        # IncreaseWindow
        if (cWnd < ssThresh):
            # slow start
            if (segmentsAcked >= 1):
                new_cWnd = cWnd + segmentSize

        if (cWnd >= ssThresh):
            # congestion avoidance
            if (segmentsAcked > 0):
                adder = 1.0 * (segmentSize * segmentSize) / cWnd
                adder = int(max(1.0, adder))
                new_cWnd = cWnd + adder

        # GetSsThresh
        new_ssThresh = int(max(2 * segmentSize, bytesInFlight / 2))
        data.act.new_cWnd = new_cWnd
        data.act.new_ssThresh = new_ssThresh

py_interface.FreeMemory()               # Free shared memory pool
