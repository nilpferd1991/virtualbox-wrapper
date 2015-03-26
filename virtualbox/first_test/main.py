from vboxapi import VirtualBoxManager
from contextlib import contextmanager
import time

# Some general remarks:
# There is the VirtualBoxManager with the vbox and there is a machine object
# for every box there is on the computer.
# A machine can be started. For this we need the current session object.
# We also need this to lock the machine and change its parameters.
# Session objects represent a client process (and are a process by themselves whereas the machines life
# in the main process)

# The important part is the IVirtualBox. To do anything useful, we need this object.
# It is implemented as a singleton.

class MachineHandler:
    settings_folder = "/media/Daten/Projects/BlueYonder/virtualbox/first_test/test/"

    def __init__(self):
        self.virtual_box_manager = VirtualBoxManager()
        self.virtual_box = self.virtual_box_manager.vbox
        self.constants = self.virtual_box_manager.constants
        self.machines = dict()
        self.get_machines()

    @contextmanager
    def get_session(self, machine=None):
        session = self.virtual_box_manager.getSessionObject(self.virtual_box)
        if machine is not None:
            machine.lockMachine(session, self.constants.LockType_Shared)
            if session.state != self.constants.SessionState_Locked:
                raise Exception

        try:
            yield session
        finally:
            if session.state == self.constants.SessionState_Locked:
                session.unlockMachine()
            else:
                print "not locked!"

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

        with self.get_session() as session:
            progress = machine.launchVMProcess(session, "headless", "")
            # Wait until startup has completed
            progress.waitForCompletion(-1)
            # when startup is completed, the running machine lives in its own session object
            # so we can reuse this session. For this we have to give away the lock.

    def remove_machine(self, machine_name):
        if machine_name not in self.machines:
            raise KeyError

        machine = self.machines[machine_name]
        media = machine.unregister(self.constants.CleanupMode_Full)
        machine.deleteConfig(media)

        del self.machines[machine_name]

    def set_machine_property(self, machine_name, **kwargs):
        if machine_name not in self.machines:
            raise KeyError

        machine = self.machines[machine_name]

        with self.get_session(machine) as session:
            mutable_machine = session.machine
            for var in kwargs:
                mutable_machine.__setattr__(var, kwargs[var])

            mutable_machine.saveSettings()

    def get_machine_property(self, machine_name, property):
        if machine_name not in self.machines:
            raise KeyError

        machine = self.machines[machine_name]
        return machine.__getattr__(property)

    def stop_machine(self, machine_name):
        if machine_name not in self.machines:
            raise KeyError

        machine = self.machines[machine_name]

        with self.get_session(machine) as session:
            console = session.console
            progress = console.powerDown()
            progress.waitForCompletion(-1)
            time.sleep(0.001)

    def call_machine_function(self, machine_name, function):
        if machine_name not in self.machines:
            raise KeyError

        machine = self.machines[machine_name]

        with self.get_session(machine) as session:
            mutable_machine = session.machine
            function(mutable_machine)
            mutable_machine.saveSettings()


if __name__ == "__main__":
    machine_handler = MachineHandler()
    #machine_handler.create_new_machine("test", "Linux")
    #machine_handler.remove_machine("test")

    machine_handler.call_machine_function("test", lambda machine:
        machine.addStorageController("storage", machine_handler.constants.StorageBus_SATA))