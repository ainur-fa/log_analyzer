import datetime
import random, gzip
import os
from string import ascii_letters
from random import randint, choice, uniform
from pathlib import Path
from uuid import uuid4
import pytest
import log_analyzer


def rnd_str(lenght):
    return ''.join(choice(ascii_letters) for _ in range(lenght))


def rng_num(lenght):
    return "".join([str(randint(0, 9)) for _ in range(lenght)])


@pytest.fixture
def log_file():
    log = 'testing_log'
    with open(log, 'w') as file:
        for _ in range(100):
            ip = ".".join([str(randint(1, 256)) for _ in range(4)])
            line = f'{ip} {rnd_str(5)} {rnd_str(5)} [{rnd_str(5)}] "GET /index.html HTTP/1.1" ' \
                f'{rng_num(3)} {rng_num(2)} "{rnd_str(5)}" "{rnd_str(7)}" "{uuid4()}" "-" {rnd_str(7)} {round(uniform(0, 5),5)}'
            file.write(f'{line}\n')
            print(line)
    yield log
    os.remove(log)


def test_log_parser(log_file):
    log = Path(log_file)
    result = log_analyzer.log_parser(log)





