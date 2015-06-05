#!/usr/bin/env python
# encoding: utf-8

import time
import json
import threading

from vagrant import Vagrant
from flask import Flask
app = Flask(__name__)

vagrant = Vagrant(quiet_stdout=False, quiet_stderr=False)

checked_out = None
minimum_standby_vms = 2
checked_in = []


def get_alive_vms():
    return [x for x in vagrant.status() if x.state == 'running' and
            x.name not in checked_in]


def get_dead_vms():
    return [x for x in vagrant.status() if x.state != 'running']


@app.route("/")
def hello():
    return "Hello World!"


def start(vm):
    print "Starting {}...".format(vm)
    vagrant.up(vm_name=vm, provision=True)
    print "{} started and ready for testing!".format(vm)


def stop(vm):
    print "Stopping {}...".format(vm)
    vagrant.destroy(vm)
    print "{} destroyed.".format(vm)


def restart(vm):
    stop(vm)
    start(vm)


@app.route("/vm/<vm_type>", methods=["POST", "GET"])
def get_vm(vm_type=None):
    vm = checkout_vm()
    return json.dumps({
        "ok": True,
        vm_type: {
            "hostname": vm['box'],
        }
    })


@app.route("/checkout")
def checkout():
    return json.dumps(checkout_vm())


def checkout_vm():
    global checked_out
    vms = [x for x in get_alive_vms() if x.name != checked_out]
    if checked_out:
        checked_in.append(checked_out)
    if vms:
        checked_out = vms[0].name
        return {
            'box': checked_out,
            'error': False,
            'ready': len(vms) - 1,
            'rebooting': len(checked_in),
            'testing': checked_out,
        }
    return {
        'box': None,
        'error': True,
        'ready': len(vms) - 1,
        'rebooting': len(checked_in),
        'testing': checked_out,
    }


class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self):
        super(StoppableThread, self).__init__()
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()


class RestartWorker(StoppableThread):

    def run(self):
        global checked_in
        while not self.stopped():
            vms = [x for x in get_alive_vms() if x.name != checked_out]
            if len(checked_in) > 0:
                vm = checked_in[0]
                stop(vm)
                checked_in = checked_in[1:]
            elif len(vms) < minimum_standby_vms and len(get_dead_vms()) > 0:
                for x in get_dead_vms()[0:(minimum_standby_vms - len(vms))]:
                    start(x.name)
            else:
                time.sleep(5)

if __name__ == "__main__":
    print(vagrant.status())
    restart_thread = RestartWorker()
    restart_thread.start()
    app.run()
    print "done"
    restart_thread.stop()
