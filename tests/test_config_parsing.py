# -*- coding: utf-8 -*-
from pathlib import Path
import shutil
from random import randint, choice
from string import ascii_letters
import pytest
import log_analyzer


def rnd_str(lenght):
    return ''.join(choice(ascii_letters) for _ in range(lenght))


def rng_num(lenght):
    return "".join([str(randint(1, 9)) for _ in range(lenght)])


@pytest.fixture
def make_full_config():
    test_dir = 'test_dir'
    Path(test_dir).mkdir()
    config = Path(test_dir).joinpath('config.txt')
    data = {'REPORT_SIZE': rng_num(5),
            'REPORT_DIR': rnd_str(10),
            'LOG_DIR': rnd_str(10),
            'ANALYZER_LOG': rnd_str(10)}
    Path(config).write_text(f"[config]\n"
                            f"REPORT_SIZE = {data['REPORT_SIZE']}\n"
                            f"REPORT_DIR = {data['REPORT_DIR']}\n"
                            f"LOG_DIR = {data['LOG_DIR']}\n"
                            f"ANALYZER_LOG = {data['ANALYZER_LOG']}""")
    yield config.resolve(), data
    shutil.rmtree(test_dir)


@pytest.fixture
def make_mixed_config():
    test_dir = 'test_dir'
    Path(test_dir).mkdir()
    config = Path(test_dir).joinpath('config.txt')
    data = {'REPORT_SIZE': rng_num(5),
            'ANALYZER_LOG': rnd_str(10)}
    Path(config).write_text(f"[config]\n"
                            f"REPORT_SIZE = {data['REPORT_SIZE']}\n"
                            f"ANALYZER_LOG = {data['ANALYZER_LOG']}\n")
    yield config.resolve(), data
    shutil.rmtree(test_dir)


def test_parsing_full_config(make_full_config):
    config, data = make_full_config
    report_size, report_dir, log_dir, script_logfile = log_analyzer.parse_config(config)
    assert str(report_size) == data['REPORT_SIZE']
    assert report_dir == data['REPORT_DIR']
    assert log_dir == data['LOG_DIR']
    assert script_logfile == data['ANALYZER_LOG']


def test_parsing_mixed_config(make_mixed_config):
    config, data = make_mixed_config
    report_size, report_dir, log_dir, script_logfile = log_analyzer.parse_config(config)
    assert str(report_size) == data['REPORT_SIZE']
    assert script_logfile == data['ANALYZER_LOG']
    assert report_dir == log_analyzer.config['REPORT_DIR']
    assert log_dir == log_analyzer.config['LOG_DIR']
