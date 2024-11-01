#
# This file is part of the BarcodeRelay distribution (https://github.com/SirAfino/barcode-relay).
# Copyright (c) 2024 Gabriele Serafino.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from queue import Queue
from time import sleep
from redis import Redis
from .sender import Sender

class RedisStreamSender(Sender):
    """Sender for Redis Stream"""
    _redis: Redis
    _stream_name: str

    def __init__(
        self,
        relay_name: str,
        queue: Queue,
        redis_host: str,
        redis_port: int,
        redis_username: str,
        redis_password: str,
        redis_stream: str,
        polling_ms: int = 1000
    ):
        super().__init__(relay_name, queue, polling_ms)
        self._redis = Redis(
            host=redis_host,
            port=redis_port,
            username=redis_username,
            password=redis_password,
            decode_responses=True
        )
        self._stream_name = redis_stream

    def _send(self, device: str, code: str, ts):
        sent = False
        data = { 'relay': self._relay_name, 'device': device, 'code': code, 'ts': ts }

        while self._run and not sent:
            try:
                self._redis.xadd(self._stream_name, data)
                sent = True
            except Exception as e:
                seconds = 5
                self._logger.info(
                    "Error while sending message, retry in %ss...", seconds,
                    extra={ 'component': 'SENDER' }
                )
                self._logger.info(e)
                sleep(seconds)

    def stop(self):
        super().stop()
        if self._redis:
            self._redis.close()
