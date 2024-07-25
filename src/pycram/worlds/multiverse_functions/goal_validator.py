from time import sleep, time

import numpy as np
import rospy
from typing_extensions import Any, Callable, Optional, Union, Iterable, Dict, TYPE_CHECKING

from pycram.datastructures.enums import JointType
from pycram.worlds.multiverse_functions.error_checkers import ErrorChecker, PoseErrorChecker, PositionErrorChecker, \
    OrientationErrorChecker, SingleValueErrorChecker

if TYPE_CHECKING:
    from pycram.datastructures.world import World
    from pycram.world_concepts.world_object import Object
    from pycram.datastructures.pose import Pose
    from pycram.description import ObjectDescription

    Joint = ObjectDescription.Joint
    Link = ObjectDescription.Link

OptionalArgCallable = Union[Callable[[], Any], Callable[[Any], Any]]


class GoalValidator:
    """
    A class to validate the goal by tracking the goal achievement progress.
    """

    raise_error: Optional[bool] = False
    """
    Whether to raise an error if the goal is not achieved.
    """

    def __init__(self, error_checker: ErrorChecker, current_value_getter: OptionalArgCallable,
                 acceptable_percentage_of_goal_achieved: Optional[float] = 0.8):
        """
        Initialize the goal validator.
        :param error_checker: The error checker.
        :param current_value_getter: The current value getter function which takes an optional input and returns the
        current value.
        :param acceptable_percentage_of_goal_achieved: The acceptable percentage of goal achieved, if given, will be
        used to check if this percentage is achieved instead of the complete goal.
        """
        self.error_checker: ErrorChecker = error_checker
        self.current_value_getter: Callable[[Optional[Any]], Any] = current_value_getter
        self.acceptable_percentage_of_goal_achieved: Optional[float] = acceptable_percentage_of_goal_achieved
        self.goal_value: Optional[Any] = None
        self.initial_error: Optional[np.ndarray] = None
        self.current_value_getter_input: Optional[Any] = None

    def register_goal_and_wait_until_achieved(self, goal_value: Any,
                                              current_value_getter_input: Optional[Any] = None,
                                              initial_value: Optional[Any] = None,
                                              acceptable_error: Optional[Union[float, Iterable[float]]] = None,
                                              max_wait_time: Optional[float] = 1,
                                              time_per_read: Optional[float] = 0.01) -> None:
        """
        Register the goal value and wait until the target is reached.
        :param goal_value: The goal value.
        :param current_value_getter_input: The values that are used as input to the current value getter.
        :param initial_value: The initial value.
        :param acceptable_error: The acceptable error.
        :param max_wait_time: The maximum time to wait.
        :param time_per_read: The time to wait between each read.
        """
        self.register_goal(goal_value, current_value_getter_input, initial_value, acceptable_error)
        self.wait_until_goal_is_achieved(max_wait_time, time_per_read)

    def wait_until_goal_is_achieved(self, max_wait_time: Optional[float] = 1,
                                    time_per_read: Optional[float] = 0.01) -> None:
        """
        Wait until the target is reached.
        :param max_wait_time: The maximum time to wait.
        :param time_per_read: The time to wait between each read.
        """
        if self.goal_value is None:
            return  # Skip if goal value is None
        start_time = time()
        current = self.current_value
        while not self.goal_achieved:
            sleep(time_per_read)
            if time() - start_time > max_wait_time:
                msg = f"Failed to achieve goal from initial error {self.initial_error} with" \
                      f" goal {self.goal_value} within {max_wait_time}" \
                      f" seconds, the current value is {current}, error is {self.current_error}, percentage" \
                      f" of goal achieved is {self.percentage_of_goal_achieved}"
                if self.raise_error:
                    rospy.logerr(msg)
                    raise TimeoutError(msg)
                else:
                    rospy.logwarn(msg)
                    break
            current = self.current_value
        self.reset()

    def reset(self) -> None:
        """
        Reset the goal validator.
        """
        self.goal_value = None
        self.initial_error = None
        self.current_value_getter_input = None
        self.error_checker.reset()

    @property
    def _acceptable_error(self) -> np.ndarray:
        """
        Get the acceptable error.
        """
        if self.error_checker.is_iterable:
            return self.tiled_acceptable_error
        else:
            return self.acceptable_error

    @property
    def acceptable_error(self) -> np.ndarray:
        """
        Get the acceptable error.
        """
        return self.error_checker.acceptable_error

    @property
    def tiled_acceptable_error(self) -> Optional[np.ndarray]:
        """
        Get the tiled acceptable error.
        """
        return self.error_checker.tiled_acceptable_error

    def register_goal(self, goal_value: Any,
                      current_value_getter_input: Optional[Any] = None,
                      initial_value: Optional[Any] = None,
                      acceptable_error: Optional[Union[float, Iterable[float]]] = None):
        """
        Register the goal value.
        :param goal_value: The goal value.
        :param current_value_getter_input: The values that are used as input to the current value getter.
        :param initial_value: The initial value.
        :param acceptable_error: The acceptable error.
        """
        if goal_value is None or hasattr(goal_value, '__len__') and len(goal_value) == 0:
            return  # Skip if goal value is None or empty
        self.goal_value = goal_value
        self.current_value_getter_input = current_value_getter_input
        self.update_initial_error(goal_value, initial_value=initial_value)
        self.error_checker.update_acceptable_error(acceptable_error, self.initial_error)

    def update_initial_error(self, goal_value: Any, initial_value: Optional[Any] = None) -> None:
        """
        Calculate the initial error.
        """
        if initial_value is None:
            self.initial_error: np.ndarray = self.current_error
        else:
            self.initial_error: np.ndarray = self.calculate_error(goal_value, initial_value)

    @property
    def current_value(self) -> Any:
        """
        Get the current value.
        """
        if self.current_value_getter_input is not None:
            return self.current_value_getter(self.current_value_getter_input)
        else:
            return self.current_value_getter()

    @property
    def current_error(self) -> np.ndarray:
        """
        Calculate the current error.
        """
        return self.calculate_error(self.goal_value, self.current_value)

    def calculate_error(self, value_1: Any, value_2: Any) -> np.ndarray:
        """
        Calculate the error between two values.
        """
        return np.array(self.error_checker.calculate_error(value_1, value_2)).flatten()

    @property
    def percentage_of_goal_achieved(self) -> float:
        """
        Calculate the percentage of goal achieved.
        """
        percent_array = 1 - self.relative_current_error / self.relative_initial_error
        percent_array_filtered = percent_array[self.relative_initial_error > self._acceptable_error]
        if len(percent_array_filtered) == 0:
            return 1
        else:
            return np.mean(percent_array_filtered)

    @property
    def actual_percentage_of_goal_achieved(self) -> float:
        """
        Calculate the percentage of goal achieved.
        """
        percent_array = 1 - self.current_error / np.maximum(self.initial_error, 1e-3)
        percent_array_filtered = percent_array[self.initial_error > self._acceptable_error]
        if len(percent_array_filtered) == 0:
            return 1
        else:
            return np.mean(percent_array_filtered)

    @property
    def relative_current_error(self) -> np.ndarray:
        """
        Get the relative current error.
        """
        return self.get_relative_error(self.current_error, threshold=0)

    @property
    def relative_initial_error(self) -> np.ndarray:
        """
        Get the relative initial error.
        """
        return np.maximum(self.initial_error, 1e-3)

    def get_relative_error(self, error: Any, threshold: Optional[float] = 1e-3) -> np.ndarray:
        """
        Get the relative error by comparing the error with the acceptable error and filtering out the errors that are
        less than the threshold.
        :param error: The error.
        :param threshold: The threshold.
        """
        return np.maximum(error - self._acceptable_error, threshold)

    @property
    def goal_achieved(self) -> bool:
        """
        Check if the goal is achieved.
        return: Whether the goal is achieved.
        """
        if self.acceptable_percentage_of_goal_achieved is None:
            return self.is_current_error_acceptable
        else:
            return self.percentage_of_goal_achieved >= self.acceptable_percentage_of_goal_achieved

    @property
    def is_current_error_acceptable(self) -> bool:
        """
        Check if the error is acceptable.
        return: Whether the error is acceptable.
        """
        return self.error_checker.is_error_acceptable(self.current_value, self.goal_value)


class PoseGoalValidator(GoalValidator):
    """
    A class to validate the pose goal by tracking the goal achievement progress.
    """

    def __init__(self, current_pose_getter: OptionalArgCallable = None,
                 acceptable_error: Union[float, Iterable[float]] = (1e-3, np.pi / 180),
                 acceptable_percentage_of_goal_achieved: Optional[float] = 0.8,
                 is_iterable: Optional[bool] = False):
        """
        Initialize the pose goal validator.
        :param current_pose_getter: The current pose getter function which takes an optional input and returns the
        current pose.
        :param acceptable_error: The acceptable error.
        :param acceptable_percentage_of_goal_achieved: The acceptable percentage of goal achieved.
        """
        super().__init__(PoseErrorChecker(acceptable_error, is_iterable=is_iterable), current_pose_getter,
                         acceptable_percentage_of_goal_achieved=acceptable_percentage_of_goal_achieved)


class MultiPoseGoalValidator(PoseGoalValidator):
    """
    A class to validate the multi-pose goal by tracking the goal achievement progress.
    """

    def __init__(self, current_poses_getter: OptionalArgCallable = None,
                 acceptable_error: Union[float, Iterable[float]] = (1e-2, 5 * np.pi / 180),
                 acceptable_percentage_of_goal_achieved: Optional[float] = 0.8):
        """
        Initialize the multi-pose goal validator.
        :param current_poses_getter: The current poses getter function which takes an optional input and returns the
        current poses.
        :param acceptable_error: The acceptable error.
        :param acceptable_percentage_of_goal_achieved: The acceptable percentage of goal achieved.
        """
        super().__init__(current_poses_getter, acceptable_error, acceptable_percentage_of_goal_achieved,
                         is_iterable=True)


class PositionGoalValidator(GoalValidator):
    """
    A class to validate the position goal by tracking the goal achievement progress.
    """

    def __init__(self, current_position_getter: OptionalArgCallable = None,
                 acceptable_error: Optional[float] = 1e-3,
                 acceptable_percentage_of_goal_achieved: Optional[float] = 0.8,
                 is_iterable: Optional[bool] = False):
        """
        Initialize the position goal validator.
        :param current_position_getter: The current position getter function which takes an optional input and
         returns the current position.
        :param acceptable_error: The acceptable error.
        :param acceptable_percentage_of_goal_achieved: The acceptable percentage of goal achieved.
        :param is_iterable: Whether it is a sequence of position vectors.
        """
        super().__init__(PositionErrorChecker(acceptable_error, is_iterable=is_iterable), current_position_getter,
                         acceptable_percentage_of_goal_achieved=acceptable_percentage_of_goal_achieved)


class MultiPositionGoalValidator(PositionGoalValidator):
    """
    A class to validate the multi-position goal by tracking the goal achievement progress.
    """

    def __init__(self, current_positions_getter: OptionalArgCallable = None,
                 acceptable_error: Optional[float] = 1e-3,
                 acceptable_percentage_of_goal_achieved: Optional[float] = 0.8):
        """
        Initialize the multi-position goal validator.
        :param current_positions_getter: The current positions getter function which takes an optional input and
         returns the current positions.
        :param acceptable_error: The acceptable error.
        :param acceptable_percentage_of_goal_achieved: The acceptable percentage of goal achieved.
        """
        super().__init__(current_positions_getter, acceptable_error, acceptable_percentage_of_goal_achieved,
                         is_iterable=True)


class OrientationGoalValidator(GoalValidator):
    """
    A class to validate the orientation goal by tracking the goal achievement progress.
    """

    def __init__(self, current_orientation_getter: OptionalArgCallable = None,
                 acceptable_error: Optional[float] = np.pi / 180,
                 acceptable_percentage_of_goal_achieved: Optional[float] = 0.8,
                 is_iterable: Optional[bool] = False):
        """
        Initialize the orientation goal validator.
        :param current_orientation_getter: The current orientation getter function which takes an optional input and
         returns the current orientation.
        :param acceptable_error: The acceptable error.
        :param acceptable_percentage_of_goal_achieved: The acceptable percentage of goal achieved.
        :param is_iterable: Whether it is a sequence of quaternions.
        """
        super().__init__(OrientationErrorChecker(acceptable_error, is_iterable=is_iterable), current_orientation_getter,
                         acceptable_percentage_of_goal_achieved=acceptable_percentage_of_goal_achieved)


class MultiOrientationGoalValidator(OrientationGoalValidator):
    """
    A class to validate the multi-orientation goal by tracking the goal achievement progress.
    """

    def __init__(self, current_orientations_getter: OptionalArgCallable = None,
                 acceptable_error: Optional[float] = np.pi / 180,
                 acceptable_percentage_of_goal_achieved: Optional[float] = 0.8):
        """
        Initialize the multi-orientation goal validator.
        :param current_orientations_getter: The current orientations getter function which takes an optional input and
         returns the current orientations.
        :param acceptable_error: The acceptable error.
        :param acceptable_percentage_of_goal_achieved: The acceptable percentage of goal achieved.
        """
        super().__init__(current_orientations_getter, acceptable_error, acceptable_percentage_of_goal_achieved,
                         is_iterable=True)


class JointPositionGoalValidator(GoalValidator):
    """
    A class to validate the joint position goal by tracking the goal achievement progress.
    """

    def __init__(self, current_position_getter: OptionalArgCallable = None,
                 acceptable_error: Optional[float] = None,
                 acceptable_orientation_error: Optional[Iterable[float]] = np.pi / 180,
                 acceptable_position_error: Optional[Iterable[float]] = 1e-3,
                 acceptable_percentage_of_goal_achieved: Optional[float] = 0.8,
                 is_iterable: Optional[bool] = False):
        """
        Initialize the joint position goal validator.
        :param current_position_getter: The current position getter function which takes an optional input and returns
         the current position.
        :param acceptable_error: The acceptable error.
        :param acceptable_orientation_error: The acceptable orientation error.
        :param acceptable_position_error: The acceptable position error.
        :param acceptable_percentage_of_goal_achieved: The acceptable percentage of goal achieved.
        :param is_iterable: Whether it is a sequence of joint positions.
        """
        super().__init__(SingleValueErrorChecker(acceptable_error, is_iterable=is_iterable), current_position_getter,
                         acceptable_percentage_of_goal_achieved=acceptable_percentage_of_goal_achieved)
        self.acceptable_orientation_error = acceptable_orientation_error
        self.acceptable_position_error = acceptable_position_error

    def register_goal(self, goal_value: Any, joint_type: JointType,
                      current_value_getter_input: Optional[Any] = None,
                      initial_value: Optional[Any] = None,
                      acceptable_error: Optional[float] = None):
        """
        Register the goal value.
        :param goal_value: The goal value.
        :param joint_type: The joint type (e.g. REVOLUTE, PRISMATIC).
        :param current_value_getter_input: The values that are used as input to the current value getter.
        :param initial_value: The initial value.
        :param acceptable_error: The acceptable error.
        """
        if acceptable_error is None:
            self.error_checker.acceptable_error = self.acceptable_orientation_error if joint_type == JointType.REVOLUTE\
                else self.acceptable_position_error
        super().register_goal(goal_value, current_value_getter_input, initial_value, acceptable_error)


class MultiJointPositionGoalValidator(GoalValidator):
    """
    A class to validate the multi-joint position goal by tracking the goal achievement progress.
    """

    def __init__(self, current_positions_getter: OptionalArgCallable = None,
                 acceptable_error: Optional[Iterable[float]] = None,
                 acceptable_orientation_error: Optional[Iterable[float]] = np.pi / 180,
                 acceptable_position_error: Optional[Iterable[float]] = 1e-3,
                 acceptable_percentage_of_goal_achieved: Optional[float] = 0.8):
        """
        Initialize the multi-joint position goal validator.
        :param current_positions_getter: The current positions getter function which takes an optional input and
         returns the current positions.
        :param acceptable_error: The acceptable error.
        :param acceptable_orientation_error: The acceptable orientation error.
        :param acceptable_position_error: The acceptable position error.
        :param acceptable_percentage_of_goal_achieved: The acceptable percentage of goal achieved.
        """
        super().__init__(SingleValueErrorChecker(acceptable_error, is_iterable=True), current_positions_getter,
                         acceptable_percentage_of_goal_achieved)
        self.acceptable_orientation_error = acceptable_orientation_error
        self.acceptable_position_error = acceptable_position_error

    def register_goal(self, goal_value: Any, joint_type: Iterable[JointType],
                      current_value_getter_input: Optional[Any] = None,
                      initial_value: Optional[Any] = None,
                      acceptable_error: Optional[Iterable[float]] = None):
        if acceptable_error is None:
            self.error_checker.acceptable_error = [self.acceptable_orientation_error if jt == JointType.REVOLUTE
                                                   else self.acceptable_position_error for jt in joint_type]
        super().register_goal(goal_value, current_value_getter_input, initial_value, acceptable_error)


def validate_object_pose(pose_setter_func):
    """
    A decorator to validate the object pose.
    :param pose_setter_func: The function to set the pose of the object.
    """

    def wrapper(world: 'World', obj: 'Object', pose: 'Pose'):
        attachments_pose_goal = obj.get_target_poses_of_attached_objects_given_parent(pose)
        if len(attachments_pose_goal) == 0:
            world.pose_goal_validator.register_goal(pose, obj)
        else:
            world.multi_pose_goal_validator.register_goal([pose, *list(attachments_pose_goal.values())],
                                                          [obj, *list(attachments_pose_goal.keys())])
        if not pose_setter_func(world, obj, pose):
            world.pose_goal_validator.reset()
            world.multi_pose_goal_validator.reset()
            return False

        world.pose_goal_validator.wait_until_goal_is_achieved()
        world.multi_pose_goal_validator.wait_until_goal_is_achieved()
        return True

    return wrapper


def validate_multiple_joint_positions(position_setter_func):
    """
    A decorator to validate the joint positions, this function does not validate the virtual joints,
    as in multiverse the virtual joints take command velocities and not positions, so after their goals
    are set, they are zeroed thus can't be validated. (They are actually validated by the robot pose in case
    of virtual move base joints)
    :param position_setter_func: The function to set the joint positions.
    """

    def wrapper(world: 'World', joint_positions: Dict['Joint', float]):
        joint_positions_to_validate = {joint: position for joint, position in joint_positions.items()
                                       if not joint.is_virtual}
        joint_types = [joint.type for joint in joint_positions_to_validate.keys()]
        world.multi_joint_position_goal_validator.register_goal(list(joint_positions_to_validate.values()), joint_types,
                                                                list(joint_positions_to_validate.keys()))
        if not position_setter_func(world, joint_positions):
            world.multi_joint_position_goal_validator.reset()
            return False

        world.multi_joint_position_goal_validator.wait_until_goal_is_achieved()
        return True

    return wrapper
