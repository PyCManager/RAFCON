
import gtk

from awesome_tool.mvc.controllers.extended_controller import ExtendedController
from awesome_tool.mvc.controllers import StateOverviewController, SourceEditorController, \
    DataPortListController, ScopedVariableListController, StateOutcomesEditorController, LinkageOverviewController

from awesome_tool.mvc.controllers.state_transitions import StateTransitionsEditorController
from awesome_tool.mvc.controllers.state_data_flows import StateDataFlowsEditorController
from awesome_tool.mvc.models import ContainerStateModel
from awesome_tool.utils import constants
from awesome_tool.utils import log
logger = log.get_logger(__name__)


class StateEditorController(ExtendedController):
    """Controller handles the organization of the Logic-Data oriented State-Editor.
    Widgets concerning logic flow (outcomes and transitions) are grouped in the Logic Linkage expander.
    Widgets concerning data flow (data-ports and data-flows) are grouped in the data linkage expander.
    """

    icons = {
        "Source":           constants.ICON_SOURCE,
        "Data Linkage":     constants.ICON_DLINK,
        "Logical Linkage":  constants.ICON_LLINK,
        "Linkage Overview": constants.ICON_OVERV,
        "Description":      constants.ICON_DESC
    }

    def __init__(self, model, view):
        """Constructor
        """
        ExtendedController.__init__(self, model, view)

        self.add_controller('properties_ctrl', StateOverviewController(model, view['properties_view']))

        self.add_controller('inputs_ctrl', DataPortListController(model, view['inputs_view'], "input"))
        self.add_controller('outputs_ctrl', DataPortListController(model, view['outputs_view'], "output"))
        self.add_controller('scoped_ctrl', ScopedVariableListController(model, view['scopes_view']))
        self.add_controller('outcomes_ctrl', StateOutcomesEditorController(model, view['outcomes_view']))

        self.add_controller('source_ctrl', SourceEditorController(model, view['source_view']))
        self.add_controller('transitions_ctrl', StateTransitionsEditorController(model, view['transitions_view']))
        self.add_controller('data_flows_ctrl', StateDataFlowsEditorController(model, view['data_flows_view']))

        self.add_controller('linkage_overview_ctrl', LinkageOverviewController(model, view['linkage_overview']))

        view['inputs_view'].show()
        view['outputs_view'].show()
        view['scopes_view'].show()
        view['outcomes_view'].show()
        view['source_view'].show()
        view['transitions_view'].show()
        view['data_flows_view'].show()

        view['description_text_view'].connect('focus-out-event', self.change_description)
        view['description_text_view'].connect('size-allocate', self.scroll_to_bottom)

        for i in range(view["main_notebook_1"].get_n_pages()):
            child = view["main_notebook_1"].get_nth_page(i)
            tab_label = view["main_notebook_1"].get_tab_label(child)
            tab_label_text = tab_label.get_text()
            view["main_notebook_1"].set_tab_label(child, self.create_tab_header_label(tab_label_text))
            view["main_notebook_1"].set_tab_reorderable(child, True)
            view["main_notebook_1"].set_tab_detachable(child, True)

        for i in range(view["main_notebook_2"].get_n_pages()):
            child = view["main_notebook_2"].get_nth_page(i)
            tab_label = view["main_notebook_2"].get_tab_label(child)
            tab_label_text = tab_label.get_text()
            view["main_notebook_2"].set_tab_label(child, self.create_tab_header_label(tab_label_text))
            view["main_notebook_2"].set_tab_reorderable(child, True)
            view["main_notebook_2"].set_tab_detachable(child, True)

        if isinstance(model, ContainerStateModel):
            self.get_controller('scoped_ctrl').reload_scoped_variables_list_store()

    def create_tab_header_label(self, tab_name):
        tooltip_event_box = gtk.EventBox()
        tooltip_event_box.set_tooltip_text(tab_name)
        tab_label = gtk.Label()
        tab_label.set_markup('<span font_desc="%s %s">&#x%s;</span>' %
                             (constants.ICON_FONT,
                              constants.FONT_SIZE_BIG,
                              self.icons[tab_name]))
        tab_label.show()
        tooltip_event_box.add(tab_label)
        tooltip_event_box.set_visible_window(False)
        tooltip_event_box.show()
        return tooltip_event_box

    def register_view(self, view):
        """Called when the View was registered

        Can be used e.g. to connect signals. Here, the destroy signal is connected to close the application
        """
        view['new_input_port_button'].connect('clicked',
            self.get_controller('inputs_ctrl').on_new_port_button_clicked)
        view['new_output_port_button'].connect('clicked',
            self.get_controller('outputs_ctrl').on_new_port_button_clicked)
        view['new_scoped_variable_button'].connect('clicked',
            self.get_controller('scoped_ctrl').on_new_scoped_variable_button_clicked)

        view['delete_input_port_button'].connect('clicked',
            self.get_controller('inputs_ctrl').on_delete_port_button_clicked)
        view['delete_output_port_button'].connect('clicked',
            self.get_controller('outputs_ctrl').on_delete_port_button_clicked)
        view['delete_scoped_variable_button'].connect('clicked',
            self.get_controller('scoped_ctrl').on_delete_scoped_variable_button_clicked)

        if self.model.state.description is not None:
            view['description_text_view'].get_buffer().set_text(self.model.state.description)

    def register_adapters(self):
        """Adapters should be registered in this method call

        Each property of the state should have its own adapter, connecting a label in the View with the attribute of
        the State.
        """
        #self.adapt(self.__state_property_adapter("name", "input_name"))

    def scroll_to_bottom(self, widget, data=None):
        scroller = self.view['description_scroller']
        adj = scroller.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())

    def change_description(self, textview, otherwidget):
        tbuffer = textview.get_buffer()
        entry_text = tbuffer.get_text(tbuffer.get_start_iter(), tbuffer.get_end_iter())

        if len(entry_text) > 0:
            logger.debug("State %s changed description from '%s' to: '%s'\n" % (self.model.state.state_id,
                                                                                self.model.state.description, entry_text))
            self.model.state.description = entry_text
            self.view['description_text_view'].get_buffer().set_text(self.model.state.description)
