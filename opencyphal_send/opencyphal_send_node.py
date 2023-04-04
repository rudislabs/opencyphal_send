#!/usr/bin/env python3
import rclpy
import numpy as np
import time
import can
from rclpy.node import Node
from rclpy.qos import QoSProfile
from rclpy.exceptions import ParameterNotDeclaredException
from rcl_interfaces.msg import Parameter, ParameterType, ParameterDescriptor
from canfd_msgs.msg import OpenCyphalMessage

class OpenCyphalSend(Node):
    def __init__(self):
        super().__init__('opencyphal_send_node')

        can_channel_descriptor = ParameterDescriptor(
            type=ParameterType.PARAMETER_STRING,
            description='CAN channel to send CAN frame on.')

        cyphal_input_topic_descriptor = ParameterDescriptor(
            type=ParameterType.PARAMETER_STRING,
            description='Cyphal input topic name.')

        self.declare_parameter("cyphal_input_topic", "/CyphalTransmitFrame", 
            cyphal_input_topic_descriptor)

        self.declare_parameter("can_channel", "can1", 
            can_channel_descriptor)

        self.CANChannel = self.get_parameter("can_channel").value
        self.CyphalSubTopic = self.get_parameter("cyphal_input_topic").value

        self.bus = can.Bus(channel='{:s}'.format(self.CANChannel), interface='socketcan', fd=True)
        self.SubCyphal = self.create_subscription(OpenCyphalMessage, '{:s}'.format(self.CyphalSubTopic), self.TransmitMessageToSocketCAN, 20)

    def TransmitMessageToSocketCAN(self, msg):
        Priority = int(msg.priority)
        IsAnnonymous = int(msg.is_annonymous)
        SubjectID = int(msg.subject_id)
        SourceNodeID = int(msg.source_node_id)
        if Priority > 7:
            Priority = 7
        elif Priority < 0:
            Priority = 0
        if IsAnnonymous > 1:
            IsAnnonymous = 1
        elif IsAnnonymous < 0:
            IsAnnonymous = 0
        if SubjectID > 8191:
            SubjectID = 8191
        elif SubjectID < 0:
            SubjectID = 0
        if SourceNodeID > 127:
            SourceNodeID = 127
        elif SourceNodeID < 0:
            SourceNodeID = 0
        
        ArbitrationID = (Priority << 26) + (IsAnnonymous << 24) + (3 << 21) + (SubjectID << 8) + SourceNodeID
        SocketCANData = msg.data
        SocketCANData = np.append(SocketCANData,[msg.crc], axis=0)
        
        SocketCANMessage = can.Message(arbitration_id=ArbitrationID, data=SocketCANData.tolist(), is_fd=True)
        try:
            self.bus.send(SocketCANMessage)
        except can.CanError:
            print('Message {:s} : {:08x} [{:x}] {:s} NOT sent'.format(
                self.CANChannel, ArbitrationID, 64,
                ''.join(map("{:02x} ".format, SocketCANData.tolist())).upper()))

def main(args=None):
    rclpy.init()
    OCS = OpenCyphalSend()
    rclpy.spin(OCS)
    OCS.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
