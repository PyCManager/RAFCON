# singleton elements
import rafcon.statemachine.singleton
from rafcon.statemachine.storage import storage


# test environment elements
import testing_utils
from rafcon.statemachine.enums import StateExecutionState
from rafcon.utils import log
import time

logger = log.get_logger(__name__)

def test_run_to_selected_state(caplog):

    rafcon.statemachine.singleton.state_machine_manager.delete_all_state_machines()
    testing_utils.test_multithrading_lock.acquire()

    sm = storage.load_state_machine_from_path("/home_local/stoertebeker/develop/rafcon_tests/run_selected_state")
    # select state machine for this purpose

    rafcon.statemachine.singleton.state_machine_manager.add_state_machine(sm)
    rafcon.statemachine.singleton.state_machine_execution_engine.run_to_selected_state("VVBPOY/AOZXRY", sm.state_machine_id)
    # run the statemachine to the state before AOYXRY, this is an asychronous task

    while not sm.get_state_by_path("VVBPOY/ABNQFK").state_execution_status is StateExecutionState.WAIT_FOR_NEXT_STATE:
        time.sleep(.001)
    # wait until the statemachine is executed until ABNQFK the state before AOZXRY, so it doesnt check for the file
    # before its even written

    with open('/tmp/test_file', 'r') as test_file:
        lines = test_file.readlines()

    logger.debug("last entry in file is " + lines[len(lines)-1])
    assert len(lines) < 3
    # read all lines of the file and check if not more than 2 states have written to it

    rafcon.statemachine.singleton.state_machine_execution_engine.stop()
    rafcon.statemachine.singleton.state_machine_execution_engine.join()
    # the state machines waits at ABNQFK with state WAIT_FOR_NEXT_STATE, so it needs to be stopped manually

    testing_utils.test_multithrading_lock.release()
    testing_utils.assert_logger_warnings_and_errors(caplog)


if __name__ == '__main__':
    test_run_to_selected_state(None)
