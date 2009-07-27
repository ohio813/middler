#!/usr/bin/env python
import libmiddler as ml
import signal
import sys,os
import threading

# Add The Middler's module namespace to the path.
sys.path.append(os.curdir + os.sep)

# Make a dirty global variable to hold child pids that we should remember to clean up
ml.child_pids_to_shutdown = []

############################################################################################################
# Parse command-line options                                                                                                                                                             #
############################################################################################################

def parseCommandLineFlags():

    from optparse import OptionParser
    parser = OptionParser(usage="%prog [-p port] ", version="%prog 1.0")

    parser.add_option("-p", "--port", dest="port",
                                    help="HTTP should listen on this port",default="80")
    parser.add_option("-A", "--arpspoof_off", action="store_true", dest="toggle_arpspoof_off", default=False,
                                    help="turn off ARP spoofing, so The Middler doesn't broadcast ARP replies claiming the router's IP address")
    
    (options,args)=parser.parse_args()

    return (options,args)

###################################
# Main non-class Code starts here.
###################################


# First, parse out command-line options

if __name__ == '__main__':


    ##############################
    # Parse command-line options #
    ##############################

    (options,args) = parseCommandLineFlags()

    ml.toggle_arpspoof_off = options.toggle_arpspoof_off
    ml.port = int(options.port)

    ml.hostname = "0.0.0.0"

    ###################
    # Signal handling #
    ###################

    # Define a signal handler so we can make sure we close the log files.
    def handle_signal_term(signum,frame):

        # TODO-High: cleanly deactivate ARP spoofing

        # Deactivate any ARP spoofing
        # deactivate_arpspoof()

        # Turn off the firewalling/routing
        ml.jjlog.debug("Deactivating routing/firewall-based packet fu.")
        ml.traffic_capture.stop()

        # Close up the log files.
        ml.jjlog.debug("Closing log files.\n")
        ml.jjlog.stop()

        # Kill off any children we've left around, generally from ARP spoofing.
        for pid in ml.child_pids_to_shutdown:
            print "Killing off PID %d\n" % pid
            os.kill(pid,9)

        # Wait for any processes we started to finish
        for pid in ml.child_pids_to_shutdown:
            os.waitpid(pid,0)

        exit(0)


    # Catch normal kill command
    signal.signal(signal.SIGTERM, handle_signal_term)
    # Catch Ctrl-C
    signal.signal(signal.SIGINT, handle_signal_term)

    # Initialize Logging - open files for writing and create thread locks.
    ml.jjlog.initialize()

    # Start up the firewalling and routing to    send traffic to us.
    #from ml.Middler_Firewall import startRedirection,stopRedirection
    ml.traffic_capture.start()

    # Activate the DNS spoofing?
    #os.spawnl(os.P_NOWAIT,r"/Users/jay/BFF_DNS.pl","")

    #
    # Activate the ARP spoofing.
    #

    #
    # The middle_the_net module contains functions to target and MitM the LAN
    #
    # First, define what interfaces we need to ARPspoof.
    #
    #if ml.toggle_arpspoof:

        # Now, launch a thread/process to ARPspoof the network.
        # We wrote this as a thread, but we might write it as a process later.
        # Doing the latter requires working with shared memory and command channels.
        #ml.set_up_arpspoofing(target_host="ALL",interface="defaultroute",impersonated_host="defaultrouter")

    # Start up the multi-threaded proxy
    ml.jjlog.debug("Activating proxy\n")

    import libmiddler.proxies
    import libmiddler.proxies.http
    import libmiddler.proxies.http.http_proxy

    server = libmiddler.proxies.http.http_proxy.ThreadedTCPServer((ml.hostname,ml.port), libmiddler.proxies.http.http_proxy.MiddlerHTTPProxy)
    print("Middler Started and Proxying")
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.setDaemon(True)
    server_thread.start()
    print "Server loop running in thread:", server_thread.getName()

    while True:
        pass
    # We shouldn't ever reach this line, since the signal handler should do this.
    ml.jjlog.stop()
