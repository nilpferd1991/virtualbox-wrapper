from vboxapi import VirtualBoxManager
import time

virtual_box_manager = VirtualBoxManager()
virtual_box = virtual_box_manager.vbox

def create_new_machine(name, kind):
    if kind not in ["Linux", "MacOS"]:
        raise NotImplementedError
    new_machine = virtual_box.createMachine("/media/Daten/Projects/BlueYonder/virtualbox/first_test/test/" + str(name) + ".vbox",
                                            name, [], kind, "")
    new_machine.saveSettings()
    virtual_box.registerMachine(new_machine)

def start_machine(machine_name):
    machine = virtual_box.findMachine(machine_name)
    session = virtual_box_manager.getSessionObject(virtual_box)
    progress = machine.launchVMProcess(session, "gui", "")
    progress.waitForCompletion(-1)
    #time.sleep(10)
    virtual_box_manager.closeMachineSession(session)

def remove_machine(machine_name):
    machine = virtual_box.findMachine(machine_name)
    machine = machine.unregister(virtual_box_manager.constants.CleanupMode_Full)
    if machine:
        machine.deleteSettings()

for m in virtual_box_manager.getArray(virtual_box, "machines"):
    print "Machine %s logs in %s" %(m.name, m.logFolder)

#create_new_machine("test", "Linux")
#start_machine("test")
remove_machine("test")