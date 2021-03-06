l#!/usr/bin/env python

"""
Starter script for lab1. 
Author: Chris Correa
"""
import numpy as np
import math
import matplotlib.pyplot as plt


from utils.utils import *

try:
    import rospy
    from geometry_msgs.msg import Pose, PoseStamped, Point
    from moveit_msgs.msg import RobotTrajectory
    from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
except:
    pass

class MotionPath:
    def __init__(self, limb, kin, total_time):
        """
        Parameters
        ----------
        limb : :obj:`baxter_interface.Limb` or :obj:`intera_interface.Limb`
        kin : :obj:`baxter_pykdl.baxter_kinematics` or :obj:`sawyer_pykdl.sawyer_kinematics`
            must be the same arm as limb
        total_time : float
            number of seconds you wish the trajectory to run for
        """
        self.limb = limb
        self.kin = kin
        self.total_time = total_time

    def target_position(self, time):
        """
        Returns where the arm end effector should be at time t

        Parameters
        ----------
        time : float        

        Returns
        -------
        3x' :obj:`numpy.ndarray`
            desired x,y,z position in workspace coordinates of the end effector
        """
        pass

    def target_velocity(self, time):
        """
        Returns the arm's desired x,y,z velocity in workspace coordinates
        at time t

        Parameters
        ----------
        time : float

        Returns
        -------
        3x' :obj:`numpy.ndarray`
            desired velocity in workspace coordinates of the end effector
        """
        pass

    def target_acceleration(self, time):
        """
        Returns the arm's desired x,y,z acceleration in workspace coordinates
        at time t

        Parameters
        ----------
        time : float

        Returns
        -------
        3x' :obj:`numpy.ndarray`
            desired acceleration in workspace coordinates of the end effector
        """
        pass

    def plot(self, num=300):
        times = np.linspace(0, self.total_time, num=num)
        target_positions = np.vstack([self.target_position(t) for t in times])
        target_velocities = np.vstack([self.target_velocity(t) for t in times])

        plt.figure()
        plt.subplot(3,2,1)
        plt.plot(times, target_positions[:,0], label='Desired')
        plt.xlabel("Time (t)")
        plt.ylabel("X Position")

        plt.subplot(3,2,2)
        plt.plot(times, target_velocities[:,0], label='Desired')
        plt.xlabel("Time (t)")
        plt.ylabel("X Velocity")
            
        plt.subplot(3,2,3)
        plt.plot(times, target_positions[:,1], label='Desired')
        plt.xlabel("time (t)")
        plt.ylabel("Y Position")

        plt.subplot(3,2,4)
        plt.plot(times, target_velocities[:,1], label='Desired')
        plt.xlabel("Time (t)")
        plt.ylabel("Y Velocity")
            
        plt.subplot(3,2,5)
        plt.plot(times, target_positions[:,2], label='Desired')
        plt.xlabel("time (t)")
        plt.ylabel("Z Position")

        plt.subplot(3,2,6)
        plt.plot(times, target_velocities[:,2], label='Desired')
        plt.xlabel("Time (t)")
        plt.ylabel("Z Velocity")

        plt.show()

    def to_robot_trajectory(self, num_waypoints=300, jointspace=True):
        """
        Parameters
        ----------
        num_waypoints : float
            how many points in the :obj:`moveit_msgs.msg.RobotTrajectory`
        jointspace : bool
            What kind of trajectory.  Joint space points are 7x' and describe the
            angle of each arm.  Workspace points are 3x', and describe the x,y,z
            position of the end effector.  
        """
        traj = JointTrajectory()
        traj.joint_names = self.limb.joint_names()    
        points = []
        for t in np.linspace(0, self.total_time, num=num_waypoints):
            point = self.trajectory_point(t, jointspace)
            points.append(point)

        # We want to make a final point at the end of the trajectory so that the 
        # controller has time to converge to the final point.
        extra_point = self.trajectory_point(self.total_time, jointspace)
        extra_point.time_from_start = rospy.Duration.from_sec(self.total_time + 1)
        points.append(extra_point)

        traj.points = points
        traj.header.frame_id = 'base'
        robot_traj = RobotTrajectory()
        robot_traj.joint_trajectory = traj
        return robot_traj

    def trajectory_point(self, t, jointspace):
        """
        takes a discrete point in time, and puts the position, velocity, and
        acceleration into a ROS JointTrajectoryPoint() to be put into a 
        RobotTrajectory.  
        
        Parameters
        ----------
        t : float
        jointspace : bool
            What kind of trajectory.  Joint space points are 7x' and describe the
            angle of each arm.  Workspace points are 3x', and describe the x,y,z
            position of the end effector.  

        Returns
        -------
        :obj:`trajectory_msgs.msg.JointTrajectoryPoint`


        joint_names: [left_s0, left_s1, left_e0, left_e1, left_w0, left_w1, left_w2]
        points: 
        - 
        positions: [-0.11520713 -1.01663718 -1.13026189  1.91170776  0.5837694   1.05630898  -0.70543966]



        """
        point = JointTrajectoryPoint()
        delta_t = .01
        if jointspace:
            x_t, x_t_1, x_t_2 = None, None, None
            ik_attempts = 0
            theta_t_2 = self.get_ik(self.target_position(t-2*delta_t))
            theta_t_1 = self.get_ik(self.target_position(t-delta_t))
            theta_t   = self.get_ik(self.target_position(t))
            
            # we said you shouldn't simply take a finite difference when creating
            # the path, why do you think we're doing that here?
            point.positions = theta_t
            point.velocities = (theta_t - theta_t_1) / delta_t
            point.accelerations = (theta_t - 2*theta_t_1 + theta_t_2) / (2*delta_t)
        else:
            point.positions = self.target_position(t)
            point.velocities = self.target_velocity(t)
            point.accelerations = self.target_acceleration(t)
        point.time_from_start = rospy.Duration.from_sec(t)
        return point

    def get_ik(self, x, max_ik_attempts=10):
        """
        gets ik
        
        Parameters
        ----------
        x : 3x' :obj:`numpy.ndarray`
            workspace position of the end effector
        max_ik_attempts : int
            number of attempts before short circuiting

        Returns
        -------
        7x' :obj:`numpy.ndarray`
            joint values to achieve the passed in workspace position
        """
        ik_attempts, theta = 0, None
        while theta is None and not rospy.is_shutdown():
            theta = self.kin.inverse_kinematics(
                position=x,
                orientation=[0, 1, 0, 0]
            )
            ik_attempts += 1
            if ik_attempts > max_ik_attempts:
                rospy.signal_shutdown(
                    'MAX IK ATTEMPTS EXCEEDED AT x(t)={}'.format(x)
                )
        return theta

class LinearPath(MotionPath):
    def __init__(self, limb, start_pos = None, kin, total_time, tag_pos):
        """
        Remember to call the constructor of MotionPath

        Parameters
        ----------
        ????? You're going to have to fill these in how you see fit
        tag_pos : list of numpy array positions of ar tags
        """
        self.tag_pos = tag_pos[0]
        #STARTING POSITION (YOU PROBABLY HAVE TO CHANGE THESE VALUES)
        if (start_pos == None):
            self.start_pos = limb.endpoint_pose()['position'];
        else:
            self.start_pos = start_pos
        MotionPath.__init__(self, limb, kin, total_time)

    def target_position(self, time):
        """
        Returns where the arm end effector should be at time t

        Parameters
        ----------
        time : float        
    
        Returns
        -------
        3x' :obj:`numpy.ndarray`
            desired x,y,z position in workspace coordinates of the end effector
        """
        if (time <= 0):
            return np.array([self.start_pos.x, self.start_pos.y, self.start_pos.z])
        index = max(time/self.total_time, 1)
        return np.array([(tag_pos[0] - self.start_pos.x) * index + self.start_pos.x, (tag_ps[1] - self.start_pos.y) * index + self.start_pos.y, (tag_pos[2] - self.star_pos.z) * index + self.star_pos.z])

    def target_velocity(self, time):
        """
        Returns the arm's desired x,y,z velocity in workspace coordinates
        at time t.  You should NOT simply take a finite difference of
        self.target_position()

        Parameters
        ----------
        time : float

        Returns
        -------
        3x' :obj:`numpy.ndarray`
            desired velocity in workspace coordinates of the end effector
        """
        #NOT REALLY SURE ABOUT THIS PART, IF YOU LOOK AT THE CODE, I'M NOT EVEN SURE THIS IS CALLED IF USING MOVE_IT
        if (time <= 0 or time > self.total_time):
            return np.zeros(3)
        return np.array([(tag_pos[0] - self.start_pos.x) / self.total_time, (tag_pos[1] - self.start_pos.y) / self.total_time, (tag_pos[2] - self.start_pos.z) / self.total_time])

    def target_acceleration(self, time):
        """
        Returns the arm's desired x,y,z acceleration in workspace coordinates
        at time t.  You should NOT simply take a finite difference of
        self.target_velocity()

        Parameters
        ----------
        time : float

        Returns
        -------
        3x' :obj:`numpy.ndarray`
            desired acceleration in workspace coordinates of the end effector
        """
        #SAME AS TARGET_VELOCITY, NOT SURE ABOUT THIS PART
        return np.array([0, 0, 0])

class CircularPath(MotionPath):
    def __init__(self, limb, kin, total_time, tag_pos):
        """
        Remember to call the constructor of MotionPath
        Parameters
        ----------
        ????? You're going to have to fill these in how you see fit
        tag_pos : list of numpy array positions of ar tags
        theta : amount of degrees currently around the circle, goes from 0 to 2*pi
        """
        self.tag_pos = tag_pos[0]
        #STARTING POSITION (YOU PROBABLY HAVE TO CHANGE THESE VALUES)
        #the idea is to start some set distance away in the x direction
        #as degree increments, the target position increments
        self.start_pos = limb.endpoint_pose()['position'];
        self.radius = np.array([self.tag_pos[0] - self.start_pos.x, self.tag_pos[1] - self.start_pos.y])

        #linear velocity = angular velocity * radius
        self.ang_velocity = 2 * math.pi / self.total_time
        MotionPath.__init__(self, limb, kin, total_time)

    def target_position(self, time):
        """
        Returns where the arm end effector should be at time t
        Parameters
        ----------
        time : float        
        Returns
        -------
        3x' :obj:`numpy.ndarray`
           desired x,y,z position in workspace coordinates of the end effector
        """
        #SUPER not sure about this one... basically a guess that this will work
        if (time == 0):
            return np.array([self.start_pos.x, self.start_pos.y, self.start_pos.z])
        theta = math.pi * 2 * (time / self.total_time)
        rot_vec = rotation2d(theta).dot(self.radius)
        return np.concatenate((rot_vec, self.start_pos.z - self.tag_pos[2]), axis = 0) + self.tag_pos

    def target_velocity(self, time):
        """
        Returns the arm's desired velocity in workspace coordinates
        at time t.  You should NOT simply take a finite difference of
        self.target_position()
        Parameters
        ----------
        time : float
        Returns
        -------
        3x' :obj:`numpy.ndarray`
           desired x,y,z velocity in workspace coordinates of the end effector
        """
        #NOT REALLY SURE ABOUT THIS PART, IF YOU LOOK AT THE CODE, I'M NOT EVEN SURE THIS IS CALLED IF USING MOVE_IT
        theta = math.pi * 2 * (time / self.total_time)
        rot_vec = np.concatenate((rotation2d(theta).dot(self.radius), 0), axis = 0)
        axis_vec = np.array([0, 0, self.ang_velocity])
        return np.cross(axis_vec, rot_vec)

    def target_acceleration(self, time):
        """
        Returns the arm's desired x,y,z acceleration in workspace coordinates
        at time t.  You should NOT simply take a finite difference of
        self.target_velocity()
        Parameters
        ----------
        time : float
        Returns
        -------
        3x' :obj:`numpy.ndarray`
           desired acceleration in workspace coordinates of the end effector
        """
        #SAME AS TARGET_VELOCITY, NOT SURE ABOUT THIS PART
        #not really sure what to put here
        #centripetal acceleration?
        #linear (tangential) acceleration is 0?
        rot_vec = np.concatenate((rotation2d(theta).dot(self.radius), 0), axis = 0)
        return -(self.ang_velocity**2 * rot_vec)

class MultiplePaths(MotionPath):
    """
    Remember to call the constructor of MotionPath
    
    You can implement multiple paths a couple ways.  The way I chose when I took
    the class was to create several different paths and pass those into the 
    MultiplePaths object, which would determine when to go onto the next path.
    """
    def __init__(self, limb, kin, total_time, tag_pos):
        #go from start to first tag
        self.path1 = LinearPath(limb, kin, total_time / 5, [tag_pos[0]])
        self.path2 = LinearPath(limb, start_pos = path1.target_position(total_time / 5), kin, total_time / 5, [tag_pos[1]])
        self.path3 = LinearPath(limb, start_pos = path2.target_position(total_time / 5), kin, total_time / 5, [tag_pos[2]])
        self.path4 = LinearPath(limb, start_pos = path3.target_position(total_time / 5), kin, total_time / 5, [tag_pos[3]])
        self.path5 = LinearPath(limb, start_pos = path4.target_position(total_time / 5), kin, total_time / 5, [tag_pos[0]])
        MotionPath.__init__(self, limb, kin, total_time)

    def target_position(self, time):
        """
        Returns where the arm end effector should be at time t
        Parameters
        ----------
        time : float        
        Returns
        -------
        3x' :obj:`numpy.ndarray`
            desired position in workspace coordinates of the end effector
        """
        #honestly this was a pretty dumb way to do it... if you think of something better change it please
        if (time > total_time * 4 / 5):
            return self.path5.target_position(time - total_time * 4 / 5)
        elif (time > total_time * 3 / 5):
            return self.path4.target_position(time - total_time * 3 / 5)
        elif (time > total_time * 2 / 5):
            return self.path3.target_position(time - total_time * 2 / 5)
        elif (time > total_time * 1 / 5):
            return self.path2.target_position(time - total_time * 1 / 5)
        else:
            return self.path1.target_position(time)

    def target_velocity(self, time):
        """
        Returns the arm's desired velocity in workspace coordinates
        at time t
        Parameters
        ----------
        time : float
        Returns
        -------
        3x' :obj:`numpy.ndarray`
            desired velocity in workspace coordinates of the end effector
        """
        if (time > total_time * 4 / 5):
            return self.path5.target_velocity(time - total_time * 4 / 5)
        elif (time > total_time * 3 / 5):
            return self.path4.target_velocity(time - total_time * 3 / 5)
        elif (time > total_time * 2 / 5):
            return self.path3.target_velocity(time - total_time * 2 / 5)
        elif (time > total_time * 1 / 5):
            return self.path2.target_velocity(time - total_time * 1 / 5)
        else:
            return self.path1.target_velocity(time)

    def target_acceleration(self, time):
        """
        Returns the arm's desired acceleration in workspace coordinates
        at time t
        Parameters
        ----------
        time : float
        Returns
        -------
        3x' :obj:`numpy.ndarray`
            desired acceleration in workspace coordinates of the end effector
        """
        if (time > total_time * 4 / 5):
            return self.path5.target_acceleration(time - total_time * 4 / 5)
        elif (time > total_time * 3 / 5):
            return self.path4.target_acceleration(time - total_time * 3 / 5)
        elif (time > total_time * 2 / 5):
            return self.path3.target_acceleration(time - total_time * 2 / 5)
        elif (time > total_time * 1 / 5):
            return self.path2.target_acceleration(time - total_time * 1 / 5)
        else:
            return self.path1.target_acceleration(time)
