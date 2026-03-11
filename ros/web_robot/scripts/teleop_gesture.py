#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import subprocess

import rospy
from web_robot.msg import Jog

class RosCondaBridge:
    def __init__(self):
        self.pub=rospy.Publisher('motion', Jog, queue_size=10)
        
        # specify conda and environment
        self.conda_root = os.path.expanduser("~/anaconda3")
        self.conda_env = "google_mediapipe"
        
        # python interprter
        self.interpreter = os.path.join(self.conda_root, "envs", self.conda_env, "bin", "python3.9")
        if not os.path.exists(self.interpreter):
            rospy.logerr("%s missing!", self.interpreter)
            raise FileNotFoundError("python interpreter not found!")
        rospy.loginfo("using python interpreter: %s.", self.interpreter)

        # execute script as child program in a new process
        # line buffered
        # stdin, stdout, stderr: new pipes to the excuted program
        self.script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools/mp_gesture.py")
        self.proc = subprocess.Popen(
            [self.interpreter, self.script_path],
            bufsize=1,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        rospy.loginfo("ros-conda bridge established.")
        
        # send requests periodically 
        self.request_interval = 0.1 
        self.timer = rospy.Timer(rospy.Duration(self.request_interval), self._request_callback)
        rospy.loginfo("sending requests every %.2f seconds.", self.request_interval)
        
    def _request_callback(self, event):
        payload = {
            "data": "ros_request",
            "timestamp": rospy.get_time()
        }
        
        try:
            # write to stdin
            buf_write = json.dumps(payload) + "\n"
            self.proc.stdin.write(buf_write)
            self.proc.stdin.flush()
            
            # read from stdout
            buf_read = self.proc.stdout.readline()
            rospy.loginfo("%s", buf_read)
            if buf_read:
                data = json.loads(buf_read.strip())
                
                # status from conda process
                if data["status"] == "error":
                    rospy.logerr("conda process error: %s", data["message"])
                    return
                
                # publish to ros topic
                j = Jog()
                j.q1 = float(data["joints"]["q1"])
                j.q2 = float(data["joints"]["q2"])
                j.q3 = float(data["joints"]["q3"])
                j.q4 = float(data["joints"]["q4"])
                j.q5 = float(data["joints"]["q5"])
                j.q6 = float(data["joints"]["q6"])
                self.pub.publish(j)
            else:
                rospy.logwarn("conda process return empty.")
                self.check_process_status()

        except Exception as e:
            rospy.logerr("communication error: %s", e)
            self.check_process_status()

    def check_process_status(self):
        if self.proc.poll() is not None:
            err = self.proc.stderr.read()
            rospy.logfatal("conda process terminated!\nexit code: %s, stderr: %s", self.proc.returncode, err)
            rospy.signal_shutdown('conda process terminated.')

    def on_shutdown(self):
        rospy.loginfo("shutting down, terminating subprocess...")
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            self.proc.wait()
        
if __name__ == '__main__':
    rospy.init_node('teleop_gesture')
    bridge = RosCondaBridge()
    try:
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
    finally:
        bridge.on_shutdown()
