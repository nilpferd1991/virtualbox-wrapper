from vboxapi import VirtualBoxManager
import time

# Some general remarks:
# There is the VirtualBoxManager with the vbox and there is a machine object
# for every box there is on the computer.
# A machine can be started. For this we need the current session object.
#

class MachineHandler:
    settings_folder = "/media/Daten/Projects/BlueYonder/virtualbox/first_test/test/"

    def __init__(self):
        self.virtual_box_manager = VirtualBoxManager()
        self.virtual_box = self.virtual_box_manager.vbox

        self.machines = dict()

        self.get_machines()

    def get_machines(self):
        for machine in self.virtual_box_manager.getArray(self.virtual_box, "machines"):
            self.machines[machine.name] = machine

    def create_new_machine(self, machine_name, kind):
        if kind not in ["Linux", "MacOS"]:
            raise NotImplementedError

        if machine_name in self.machines:
            raise KeyError

        new_machine = self.virtual_box.createMachine(self.settings_folder + str(machine_name) + ".vbox",
                                                     machine_name, [], kind, "")
        new_machine.saveSettings()
        self.virtual_box.registerMachine(new_machine)
        self.machines[machine_name] = new_machine

    def start_machine(self, machine_name):
        if machine_name not in self.machines:
            raise KeyError

        machine = self.machines[machine_name]
        session = self.virtual_box_manager.getSessionObject(self.virtual_box)
        progress = machine.launchVMProcess(session, "headless", "")
        progress.waitForCompletion(-1)
        self.virtual_box_manager.closeMachineSession(session)

    def remove_machine(self, machine_name):
        if machine_name not in self.machines:
            raise KeyError

        machine = self.virtual_box.findMachine(machine_name)
        machine = machine.unregister(self.virtual_box_manager.constants.CleanupMode_Full)
        if machine:
            machine.deleteSettings()

        del self.machines[machine_name]

    def set_machine_property(self, machine_name, **kwargs):
        if machine_name not in self.machines:
            raise KeyError

        machine = self.machines[machine_name]
        session = self.virtual_box_manager.getSessionObject(self.virtual_box)
        machine.lockMachine(session, self.virtual_box_manager.constants.LockType_Shared)
        mutable_machine = session.machine
        for var in kwargs:
            mutable_machine.__setattr__(var, kwargs[var])

        mutable_machine.saveSettings()

    def get_machine_property(self, machine_name, property):
        if machine_name not in self.machines:
            raise KeyError

        machine = self.machines[machine_name]
        return machine.__getattr__(property)


if __name__ == "__main__":
    machine_handler = MachineHandler()
    #machine_handler.create_new_machine("test", "Linux")
    #machine_handler.start_machine("test")
    #machine_handler.remove_machine("test")

    test_machine = machine_handler.machines["test"]