#!/usr/bin/env python
import sys
import os
import json
import xml.etree.ElementTree as ElementTree
import re
import http_client

def create_parser():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option(
        "--root",
        dest="root",
        help="Root directory",
        type="string",
    )
    parser.add_option(
        "--force",
        dest="force",
        action="store_true",
        help="Force an update",
    )
    return parser

def load_config(_config_file) :
    import config
    return config

def load_updates(dat) :
    if not os.path.exists(dat) :
        return {}
    with open(dat) as f :
        return json.loads(f.read())

def write_updates(dat, updates) :
    with open(dat, 'w') as f :
        f.write(json.dumps(updates))

def get_current_ip() :
    client = http_client.HttpClient("ipinfo.io", secure=True)
    response = client.get("/json")
    if response['status'] != 200 :
        raise Exception("Unable to retrieve IP info")
    return json.loads(response['body'])['ip']

def xml_tree_to_dict(element) :
    ret = {}
    for child in element :
        ret[child.tag] = child.text
    print(ret)
    return ret

def xml_string_to_dict(payload) :
    # If provider lies about utf-16 but data isn't UTF-16, drop the declaration.
    payload = re.sub(br'^\s*<\?xml[^>]*\?>', b'', payload, count=1)
    return xml_tree_to_dict(ElementTree.fromstring(payload))

def maybe_update_ip(config, updates, ip, force) :
    client = http_client.HttpClient("dynamicdns.park-your-domain.com", secure=True)
    for host in config.hosts :
        if not force and host in updates and updates[host] == ip :
            config.logger.info("Host %s has ip %s.  Skipping." % (host, ip))
            continue
        params = {
            'host': host,
            'domain': config.domain,
            'password': config.password
        }
        response = client.get("/update", params=params)
        if response['status'] != 200 :
            raise Exception("Did not receive 200 on update IP info")
        data = xml_string_to_dict(response['body'])
        if data['ErrCount'] != '0' or data['IP'] != ip or data['Done'] != 'true' :
            raise Exception("Error encountered updating ip %s: %s" % (ip, data))
        config.logger.warning("Updated host %s in domain %s with ip %s" % (host, config.domain, ip))
        updates[host] = ip
    return updates


def main(argv) :
    parser = create_parser()
    (options, args) = parser.parse_args()
    try:
        if not options.root:
            parser.print_help()
            return 1
        config_file = os.sep.join([options.root, "etc", "config.py"])
        if not os.path.isfile(config_file) :
            print("No configuration file found: %s" % config_file)
            parser.print_help()
            return 1
        config = load_config(config_file)
        
        var_dir = os.sep.join([options.root, "var"])
        if not os.path.exists(var_dir) :
            os.mkdir(var_dir)
        dat = os.sep.join([var_dir, "update.dat"])
        updates = maybe_update_ip(config, load_updates(dat), get_current_ip(), options.force)
        write_updates(dat, updates)

        return 0
    except Exception as e:
        import logging
        logging.error(e)
        import traceback
        traceback.print_exc()
        return -1

if __name__ == "__main__" :
    sys.exit(main(sys.argv))
