# Fallback Generic Thermostat for Home Assistant

The [generic-thermostat](https://www.home-assistant.io/integrations/generic_thermostat/) for Home Assistant has a big problem. If for some reason the temperature sensor becomes unavailable, the controller just keeps the state its in. So it can heat forever, or not heat at all. This is problematic when running Home Assistant in remote locations where physical intervention is not an option.

This component extends the [generic-thermostat](https://www.home-assistant.io/integrations/generic_thermostat/) by adding a fallback mode in case the temperature sensor becomes unavailable. In that mode, the climate controller regulates heat by turning on the heater on for some `%` of time.

<!-- vim-markdown-toc GFM -->

* [Installation](#installation)
* [Usage](#usage)
* [Example](#example)
    * [Basic](#basic)
    * [Full](#full)

<!-- vim-markdown-toc -->

## Installation

You can install this either manually copying files or using HACS.

## Usage

Uses the exact same configuration as the [generic-thermostat](https://www.home-assistant.io/integrations/generic_thermostat/#configuration-variables), but adds 3 new configuration variables:

| Configuration Variable | Description |
| --- | --- |
| `fallback_on_ratio` | A number between `0` and `1` that represents how much of the time the heater switch should be on. This number should be in `0.05` increments e.g. `0.15` or `0.45` |
| `fallback_interval` | The duration that the `fallback_on_ratio` relates to. This value defaults to `60` minutes.
|`fallback_force_switch` | A optional switch entity id that forces fallback mode to be enabled. This is useful when you are tweaking `fallback_on_ratio`. |

> [!NOTE]
> If `fallback_interval` is `60` minutes and `fallback_on_ratio` is `0.2`, the radiator will be on for `12` minutes and off for `48` minutes per hour when the temperature sensor becomes unavailable.

## Example

### Basic

```yaml
climate:
  - platform: fallback_generic_thermostat
    name: Study
    heater: switch.study_heater
    target_sensor: sensor.study_temperature
    fallback_on_ratio: 0.2 # Heater will be on 20% of the time (12 minutes per hour)
```

### Full

```yaml
input_boolean:
  force_fallback_mode:
    name: Force fallback mode

climate:
  - platform: fallback_generic_thermostat
    name: Study
    heater: switch.study_heater
    target_sensor: sensor.study_temperature
    fallback_on_ratio: 0.5 # Heater will be on 50% of the time (15 minutes per half an hour)
    fallback_interval: 00:30:00
    fallback_force_switch: input_boolean.force_fallback_mode
```
