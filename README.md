# Fallback Generic Thermostat for Home Assistant

This component extends the [generic-thermostat](https://www.home-assistant.io/integrations/generic_thermostat/) by adding a fallback mode in case the temperature sensor becomes unavailable.

<!-- vim-markdown-toc GFM -->

* [Installation](#installation)
* [Usage](#usage)
* [Example](#example)

<!-- vim-markdown-toc -->

## Installation

You can install this either manually copying files or using HACS.

## Usage

Uses the exact same configuration as the [generic-thermostat](https://www.home-assistant.io/integrations/generic_thermostat/), but adds 2 new configuration variables:

| Configuration Variable | Description |
| --- | --- |
| `fallback_on_ratio` | A number between `0` and `1` that represents how much of the time the heater switch should be on. This number should be in `0.05` increments e.g. `0.15` or `0.45` |
|`fallback_force_switch` | A optional switch entity id that forces fallback mode to be enabled. This is useful when you are tweaking `fallback_on_ratio`. |

> [!NOTE]
> This component will automatically set `keep_alive` to `3` minutes. You can change that value if you want, but you should keep it low.

## Example

```yaml
input_boolean:
  force_fallback_mode:
    name: Force fallback mode

climate:
  - platform: generic_thermostat
    name: Study
    heater: switch.study_heater
    target_sensor: sensor.study_temperature
    fallback_on_ratio: 0.3 # Heater will be on 30% of the time
    fallback_force_switch: input_boolean.force_fallback_mode
```
