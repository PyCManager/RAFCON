def execute(self, inputs, outputs, external_modules):
    print "Hello world: Execute"
    print inputs
    print outputs
    outputs["MyFirstDataOutputPort"] = 10.0
    self.print_state_information()
    return 3
