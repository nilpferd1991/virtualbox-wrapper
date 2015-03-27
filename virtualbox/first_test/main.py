from vboxapi import VirtualBoxManager
import xpcom
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

    def start_machine(self, machine_name, kind):
        # kind in [headless, gui]
        if machine_name not in self.machines:
            raise KeyError

        machine = self.machines[machine_name]

        with self.get_session() as session:
            progress = machine.launchVMProcess(session, kind, "")
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

            try:
                function(mutable_machine)
            except xpcom.Exception as e:
                print e.msg
            mutable_machine.saveSettings()

    def add_storage(self, machine_name, storage_controller_name, kind):
        def add_storage_impl(machine):
            machine.addStorageController(storage_controller_name, kind)

        self.call_machine_function(machine_name, add_storage_impl)

    def attach_device(self, machine_name, hard_disk_name, storage_controller_name, port):
        file_name = self.settings_folder + hard_disk_name + ".vdi"

        new_medium = None

        for media in self.virtual_box_manager.getArray(self.virtual_box, "hardDisks"):
            if media.location == file_name:
                new_medium = media
                if self.virtual_box_manager.getArray(new_medium, "machineIds"):
                    raise NotImplementedError
                new_medium.deleteStorage()

        if not new_medium:
            new_medium = self.virtual_box.createHardDisk("vdi", file_name)

        progress = new_medium.createBaseStorage(10 * 1024*1024*1024, (self.constants.MediumVariant_Standard, ))
        progress.waitForCompletion(-1)

        media = self.virtual_box.openMedium(file_name, self.constants.DeviceType_HardDisk,
                                            self.constants.AccessMode_ReadWrite, True)

        def attach_device_impl(machine):
            machine.attachDevice(storage_controller_name, port, 0, self.constants.DeviceType_HardDisk, media)

        self.call_machine_function(machine_name, attach_device_impl)

    def detach_device(self, machine_name, storage_controller_name, port):
        def detach_device_impl(machine):
            machine.detachDevice(storage_controller_name, port, 0)

        self.call_machine_function(machine_name, detach_device_impl)

    def attach_dvd(self, machine_name, storage_controller_name, port, img_location):
        media = self.virtual_box.openMedium(img_location, self.constants.DeviceType_DVD,
                                            self.constants.AccessMode_ReadOnly, True)

        def attach_device_impl(machine):
            machine.attachDevice(storage_controller_name, port, 0, self.constants.DeviceType_DVD, media)

        self.call_machine_function(machine_name, attach_device_impl)

if __name__ == "__main__":
    machine_handler = MachineHandler()
    machine_handler.detach_device("test", "storage", 1)
    machine_handler.attach_dvd("test", "storage", 1, machine_handler.settings_folder + "debian-7.8.0-i386-CD-1.iso")
    machine_handler.start_machine("test", "gui")

