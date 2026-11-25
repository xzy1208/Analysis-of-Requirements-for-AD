# 待评审模型：M5-L1

## 元素（共 34）
- **Normal** (state): No risk: cruise/keep-lane manoeuvre, no warning (F3.2/F3.3).
- **Caution** (state): Caution band: forward collision warning plus non-zero deceleration (F3.2/F3.3).
- **EmergencyBrake** (state): Critical: emergency deceleration at least 2.0 m/s2 with target speed 0 (F3.3/A-1).
- **Standstill** (state): Substate of EmergencyBrake: target speed 0 reached and brake held.
- **DriverOverride** (state): Driver acceleration request takes precedence for no-risk and caution levels, never for critical (F3.
- **FaultDegraded** (state): Synthetic degraded state entered when sensor validity flags are false; last outputs are retained.
- **Deactivated** (state): Synthetic exit state entered when ODD status becomes inactive; AEB off.
- **T1** (transition): 及时处理相关数据以提供合适输出
    pre: 输入应在适当时刻有效
    post: warning = caution and maneuver = deceleration and maneuver.deceleration > 0
- **T2** (transition): 
    pre: warning = caution and obj_count > 0
    post: warning = none and maneuver = cruise
- **T3** (transition): 
    pre: warning = caution and sensor_validity = true and odd_active = true
    post: warning = imminent_collision and maneuver = emergency_deceleration and maneuver.deceleration == 2.0 and maneuver.target_speed = 0 and checked_cmd.dece
- **T4** (transition): 
    pre: warning = imminent_collision and maneuver.deceleration == 2.0
    post: warning = caution and maneuver = deceleration and maneuver.deceleration > 0
- **T5** (transition): 
    pre: warning = imminent_collision and obj_count > 0
    post: warning = none and maneuver = cruise
- **T6** (transition): 
    pre: warning = caution and obj_count = 0
    post: warning = none and maneuver = cruise
- **T7** (transition): 
    pre: warning = imminent_collision and obj_count = 0
    post: warning = none and maneuver = cruise
- **T8** (transition): 
    pre: driver_accel_request = true and obj_count = 0
    post: warning = none and maneuver = cruise
- **T9** (transition): 
    pre: risk_level = no_risk and odd_active = true
    post: maneuver = driver_accelerate and warning = none
- **T10** (transition): 
    pre: risk_level = caution and warning = caution
    post: maneuver = driver_accelerate and warning = caution
- **T11** (transition): 
    pre: driver_accel_request = true and risk_level = no_risk
    post: maneuver = cruise and warning = none
- **T12** (transition): 
    pre: driver_accel_request = true and risk_level = caution
    post: maneuver = deceleration and warning = caution and maneuver.deceleration > 0
- **T13** (transition): 
    pre: driver_accel_request = true and min_ttc <= 1.5
    post: warning = imminent_collision and maneuver = emergency_deceleration and maneuver.deceleration == 2.0 and maneuver.target_speed = 0 and checked_cmd.dece
- **T14** (transition): 
    pre: risk_level = no_risk
    post: warning = none and maneuver = cruise
- **T15** (transition): 
    pre: warning = caution
    post: warning = caution and maneuver = deceleration
- **T16** (transition): 
    pre: warning = imminent_collision and maneuver.deceleration == 2.0
    post: warning = imminent_collision and maneuver = emergency_deceleration
- **T17** (transition): 
    pre: driver_accel_request = true
    post: warning = none and maneuver = driver_accelerate
- **T18** (transition): 
    pre: sensor_validity = false and odd_active = true
    post: warning = none and maneuver = cruise
- **T19** (transition): 
    pre: sensor_validity = false and odd_active = true
    post: warning = caution and maneuver = deceleration and maneuver.deceleration > 0
- **T20** (transition): 
    pre: sensor_validity = false and odd_active = true
    post: warning = imminent_collision and maneuver = emergency_deceleration and maneuver.deceleration == 2.0 and maneuver.target_speed = 0
- **T21** (transition): 
    pre: risk_level = no_risk
    post: warning = none and maneuver = cruise
- **T22** (transition): 
    pre: warning = caution
    post: warning = none and maneuver = cruise
- **T23** (transition): 
    pre: warning = imminent_collision
    post: warning = none and maneuver = cruise
- **T24** (transition): 
    pre: driver_accel_request = true
    post: warning = none and maneuver = cruise
- **T25** (transition): 
    pre: sensor_validity = false
    post: warning = none and maneuver = cruise
- **T26** (transition): 
    pre: odd_active = false
    post: warning = none and maneuver = cruise
- **T27** (transition): 
    pre: maneuver.deceleration == 2.0
    post: checked_cmd.target_speed = 0 and checked_cmd.brake = active

## 数据流（共 32）
- sensor_validity_E1: E1 -> FaultDegraded
- sensor_validity_E2: E2 -> FaultDegraded
- driver_accel_request: E3 -> DriverOverride
- odd_active: E3 -> Deactivated
- warning_caution: Caution -> E7
- warning_imminent: EmergencyBrake -> E7
- checked_cmd_brake: EmergencyBrake -> E8
- T1_guard: Normal -> Caution
- T2_guard: Caution -> Normal
- T3_guard: Caution -> EmergencyBrake
- T4_guard: EmergencyBrake -> Caution
- T5_guard: EmergencyBrake -> Normal
- T6_guard: Caution -> Normal
- T7_guard: EmergencyBrake -> Normal
- T8_guard: DriverOverride -> Normal
- T9_guard: Normal -> DriverOverride
- T11_guard: DriverOverride -> Normal
- T12_guard: DriverOverride -> Caution
- T13_guard: DriverOverride -> EmergencyBrake
- T14_guard: Normal -> FaultDegraded
- T15_guard: Caution -> FaultDegraded
- T16_guard: EmergencyBrake -> FaultDegraded
- T17_guard: DriverOverride -> FaultDegraded
- T18_guard: FaultDegraded -> Normal
- T19_guard: FaultDegraded -> Caution
- T20_guard: FaultDegraded -> EmergencyBrake
- T21_guard: Normal -> Deactivated
- T22_guard: Caution -> Deactivated
- T23_guard: EmergencyBrake -> Deactivated
- T24_guard: DriverOverride -> Deactivated
- T25_guard: FaultDegraded -> Deactivated
- T26_guard: Deactivated -> Normal

## 追溯条目（共 10）
- R-SCOPE-1 -> ['DriverOverride']
- R-SCOPE-2 -> ['E1', 'E2', 'E3', 'E7', 'E8', 'E9']
- R-SCOPE-4 -> ['Normal', 'Caution', 'EmergencyBrake', 'DriverOverride']
- R-E-1 -> ['Caution', 'EmergencyBrake', 'T3', 'T13', 'T20', 'T27']
- R-E-2 -> ['T3', 'T13', 'T20', 'T27', 'E9']
- R-L1-1 -> ['Normal', 'Caution', 'EmergencyBrake', 'DriverOverride']
- F3.1 -> ['T6', 'T7', 'T8']
- F3.2 -> ['Normal', 'Caution', 'EmergencyBrake', 'T1', 'T2', 'T3', 'T4', 'T5']
- F3.3 -> ['DriverOverride', 'T9', 'T10', 'T11', 'T12', 'T13', 'T27']
- N-2 -> ['T3', 'T10', 'T13', 'T20']