from rafcon.core.singleton import state_machine_execution_engine as smee


def execute(self, inputs, outputs, gvm):
    self.logger.info("Stopping state machine")
    smee.stop()
    return "success"
