#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import json
from string import Template
from statistics import median
import gzip
import argparse
from collections import Counter
import configparser
from pathlib import Path
from logging import *

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}


def init_config():
    """Init configuration"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", metavar='<path>', dest='config', help="path to config file", default='settings.ini')
    conf_file = parser.parse_args().config

    if not Path(conf_file).exists():
        raise Exception('Config file not found')

    return conf_file


def parse_config(conf_file):
    """Parsig configuration file"""
    try:
        cp = configparser.ConfigParser()
        cp.read(conf_file)
        cp_section = cp['config']
        report_size = int(cp_section.get('REPORT_SIZE', config.get('REPORT_SIZE')))
        report_dir = cp_section.get('REPORT_DIR', config.get('REPORT_DIR'))
        log_dir = cp_section.get('LOG_DIR', config.get('LOG_DIR'))
        script_logfile = cp_section.get('ANALYZER_LOG', config.get('ANALYZER_LOG'))
        return report_size, report_dir, log_dir, script_logfile
    except:
        raise Exception('Config file parsing error')


def get_last_log_info(log_dir):
    """Path and date for last log"""
    files = Path(log_dir).iterdir()
    nginx_logs = {file: re.search(r'\d{8}', file.name).group() for file in files
                  if re.match(r'nginx-access-ui.log-(\d{8})($|.gz$)', file.name)}
    if not nginx_logs:
        return None, None
    last_log = max(nginx_logs, key=lambda x: int(nginx_logs.get(x)))
    date_string = nginx_logs[last_log]
    created_date = '.'.join([date_string[:4], date_string[4:6], date_string[6:]])
    info(f'Found last log file: {last_log}')
    return last_log, created_date


def lines_from_log(path):
    """Opened log file"""
    if path.suffix == '.gz':
        opener = gzip.open(path, 'rt', encoding='utf-8')
    else:
        opener = open(path, 'rt', encoding='utf-8')
    yield from opener


def log_parser(log_file):
    """Log parser"""
    pattern = re.compile(r'(\d+\.\d+\.\d+\.\d+) (.+) (.+) \[(.+)\] "(.+) (?P<request>.+) (.+)" '
                         r'(\d+) (\d+) \"(.+)\" "(.+)" "(.+)" "(.+)" (.+) (?P<time>.+)')
    logpat = re.compile(pattern)
    raw_lines = lines_from_log(log_file)
    groups = (logpat.match(line) for line in raw_lines)
    logs = ((g.group('request'), float(g.group('time'))) if g else (None, None) for g in groups)
    return logs


def consolidate(parsed_log):
    """Consolidate requests"""
    parsed_requests = {}
    all_requests_counter = 0
    total_time = 0
    not_parsed = 0

    for url, time in parsed_log:
        if not url:
            not_parsed += 1
            continue
        if not parsed_requests.get(url):
            parsed_requests[url] = [time]
        else:
            parsed_requests[url].append(time)
        all_requests_counter += 1
        total_time += time

    not_parsed_limit = 5
    not_parsed_perc = (not_parsed * 100)/all_requests_counter
    if not_parsed_perc > not_parsed_limit:
        error(f'most of the log could not be parsed ( {round(not_parsed_perc, 5)} % )')
        exit(1)

    return parsed_requests, all_requests_counter, total_time


def calculate(parsed_requests, all_requests_counter, total_time):
    """Calculate statistics"""
    result_table = []

    for url, times in parsed_requests.items():
        count = len(times)
        time_sum = sum(times)
        count_pers = round(count * 100 / all_requests_counter, 3)
        time_perc = round(time_sum * 100 / total_time, 3)
        time_avg = round(time_sum / count, 3)
        time_max = round(max(times), 3)
        time_med = round(median(times), 3)
        time_sum = round(time_sum, 3)

        result_table.append(
            {'url': url, 'count': count, 'count_pers': count_pers, 'time_sum': time_sum, 'time_perc': time_perc,
             'time_avg': time_avg, 'time_max': time_max, 'time_med': time_med})

    return result_table


def selection(report, size):
    """N url's with max time_sum"""
    info(f"The report will display information about {size} url's")
    c = Counter({x: sum(y) for x, y in report.items()})
    most_common = c.most_common(size)
    result = {k: report[k] for k, v in most_common}
    return result


def make_report(data, report):
    """Write results to html"""
    template = Template(Path('report.html').read_text(encoding='utf-8'))
    content = template.safe_substitute(table_json=json.dumps(data))
    Path(report).write_text(content, encoding='utf-8')
    info('Report generated success')


def main():
    conf = init_config()
    args = parse_config(conf)
    report_size, report_dir, log_dir, script_logfile = args

    basicConfig(format=u'[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S',
                level=INFO, filename=script_logfile)

    info('Starting')
    log_file, date = get_last_log_info(log_dir)
    if not log_file:
        info(f'Not found log files in {log_dir}')
        exit(1)

    report = Path(report_dir).joinpath(f'report-{date}.html')
    if report.exists():
        info(f'Report for last log already exists: "{report}", nothing to do')
        exit()

    parsed_log = log_parser(log_file)
    urls_statistics, urls_counter, total_time = consolidate(parsed_log)
    urls_statistics = selection(urls_statistics, report_size)
    result = calculate(urls_statistics, urls_counter, total_time)
    make_report(result, report)
    info('Done')


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        info("Terminated by user ...")
    except Exception as e:
        exception('Fatal error')
