"""
.. module:: state_helper
   :platform: Unix, Windows
   :synopsis: A module to represent a state in the statemachine

.. moduleauthor:: Sebastian Brunner


"""
import os

from rafcon.statemachine.storage.storage import StateMachineStorage
from rafcon.utils.constants import RAFCON_TEMP_PATH_STORAGE


class StateHelper(object):

    """A class that holds utility functions to modify and handle states.

    """

    def __init__(self):
        pass

    @staticmethod
    def get_state_copy(source_state):
        """
        This functions returns a state copy of a given state.
        :param source_state: the source state to make a copy of
        :return: the copy of the source state
        """
        state_copy = None
        local_storage = StateMachineStorage(RAFCON_TEMP_PATH_STORAGE+"/state_copy_tmp_folder")

        if not os.path.exists(local_storage.base_path):
            os.makedirs(local_storage.base_path)
        local_storage.save_state_recursively(source_state, "", True)
        state_copy = local_storage.load_state_from_path(os.path.join(local_storage.base_path, source_state.state_id))
        from rafcon.statemachine.states.execution_state import ExecutionState
        if isinstance(state_copy, ExecutionState):
            state_copy.script_text = source_state.script_text
        # state_copy._script.reset_script(state_copy.get_path())
        # change the id of the state
        state_copy.change_state_id()

        return state_copy
