import os
import gc
import time
import gtkmvc

import rafcon.core.singleton
from rafcon.core.states.execution_state import ExecutionState
from rafcon.core.states.hierarchy_state import HierarchyState
import rafcon.core.states.state
import rafcon.core.state_elements.state_element

from rafcon.utils.constants import RAFCON_TEMP_PATH_BASE

import core.test_states as basic_state_machines
import testing_utils
from rafcon.utils import log
logger = log.get_logger(__name__)

GENERATION_LOG_FILE_APPENDIX = 'gen_log_file.txt'
DELETION_LOG_FILE_APPENDIX = 'del_log_file.txt'

CORE_FILES = ['state', 'state_element']

MODEL_FILES = ['abstract_state_model', 'state_element_model']

CTRL_FILES = ['extended_controller']

GTKMVC_FILES = ['gtkmvc_view', 'gtkmvc_controller']

FILES = CORE_FILES + MODEL_FILES + CTRL_FILES

# store method of core element classes
old_state_init = None
old_state_element_init = None

# store method of model element classes
old_abstract_state_model_init = None
old_state_element_model_init = None

# store method of extended ctrl class
old_extended_controller_init = None

# store method of gtkmvc element classes
old_gtkmvc_view_init = gtkmvc.View.__init__
old_gtkmvc_controller_init = gtkmvc.Controller.__init__


def create_container_state(*args, **kargs):

    state1 = ExecutionState('State1', state_id='STATE1')
    output_state1 = state1.add_output_data_port("output", "int")
    input_state1 = state1.add_input_data_port("input", "str", "zero")
    state2 = ExecutionState('State2', state_id='STATE2')
    input_par_state2 = state2.add_input_data_port("par", "int", 0)
    output_res_state2 = state2.add_output_data_port("res", "int")
    state4 = HierarchyState(name='Nested', state_id='NESTED')
    state4.add_outcome('GoGo')
    output_state4 = state4.add_output_data_port("out", "int")
    state5 = ExecutionState('Nested2', state_id='NESTED2')
    state5.add_outcome('HereWeGo')
    input_state5 = state5.add_input_data_port("in", "int", 0)
    state3 = HierarchyState(name='State3', state_id='STATE3')
    input_state3 = state3.add_input_data_port("input", "int", 0)
    output_state3 = state3.add_output_data_port("output", "int")
    state3.add_state(state4)
    state3.add_state(state5)
    state3.set_start_state(state4)
    state3.add_scoped_variable("share", "int", 3)
    state3.add_transition(state4.state_id, 0, state5.state_id, None)
    state3.add_transition(state5.state_id, 0, state3.state_id, 0)
    state3.add_data_flow(state4.state_id, output_state4, state5.state_id, input_state5)
    state3.add_outcome('Branch1')
    state3.add_outcome('Branch2')

    ctr_state = HierarchyState(name="Container", state_id='CONT2')
    ctr_state.add_state(state1)
    ctr_state.add_state(state2)
    ctr_state.add_state(state3)
    input_ctr_state = ctr_state.add_input_data_port("ctr_in", "str", "zero")
    output_ctr_state = ctr_state.add_output_data_port("ctr_out", "int")
    ctr_state.set_start_state(state1)
    ctr_state.add_transition(state1.state_id, 0, state2.state_id, None)
    ctr_state.add_transition(state2.state_id, 0, state3.state_id, None)
    ctr_state.add_transition(state3.state_id, 0, ctr_state.state_id, 0)
    ctr_state.add_data_flow(state1.state_id, output_state1, state2.state_id, input_par_state2)
    ctr_state.add_data_flow(state2.state_id, output_res_state2, state3.state_id, input_state3)
    ctr_state.add_data_flow(ctr_state.state_id, input_ctr_state, state1.state_id, input_state1)
    ctr_state.add_data_flow(state3.state_id, output_state3, ctr_state.state_id, output_ctr_state)
    ctr_state.name = "Container"

    ctr_state.add_input_data_port("input", "str", "default_value1")
    ctr_state.add_input_data_port("pos_x", "str", "default_value2")
    ctr_state.add_input_data_port("pos_y", "str", "default_value3")

    ctr_state.add_output_data_port("output", "str", "default_value1")
    ctr_state.add_output_data_port("result", "str", "default_value2")

    scoped_variable1_ctr_state = ctr_state.add_scoped_variable("scoped", "str", "default_value1")
    scoped_variable3_ctr_state = ctr_state.add_scoped_variable("ctr", "int", 42)

    ctr_state.add_data_flow(ctr_state.state_id, input_ctr_state, ctr_state.state_id, scoped_variable1_ctr_state)
    ctr_state.add_data_flow(state1.state_id, output_state1, ctr_state.state_id, scoped_variable3_ctr_state)

    state_dict = {'Container': ctr_state, 'State1': state1, 'State2': state2, 'State3': state3, 'Nested': state4,
                  'Nested2': state5}

    return ctr_state, state_dict


def generate_sm_for_garbage_collector():
    ctr_state, dict_states = create_container_state()
    from rafcon.core.state_machine import StateMachine
    _ = StateMachine(ctr_state)


def get_log_elements(elements, with_prints=False, print_method=None):

    log_result_dict = {}
    for element_name, with_assert, object_class in elements:
        gen_file = os.path.join(RAFCON_TEMP_PATH_BASE, "{0}_{1}".format(element_name, GENERATION_LOG_FILE_APPENDIX))
        with open(gen_file) as f:
            element_gen_file = f.readlines()
        element_gen_file = [line.replace('\n', '') for line in element_gen_file]

        # TODO find not deleted by checking gc for which are still existing if this is useful to know
        with_prints = False
        element_del_file = []

        # if element_name == 'state':
        for elem in element_gen_file:
            mem_id = elem.split(" ")

            if with_prints:
                _print_method = logger.error if with_assert else print_method
                if (mem_id[-2], mem_id[-1]) not in [(e.split(" ")[-2], e.split(" ")[-1]) for e in element_del_file]:
                    s = "{0} object still in memory: \n{1}\nDeleted are:\n{2}".format(element_name, elem,
                                                                                      '\n'.join(element_del_file))
                else:
                    s = None
                    # s = "{0} object destroyed: \n{1}\n".format(element_name, elem, ''.join(element_del_file))
                if s is not None:
                    if _print_method is not None:
                        _print_method(s)
                    else:
                        print s

        log_result_dict[element_name] = {'gen_file': element_gen_file, 'del_file': element_del_file}

    # print '\n'.join(["{0}: \n{1}\n{2}".format(element_name, log_files['gen_file'], log_files['del_file'])
    #                  for element_name, log_files in log_result_dict.iteritems()])

    return log_result_dict


def check_log_files(elements):
    files = []
    for element_name in elements:
        files.append(os.path.join(RAFCON_TEMP_PATH_BASE, "{0}_{1}".format(element_name, GENERATION_LOG_FILE_APPENDIX)))

    for file_path in files:
        print "check file: ", file_path
        if os.path.exists(file_path):
            print "exists before: ", file_path
        with open(file_path, 'a+'):
            pass
        if os.path.exists(file_path):
            print "exists after: ", file_path


def remove_log_files(elements):
    files = []
    for element_name in elements:
        files.append(os.path.join(RAFCON_TEMP_PATH_BASE, "{0}_{1}".format(element_name, GENERATION_LOG_FILE_APPENDIX)))
    print "REMOVE: \n{}".format('\n'.join([log_file_path for log_file_path in files]))
    for log_file_path in files:
        if os.path.exists(log_file_path):
            os.remove(log_file_path)


def create_models():
    import logging
    import rafcon.core.singleton
    from rafcon.core.state_machine import StateMachine
    from rafcon.core.states.execution_state import ExecutionState
    from rafcon.core.states.hierarchy_state import HierarchyState
    import rafcon.gui.singleton

    # global_gui_config.set_config_value('HISTORY_ENABLED', True)
    logger = log.get_logger(__name__)
    logger.setLevel(logging.DEBUG)
    for handler in logging.getLogger('gtkmvc').handlers:
        logging.getLogger('gtkmvc').removeHandler(handler)

    state1 = ExecutionState('State1', state_id='STATE1')
    output_state1 = state1.add_output_data_port("output", "int")
    input_state1 = state1.add_input_data_port("input", "str", "zero")
    state2 = ExecutionState('State2', state_id='STATE2')
    input_par_state2 = state2.add_input_data_port("par", "int", 0)
    output_res_state2 = state2.add_output_data_port("res", "int")
    state4 = HierarchyState(name='Nested', state_id='NESTED')
    state4.add_outcome('GoGo')
    output_state4 = state4.add_output_data_port("out", "int")
    state5 = ExecutionState('Nested2', state_id='NESTED2')
    state5.add_outcome('HereWeGo')
    input_state5 = state5.add_input_data_port("in", "int", 0)
    state3 = HierarchyState(name='State3', state_id='STATE3')
    input_state3 = state3.add_input_data_port("input", "int", 0)
    output_state3 = state3.add_output_data_port("output", "int")
    state3.add_state(state4)
    state3.add_state(state5)
    state3.set_start_state(state4)
    state3.add_scoped_variable("share", "int", 3)
    state3.add_transition(state4.state_id, 0, state5.state_id, None)
    state3.add_transition(state5.state_id, 0, state3.state_id, 0)
    state3.add_data_flow(state4.state_id, output_state4, state5.state_id, input_state5)
    state3.add_outcome('Branch1')
    state3.add_outcome('Branch2')

    ctr_state = HierarchyState(name="Container", state_id='CONT2')
    ctr_state.add_state(state1)
    ctr_state.add_state(state2)
    ctr_state.add_state(state3)
    input_ctr_state = ctr_state.add_input_data_port("ctr_in", "str", "zero")
    output_ctr_state = ctr_state.add_output_data_port("ctr_out", "int")
    ctr_state.set_start_state(state1)
    ctr_state.add_transition(state1.state_id, 0, state2.state_id, None)
    ctr_state.add_transition(state2.state_id, 0, state3.state_id, None)
    ctr_state.add_transition(state3.state_id, 0, ctr_state.state_id, 0)
    ctr_state.add_data_flow(state1.state_id, output_state1, state2.state_id, input_par_state2)
    ctr_state.add_data_flow(state2.state_id, output_res_state2, state3.state_id, input_state3)
    ctr_state.add_data_flow(ctr_state.state_id, input_ctr_state, state1.state_id, input_state1)
    ctr_state.add_data_flow(state3.state_id, output_state3, ctr_state.state_id, output_ctr_state)
    ctr_state.name = "Container"

    ctr_state.add_input_data_port("input", "str", "default_value1")
    ctr_state.add_input_data_port("pos_x", "str", "default_value2")
    ctr_state.add_input_data_port("pos_y", "str", "default_value3")

    ctr_state.add_output_data_port("output", "str", "default_value1")
    ctr_state.add_output_data_port("result", "str", "default_value2")

    scoped_variable1_ctr_state = ctr_state.add_scoped_variable("scoped", "str", "default_value1")
    scoped_variable3_ctr_state = ctr_state.add_scoped_variable("ctr", "int", 42)

    ctr_state.add_data_flow(ctr_state.state_id, input_ctr_state, ctr_state.state_id, scoped_variable1_ctr_state)
    ctr_state.add_data_flow(state1.state_id, output_state1, ctr_state.state_id, scoped_variable3_ctr_state)

    state_dict = {'Container': ctr_state, 'State1': state1, 'State2': state2, 'State3': state3, 'Nested': state4,
                  'Nested2': state5}
    sm = StateMachine(ctr_state)
    rafcon.core.singleton.state_machine_manager.add_state_machine(sm)
    rafcon.gui.singleton.state_machine_manager_model.selected_state_machine_id = sm.state_machine_id
    testing_utils.wait_for_gui()
    sm_m = rafcon.gui.singleton.state_machine_manager_model.state_machines[sm.state_machine_id]
    # sm_m.history.fake = False
    # print "with_prints is: ", sm_m.history.with_prints
    # sm_m.history.with_prints = False
    return logger, sm_m, state_dict


def check_existing_objects_of_kind(elements, print_method=None, ignored_objects=None, log_file=True):
    found_objects = []
    if ignored_objects is None:
        ignored_objects = []
    print_method = logger.warning if print_method is None else print_method
    if log_file:
        result_dict = get_log_elements(elements, with_prints=True, print_method=print_method)
    else:
        result_dict = {name: {'gen_file': []} for name, check_it, object_class in elements}
    for name, check_it, object_class in elements:
        found_objects_of_kind = [o for o in gc.get_objects() if isinstance(o, object_class) and o not in ignored_objects]
        found_objects += found_objects_of_kind
        if not len(found_objects_of_kind) == 0:
            collection_counts = [len(gc.get_referrers(o)) for o in found_objects_of_kind]
            class_types_found = set([o.__class__.__name__ for o in found_objects_of_kind])
            print_method("of object of kind '{0}' have been generated {3} and there are {1} left over instances "
                         "with respective reference numbers of {2} and those types {4}"
                         "".format(object_class, len(found_objects_of_kind), collection_counts,
                                   len(result_dict[name]['gen_file']), class_types_found))
        else:
            print "of object of kind '{0}' have been generated {2} and there are {1} left over instances " \
                  "".format(object_class, len(found_objects_of_kind), len(result_dict[name]['gen_file']))
        if check_it:
            assert len(found_objects_of_kind) == 0
    return found_objects

    # for element_name, with_assert, object_class in elements:
    #     print "finally ", element_name, "__init__:", len(result_dict[element_name]['gen_file']), "__del__:", \
    #         len(result_dict[element_name]['del_file']), "check with assert: ", with_assert
    #     ratio = float(len(result_dict[element_name]['del_file']))/float(len(result_dict[element_name]['gen_file']))
    #     diff = len(result_dict[element_name]['gen_file']) - len(result_dict[element_name]['del_file'])
    #     print "Ratio of destroyed/generated {0} objects is: {1} and diff: {2}".format(element_name, ratio, diff)
    #     if diff > 0:
    #         print "## WARNING ## We have more created then destroyed elements {0} < {1} -> diff {2} of kine: {3}" \
    #               "".format(len(result_dict[element_name]['del_file']), len(result_dict[element_name]['gen_file']),
    #                         diff, element_name)
    #     if with_assert:
    #         assert 0 == diff


def run_model_construction():
    import rafcon.core.singleton
    import rafcon.gui.models.state

    logger, sm_m, state_dict = create_models()
    # root_state = sm_m.root_state

    c_state, state_dict = create_container_state()
    s_m = rafcon.gui.models.state.StateModel(c_state.states['STATE1'])
    rafcon.core.singleton.state_machine_manager.delete_all_state_machines()
    s_m.prepare_destruction()
    testing_utils.wait_for_gui()
    # s_m._reset_property_notification()

    # del logger
    # del sm_m
    # del state_dict
    return s_m


def run_controller_construction(caplog, with_gui):
    from gui.widget.test_states_editor import trigger_state_type_change_tests

    # for a start load one of the type change tests to generate a lot of controllers which also close the GUI
    # from gui.widget.test_states_editor import create_models, MainWindowView, \
    #     MainWindowController, trigger_state_type_change_tests, gtk, threading

    _, sm_m, state_dict = testing_utils.call_gui_callback(create_models)

    print "start 3"

    trigger_state_type_change_tests(with_gui=True)


def patch_core_classes_with_log():

    import rafcon.core.states.state
    import rafcon.core.state_elements.state_element

    global old_state_init, old_state_element_init

    old_state_init = rafcon.core.states.state.State.__init__
    old_state_element_init = rafcon.core.state_elements.state_element.StateElement.__init__

    check_log_files(CORE_FILES)

    def state_init(self, name=None, state_id=None, input_data_ports=None, output_data_ports=None, outcomes=None,
                   parent=None):
        self._patch = None
        self._name = name
        if state_id is None:
            self._state_id = rafcon.core.states.state.state_id_generator()
        else:
            self._state_id = state_id
        self.gen_time_stamp = int(round(time.time() * 1000))
        gen_file = os.path.join(RAFCON_TEMP_PATH_BASE, "{0}_{1}".format("state", GENERATION_LOG_FILE_APPENDIX))
        with open(gen_file, 'a+') as f:
            f.write("RUN {2} of {0} {3} {1}\n".format(self, id(self), "state", self.gen_time_stamp))
        old_state_init(self, name, self._state_id, input_data_ports, output_data_ports, outcomes, parent)

    def state_element_init(self, parent=None):
        self._patch = None
        self.gen_time_stamp = int(round(time.time() * 1000))
        gen_file = os.path.join(RAFCON_TEMP_PATH_BASE, "{0}_{1}".format("state_element", GENERATION_LOG_FILE_APPENDIX))
        with open(gen_file, 'a+') as f:
            f.write("RUN {2} of {0} {3} {1}\n".format(self, id(self), "state_element", self.gen_time_stamp))
        old_state_element_init(self, parent)

    rafcon.core.states.state.State.__init__ = state_init
    rafcon.core.state_elements.state_element.StateElement.__init__ = state_element_init


def un_patch_core_classes_from_log():
    import rafcon.core.states.state
    import rafcon.core.state_elements.state_element

    global old_state_init, old_state_element_init

    rafcon.core.states.state.State.__init__ = old_state_init
    rafcon.core.state_elements.state_element.StateElement.__init__ = old_state_element_init
    remove_log_files(CORE_FILES)


def patch_model_classes_with_log():

    import rafcon.gui.models.abstract_state
    import rafcon.gui.models.state_element

    global old_abstract_state_model_init, old_state_element_model_init

    old_abstract_state_model_init = rafcon.gui.models.abstract_state.AbstractStateModel.__init__
    old_state_element_model_init = rafcon.gui.models.state_element.StateElementModel.__init__

    check_log_files(MODEL_FILES)

    def abstract_state_model_init(self, state, parent=None, meta=None):
        self._patch = None
        self._state = None
        self.__gen_time_stamp = int(round(time.time() * 1000))
        self.__kind = 'abstract_state_model'
        self.__gen_log_file = os.path.join(RAFCON_TEMP_PATH_BASE, '{0}_{1}'.format(self.__kind,
                                                                                   GENERATION_LOG_FILE_APPENDIX))
        with open(self.__gen_log_file, 'a+') as f:
            f.write("RUN {2} of {0} {3} {1}\n".format(super(self.__class__, self).__str__(), id(self),
                                                      self.__kind, self.__gen_time_stamp))
        old_abstract_state_model_init(self, state, parent, meta)

    def state_element_model_init(self, parent, meta=None):
        self._patch = None
        self.parent = parent
        self.__gen_time_stamp = int(round(time.time() * 1000))
        self.__kind = 'state_element_model'
        self.__gen_log_file = os.path.join(RAFCON_TEMP_PATH_BASE, '{0}_{1}'.format(self.__kind,
                                                                                   GENERATION_LOG_FILE_APPENDIX))
        with open(self.__gen_log_file, 'a+') as f:
            f.write("RUN {2} of {0} {3} {1}\n".format(super(self.__class__, self).__str__(), id(self),
                                                  self.__kind, self.__gen_time_stamp))
        old_state_element_model_init(self, parent, meta)

    rafcon.gui.models.abstract_state.AbstractStateModel.__init__ = abstract_state_model_init
    rafcon.gui.models.state_element.StateElementModel.__init__ = state_element_model_init


def un_patch_model_classes_from_log():
    import rafcon.gui.models.abstract_state
    import rafcon.gui.models.state_element

    global old_abstract_state_model_init, old_state_element_model_init

    rafcon.gui.models.abstract_state.AbstractStateModel.__init__ = old_abstract_state_model_init
    rafcon.gui.models.state_element.StateElementModel.__init__ = old_state_element_model_init
    remove_log_files(MODEL_FILES)


def patch_ctrl_classes_with_log():

    # TODO maybe remove this again because the gtkmvc classes are covering this case
    import rafcon.gui.controllers.utils.extended_controller
    global old_extended_controller_init

    old_extended_controller_init = rafcon.gui.controllers.utils.extended_controller.ExtendedController.__init__

    check_log_files(CTRL_FILES)

    def extended_controller_init(self, model, view, spurious=None):
        self._patch = None
        self.__gen_time_stamp = int(round(time.time() * 1000))
        self.__kind = 'extended_controller'
        self.__gen_log_file = os.path.join(RAFCON_TEMP_PATH_BASE, '{0}_{1}'.format(self.__kind,
                                                                                   GENERATION_LOG_FILE_APPENDIX))
        with open(self.__gen_log_file, 'a+') as f:
            f.write("RUN {2} of {0} {3} {1}\n".format(super(self.__class__, self).__str__(), id(self),
                                                      self.__kind, self.__gen_time_stamp))
        if spurious is None:
            old_extended_controller_init(self, model, view)
        else:
            old_extended_controller_init(self, model, view, spurious)

    rafcon.gui.controllers.utils.extended_controller.ExtendedController.__init__ = extended_controller_init


def un_patch_ctrl_classes_from_log():
    import rafcon.gui.controllers.utils.extended_controller
    global old_extended_controller_init
    rafcon.gui.controllers.utils.extended_controller.ExtendedController.__init__ = old_extended_controller_init
    remove_log_files(CTRL_FILES)


def patch_gtkmvc_classes_with_log():

    global old_gtkmvc_view_init, old_gtkmvc_controller_init

    check_log_files(GTKMVC_FILES)

    def gtkmvc_view_init(self, glade=None, top=None, parent=None, builder=None):
        self._patch = None
        self.__gen_time_stamp = int(round(time.time() * 1000))
        self.__kind = 'gtkmvc_view'
        self.__gen_log_file = os.path.join(RAFCON_TEMP_PATH_BASE, '{0}_{1}'.format(self.__kind,
                                                                                   GENERATION_LOG_FILE_APPENDIX))
        with open(self.__gen_log_file, 'a+') as f:
            f.write("RUN {2} of {0} {3} {1}\n".format(super(self.__class__, self).__str__(), id(self),
                                                      self.__kind, self.__gen_time_stamp))
        old_gtkmvc_view_init(self, glade, top, parent, builder)

    def gtkmvc_controller_init(self, model, view, spurious=False, auto_adapt=False):
        self._patch = None
        self.__gen_time_stamp = int(round(time.time() * 1000))
        self.__kind = 'gtkmvc_controller'
        self.__gen_log_file = os.path.join(RAFCON_TEMP_PATH_BASE, '{0}_{1}'.format(self.__kind,
                                                                                   GENERATION_LOG_FILE_APPENDIX))
        with open(self.__gen_log_file, 'a+') as f:
            f.write("RUN {2} of {0} {3} {1}\n".format(super(self.__class__, self).__str__(), id(self),
                                                      self.__kind, self.__gen_time_stamp))
        old_gtkmvc_controller_init(self, model, view, spurious, auto_adapt)

    gtkmvc.View.__init__ = gtkmvc_view_init
    gtkmvc.Controller.__init__ = gtkmvc_controller_init


def un_patch_gtkmvc_classes_from_log():
    global old_gtkmvc_view_init, old_gtkmvc_controller_init
    gtkmvc.View.__init__ = old_gtkmvc_view_init
    gtkmvc.Controller.__init__ = old_gtkmvc_controller_init
    remove_log_files(GTKMVC_FILES)


def print_func(s):
    print s


def test_core_destruct(caplog):
    gc.collect()
    elements = [('state', True, rafcon.core.states.state.State),
                ('state_element', True, rafcon.core.state_elements.state_element.StateElement),
                ]

    already_existing_objects = check_existing_objects_of_kind([(n, False, c) for n, _, c in elements],
                                                              logger.debug, log_file=False)

    testing_utils.initialize_environment_core()

    patch_core_classes_with_log()

    basic_state_machines.test_create_state(caplog)

    basic_state_machines.test_create_container_state(caplog)

    basic_state_machines.test_port_and_outcome_removal(caplog)

    # test
    generate_sm_for_garbage_collector()

    gc.collect()

    check_existing_objects_of_kind(elements, ignored_objects=already_existing_objects)

    un_patch_core_classes_from_log()

    testing_utils.shutdown_environment(caplog=caplog, unpatch_threading=False)


def test_model_and_core_destruct(caplog):
    gc.collect()
    testing_utils.initialize_environment(gui_config={'AUTO_BACKUP_ENABLED': False, 'HISTORY_ENABLED': False},
                                         gui_already_started=False)

    import rafcon.gui.models.abstract_state
    import rafcon.gui.models.state_element

    elements = [('state', True, rafcon.core.states.state.State),
                ('state_element', True, rafcon.core.state_elements.state_element.StateElement),
                ('abstract_state_model', True, rafcon.gui.models.abstract_state.AbstractStateModel),
                ('state_element_model', True, rafcon.gui.models.state_element.StateElementModel),
                ]

    # TODO make this return no existing model of kind State, StateElement, AbstractStateModel, StateElementModel
    # if core test run before
    already_existing_objects = check_existing_objects_of_kind([(n, False, c) for n, check_it, c in elements],
                                                              logger.debug, log_file=False)

    patch_core_classes_with_log()
    patch_model_classes_with_log()

    run_model_construction()

    gc.collect()

    check_existing_objects_of_kind(elements, logger.debug, already_existing_objects)

    un_patch_core_classes_from_log()
    un_patch_model_classes_from_log()

    testing_utils.shutdown_environment(caplog=caplog, unpatch_threading=False)


def _test_model_and_core_destruct_with_gui(caplog):

    testing_utils.run_gui(gui_config={'AUTO_BACKUP_ENABLED': False, 'HISTORY_ENABLED': False})

    import rafcon.gui.models.abstract_state
    import rafcon.gui.models.state_element
    import rafcon.gui.controllers.utils.extended_controller

    patch_core_classes_with_log()
    patch_model_classes_with_log()
    patch_ctrl_classes_with_log()
    try:
        run_controller_construction(caplog, with_gui=True)

        elements = [('state', False, rafcon.core.states.state.State),
                    ('state_element', False, rafcon.core.state_elements.state_element.StateElement),
                    ('abstract_state_model', False, rafcon.gui.models.abstract_state.AbstractStateModel),
                    ('state_element_model', False, rafcon.gui.models.state_element.StateElementModel),
                    ('extended_controller', False, rafcon.gui.controllers.utils.extended_controller.ExtendedController),
                    ]

        check_existing_objects_of_kind(elements)
    except Exception as e:
        raise e
    finally:
        un_patch_core_classes_from_log()
        un_patch_model_classes_from_log()
        un_patch_ctrl_classes_from_log()
        testing_utils.close_gui()
        testing_utils.shutdown_environment(caplog=caplog)


def _test_widget_destruct(caplog):

    # TODO make it fully working and later activate modification history and auto backup
    testing_utils.run_gui(gui_config={'AUTO_BACKUP_ENABLED': False, 'HISTORY_ENABLED': False})

    import rafcon.gui.models.abstract_state
    import rafcon.gui.models.state_element
    import rafcon.gui.controllers.utils.extended_controller

    patch_core_classes_with_log()
    patch_model_classes_with_log()
    patch_ctrl_classes_with_log()
    patch_gtkmvc_classes_with_log()

    try:
        run_controller_construction(caplog, with_gui=True)

        elements = [('state', False, rafcon.core.states.state.State),
                    ('state_element', False, rafcon.core.state_elements.state_element.StateElement),
                    ('abstract_state_model', False, rafcon.gui.models.abstract_state.AbstractStateModel),
                    ('state_element_model', False, rafcon.gui.models.state_element.StateElementModel),
                    ('extended_controller', False, rafcon.gui.controllers.utils.extended_controller.ExtendedController),
                    ('gtkmvc_view', False, gtkmvc.view.View),
                    ('gtkmvc_controller', False, gtkmvc.controller.Controller),
                    ]

        check_existing_objects_of_kind(elements)
    except Exception as e:
        raise e
    finally:
        un_patch_core_classes_from_log()
        un_patch_model_classes_from_log()
        un_patch_ctrl_classes_from_log()
        un_patch_gtkmvc_classes_from_log()
        testing_utils.close_gui()
        testing_utils.shutdown_environment(caplog=caplog)


if __name__ == '__main__':
    # _test_widget_destruct(None)
    # _test_model_and_core_destruct_with_gui(None)
    # test_core_destruct(None)
    # test_model_and_core_destruct(None)
    import pytest
    pytest.main(['-s', __file__])
