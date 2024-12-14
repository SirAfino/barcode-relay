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

from datetime import datetime
import json
from redis import Redis
from .hearthbeat import Hearthbeat

class RedisPubSubHearthbeat(Hearthbeat):
    """Redis PubSub hearthbeat"""
    _redis: Redis
    _channel_name: str

    def __init__(
        self,
        relay_name: str,
        redis_host: str,
        redis_port: int,
        redis_username: str,
        redis_password: str,
        redis_channel: str,
        hb_interval_ms: int = 10000,
        polling_ms: int = 1000
    ):
        super().__init__(relay_name, hb_interval_ms, polling_ms)
        self._redis = Redis(
            host=redis_host,
            port=redis_port,
            username=redis_username,
            password=redis_password,
            decode_responses=True
        )
        self._channel_name = redis_channel

    def _send(self):
        data = { 'relay': self._relay_name, 'ts': int(datetime.now().timestamp()) }

        try:
            self._redis.publish(self._channel_name, json.dumps(data))
        except Exception as e:
            print(e)
            pass

    def stop(self):
        super().stop()
        if self._redis:
            self._redis.close()
