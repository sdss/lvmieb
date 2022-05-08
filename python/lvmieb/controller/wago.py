#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from drift import Drift, Relay


__all__ = ["IEBWAGO"]


class IEBWAGO(Drift):
    """Class controlling the WAGO PLC in each electronics box.

    Parameters
    ----------
    host
        The host of the WAGO Ethernet module.
    port
        The port serving the TCP modbus service.
    name
        The name associated with this WAGO controller.

    """

    def __init__(self, host: str, port: int = 502, name: str = ""):

        super().__init__(host, port)

        self.name = name

    async def read_sensors(
        self,
        units: bool = False,
    ) -> dict[str, float | tuple[float, str]]:
        """Read temperature and humidity sensors."""

        sensors = await self.read_category("temperature")
        rhs = await self.read_category("humidity")

        sensors.update(rhs)

        if units:
            return sensors

        sensors_no_unit = {}
        for k, v in sensors.items():
            sensors_no_unit[k] = v[0]

        return sensors_no_unit

    async def read_relays(self) -> dict[str, bool]:
        """Reads the status of the power relays.

        Returns
        -------
        power
            A dictionary with the status of the power relays. `True` means the
            relay is closed, `False` open.

        """

        return await self.read_category("relays", adapt=False)

    async def set_relay(self, relay: str, closed: bool = True):
        """Sets the status of a power relay."""

        try:
            device = self.get_device(relay)
        except ValueError:
            raise NameError(f"Cannot find relay {relay!r}.")

        assert isinstance(device, Relay)

        status = await device.read(adapt=False)
        if status == closed:
            return None

        if closed:
            await device.close()
        else:
            await device.open()

        return True
