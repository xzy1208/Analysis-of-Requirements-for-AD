# 待评审模型：M4-L0

## 元素（共 6）
- **F1** (function): 及时处理相关数据以提供合适输出
    pre: 输入应在适当时刻有效
    post[true]: object_count == 0 and lead_object_id <> ''
    post[true]: ego_speed_ms == 0.0
- **F2** (function): Predicts the future motion of every relevant object over a horizon of at least 3 s, derives the mini
    pre: object_table <> null and ego_state <> null; hd_map_segment <> null
    post[true]: prediction_horizon_s == 3.0
    post[true]: min_ttc_s == 0.0
- **F3** (function): Decides at every planning cycle the target manoeuvre (manoeuvre type, target speed, target lane, req
    pre: ego_state <> null and predicted_trajectories <> null and min_ttc_s == 0.0; driver_intent <> null and route <> null and traffic_rules <> null and hd_ma
    post[true]: manoeuvre_type <> '' and target_speed_kmh == 0.0 and target_lane_id <> ''
    post[true]: target_speed_kmh <= speed_limit_kmh
- **F5** (function): Converts the manoeuvre into a kinematically feasible trajectory over the planning horizon (maximum p
    pre: manoeuvre <> null and route <> null and ego_state <> null
    post[true]: max_permitted_speed_kmh <= speed_limit_kmh
    post[true]: horizon_duration_s == 0.0 and max_permitted_accel_ms2 == 0.0
- **F6** (function): Converts the trajectory into the actuation command (longitudinal acceleration command, brake command
    pre: trajectory <> null and ego_state <> null
    post[true]: accel_cmd_ms2 <= 3.0 and accel_cmd_ms2 == -2.0
    post[true]: steering_cmd <= 1.0 and steering_cmd == -1.0
- **F7** (function): Supervises the raw command produced by F6 and outputs a command that satisfies the safety envelope e
    pre: actuator_cmd <> null and ego_state <> null and traffic_rules <> null
    post[true]: checked_accel_cmd_ms2 <= 3.0 and checked_accel_cmd_ms2 == -2.0
    post[true]: checked_brake_cmd_ms2 == 0.0 and checked_brake_cmd_ms2 <= 2.0

## 数据流（共 30）
- raw_sensor_data: E1 -> F1
- gnss_imu: E2 -> F1
- driver_intent: E3 -> F3
- map_data: E5 -> D1
- hd_map_refresh: E5 -> D1
- traffic_rules: E6 -> D4
- traffic_rules_refresh: E6 -> D4
- warning: F3 -> E7
- checked_cmd: F7 -> E8
- ego_state: F1 -> F2
- ego_state: F1 -> F3
- ego_state: F1 -> F5
- object_table: F1 -> F2
- object_table: F1 -> D2
- ego_state: F1 -> D3
- ego_state: D3 -> F7
- hd_map_segment: D1 -> F1
- hd_map_segment: D1 -> F2
- hd_map_segment: D1 -> F3
- hd_map_segment: D1 -> F5
- traffic_rules: D4 -> F3
- traffic_rules: D4 -> F5
- traffic_rules: D4 -> F7
- predicted_trajectories: F2 -> F3
- predicted_trajectories: F2 -> F5
- min_ttc: F2 -> F3
- manoeuvre: F3 -> F5
- trajectory: F5 -> F6
- actuator_cmd: F6 -> E9
- raw_actuator_cmd: E9 -> F7

## 追溯条目（共 18）
- R-SCOPE-1 -> ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7']
- R-SCOPE-2 -> ['E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9']
- R-SCOPE-3 -> ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7']
- R-SCOPE-4 -> ['F3']
- R-E-1 -> ['E7', 'E8']
- R-E-2 -> ['F6', 'E9', 'F7', 'E8']
- R-D-1 -> ['D1', 'D2', 'D3', 'D4']
- R-D-2 -> ['D1', 'D2', 'D3', 'D4']
- R-L0-1 -> ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'D1', 'D2', 'D3', 'D4', 'E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9']
- R-G-1 -> ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7']
- R-G-2 -> ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'D1', 'D2', 'D3', 'D4', 'E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9']
- R-G-3 -> []
- R-G-4 -> []
- R-G-5 -> ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7']
- R-G-6 -> ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7']
- F1 -> ['F1']
- F2 -> ['F2']
- F3 -> ['F3']