# -*- coding: utf-8 -*-
from pathlib import Path
import datetime
import pytest
import log_analyzer
import shutil


@pytest.fixture
def generate_logs():
    test_dir = 'test_dir'
    Path(test_dir).mkdir()
    files_list = []
    for days in range(100, 200, 20):
        new_date = (datetime.date.today() + datetime.timedelta(days=days)).strftime("%Y%m%d")
        log = f'nginx-access-ui.log-{new_date}.gz'
        Path(test_dir).joinpath(log).touch()
        files_list.append(log)
    yield test_dir, files_list
    shutil.rmtree(test_dir)


@pytest.fixture
def opener():
    date = datetime.date.today().strftime("%Y%m%d")
    line = '%s - "GET /index.html HTTP/1.1" 404 42' % ip


def test_last_logfile(generate_logs):
    test_dir, files_list = generate_logs
    last, date = log_analyzer.get_last_log_info(test_dir)
    assert last.name == files_list[-1]
