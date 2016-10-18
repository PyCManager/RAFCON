from gtkmvc import Observable
from rafcon.mvc.models import AbstractStateModel, TransitionModel, DataFlowModel, DataPortModel, OutcomeModel, \
    ScopedVariableModel
from rafcon.statemachine.state_elements.data_port import InputDataPort, OutputDataPort
from rafcon.utils import log

logger = log.get_logger(__name__)


def reduce_to_parent_states(models):
    models_to_remove = []
    for model in models:
        parent_m = model.parent
        while parent_m is not None and model is AbstractStateModel:
            if parent_m in models:
                models_to_remove.append(model)
                break
            parent_m = parent_m.parent
    for model in models_to_remove:
        models.remove(model)
    return models


class Selection(Observable):
    """This class contains the selected item (States, Transitions and Data Flows) of a state_machine

    :param set __selected: The state machine elements selected
    """
    __selected = None
    _input_data_ports = None
    _output_data_ports = None
    _scoped_variables = None
    _outcomes = None
    _data_flows = None
    _transitions = None
    _states = None

    def __init__(self):
        Observable.__init__(self)

        self.__selected = set()
        self.input_data_ports = []
        self.output_data_ports = []
        self.outcomes = []
        self.data_flows = []
        self.transitions = []
        self.states = []
        self.scoped_variables = []
        # flag to enable new method to use list updates -> cause additional but unique notifications -> support for better code
        self.__with_updates = True

    def __str__(self):
        return_string = "Selected: "
        for item in self.__selected:
            return_string = "%s, %s" % (return_string, str(item))
        return return_string

    @Observable.observed
    def add(self, item):
        self.__selected.add(item)
        self.__selected = reduce_to_parent_states(self.__selected)
        if self.__with_updates: self.__update()

    @Observable.observed
    def remove(self, item):
        if item in self.__selected:
            self.__selected.remove(item)
            if self.__with_updates: self.__update()
        # else:
        #     logger.warning("Can not remove item not in selection: {0}".format(item))

    @Observable.observed
    def append(self, selection):
        self.__selected.update(selection)
        self.__selected = reduce_to_parent_states(self.__selected)
        if self.__with_updates: self.__update()

    @Observable.observed
    def set(self, selection):
        self.__selected.clear()
        # Do not add None values to selection
        if not selection:
            return
        if not isinstance(selection, list):
            selection = [selection]
        else:
            selection = reduce_to_parent_states(selection)
        self.__selected.update(selection)
        if self.__with_updates: self.__update()

    def __iter__(self):
        return self.__selected.__iter__()

    def __len__(self):
        return len(self.__selected)

    def __contains__(self, item):
        return item in self.__selected

    def __getitem__(self, key):
        return [s for s in self.__selected][key]

    def __update(self):
        if not self._states == self.get_states():
            self.states = self.get_states()
        if not self._transitions == self.get_transitions():
            self.transitions = self.get_transitions()
        if not self._data_flows == self.get_data_flows():
            self.data_flows = self.get_data_flows()
        if not self._input_data_ports == self.get_input_data_ports():
            self.input_data_ports = self.get_input_data_ports()
        if not self._output_data_ports == self.get_output_data_ports():
            self.output_data_ports = self.get_output_data_ports()
        if not self._outcomes == self.get_outcomes():
            self.outcomes = self.get_outcomes()

    @property
    def states(self):
        return self._states

    @states.setter
    @Observable.observed
    def states(self, model_list):
        assert all([isinstance(m, AbstractStateModel) for m in model_list])
        assert self.get_states() == model_list
        self._states = model_list

    @property
    def transitions(self):
        return self._transitions

    @transitions.setter
    @Observable.observed
    def transitions(self, model_list):
        assert all([isinstance(m, TransitionModel) for m in model_list])
        assert self.get_transitions() == model_list
        self._transitions = model_list

    @property
    def data_flows(self):
        return self._data_flows

    @data_flows.setter
    @Observable.observed
    def data_flows(self, model_list):
        assert all([isinstance(m, DataPortModel) for m in model_list])
        assert self.get_data_flows() == model_list
        self._data_flows = model_list

    @property
    def outcomes(self):
        return self._outcomes

    @outcomes.setter
    @Observable.observed
    def outcomes(self, model_list):
        assert all([isinstance(m, OutcomeModel) for m in model_list])
        assert self.get_outcomes() == model_list
        self._outcomes = model_list

    @property
    def input_data_ports(self):
        return self._input_data_ports

    @input_data_ports.setter
    @Observable.observed
    def input_data_ports(self, model_list):
        assert all([isinstance(m, DataPortModel) and isinstance(m.data_port, InputDataPort) for m in model_list])
        assert self.get_input_data_ports() == model_list
        self._input_data_ports = model_list

    @property
    def output_data_ports(self):
        return self._output_data_ports

    @output_data_ports.setter
    @Observable.observed
    def output_data_ports(self, model_list):
        assert all([isinstance(m, DataPortModel) and isinstance(m.data_port, OutputDataPort)  for m in model_list])
        assert self.get_output_data_ports() == model_list
        self._output_data_ports = model_list

    @property
    def scoped_variables(self):
        return self._scoped_variables

    @scoped_variables.setter
    @Observable.observed
    def scoped_variables(self, model_list):
        """Observable selected scoped variable setter that is only usable by the class it self."""
        assert all([isinstance(m, ScopedVariableModel) for m in model_list])
        assert self.get_scoped_variables() == model_list
        self._scoped_variables = model_list

    def is_selected(self, item):
        if item is None:
            return len(self.__selected) == 0
        return item in self.__selected

    def get_all(self):
        return [s for s in self.__selected]

    def get_states(self):
        return [s for s in self.__selected if isinstance(s, AbstractStateModel)]

    def get_num_states(self):
        return sum((1 for s in self.__selected if isinstance(s, AbstractStateModel)))

    def get_transitions(self):
        return [s for s in self.__selected if isinstance(s, TransitionModel)]

    def get_num_transitions(self):
        return sum((1 for s in self.__selected if isinstance(s, TransitionModel)))

    def get_data_flows(self):
        return [s for s in self.__selected if isinstance(s, DataFlowModel)]

    def get_outcomes(self):
        return [s for s in self.__selected if isinstance(s, OutcomeModel)]

    def get_num_outcomes(self):
        return sum((1 for s in self.__selected if isinstance(s, OutcomeModel)))

    def get_num_data_flows(self):
        return sum((1 for s in self.__selected if isinstance(s, DataFlowModel)))

    def get_input_data_ports(self):
        return [s for s in self.__selected if isinstance(s, DataPortModel) and isinstance(s.data_port, InputDataPort)]

    def get_num_input_data_ports(self):
        return sum((1 for s in self.__selected if isinstance(s, DataPortModel) and isinstance(s.data_port, InputDataPort)))

    def get_output_data_ports(self):
        return [s for s in self.__selected if isinstance(s, DataPortModel) and isinstance(s.data_port, OutputDataPort)]

    def get_num_output_data_ports(self):
        return sum((1 for s in self.__selected if isinstance(s, DataPortModel) and isinstance(s.data_port, OutputDataPort)))

    def get_scoped_variables(self):
        return [s for s in self.__selected if isinstance(s, ScopedVariableModel)]

    def get_num_scoped_variables(self):
        return sum((1 for s in self.__selected if isinstance(s, ScopedVariableModel)))

    @Observable.observed
    def clear(self):
        self.set([])
        if self.__with_updates: self.__update()

    def get_selected_state(self):
        selected_states = self.get_states()
        if not selected_states:
            return None
        else:
            return selected_states[0]
