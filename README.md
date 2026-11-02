# SHL Schedule Maker

## Run Instructions

Requirements should only be numpy and pandas (any new-ish version).

### SHL:
```python schedule_maker_fullymanual.py --league=shl --season=91 --debug_log=True```

Replace 91 with the current upcoming season number

### SMJHL:
```python schedule_maker_fullymanual.py --league=smjhl --season=91 --debug_log=True```

Replace 91 with the current upcoming season number

### Outputs

The outputs will in a folder in the same working directory named "fullymanual_schedules", under files shl_s91_sched.csv or smjhl_s91_sched.csv