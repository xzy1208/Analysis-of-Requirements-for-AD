# 待评审模型：M3-L0

## 元素（共 6）
- **F1** (function): 及时处理相关数据以提供合适输出
    pre: 输入应在适当时刻有效
    post[true]: ego_state.speed == 0 and object_table.lead_velocity == 0
- **F2** (function): Predict relevant object trajectories over at least 3 s and derive the minimum TTC; the only TTC-comp
    pre: ego_state.speed == 0; object_table.lead_velocity == 0
    post[true]: predicted_trajectories.horizon == 3.0 and min_ttc == 0
- **F3** (function): Decide the target manoeuvre and driver warning each planning cycle, respecting traffic rules and dri
    pre: traffic_rules.speed_limit == 0; driver_intent.requested_speed == 0; route.path_length > 0
    post[true]: manoeuvre.target_speed == 0 and manoeuvre.required_decel == 0
- **F5** (function): Convert the manoeuvre into a kinematically feasible trajectory that never exceeds the speed limit.
    pre: traffic_rules.speed_limit == 0; manoeuvre.target_speed == 0; route.path_length > 0
    post[true]: trajectory.max_speed <= traffic_rules.speed_limit and trajectory.max_accel <= 3.0 and trajectory.required_decel == manoeuvre.required_decel
- **F6** (function): Convert the trajectory into an actuation command inside the actuator envelope.
    pre: trajectory.max_accel <= 3.0; ego_state.speed == 0
    post[true]: actuator_cmd.longitudinal_accel <= 3.0 and actuator_cmd.steering <= 1.0 and actuator_cmd.steering == -1.0
- **F7** (function): Monitor and arbitrate F6's command into E8 so the safety envelope and traffic rules are satisfied.
    pre: traffic_rules.speed_limit == 0; ego_state.speed == 0; actuator_cmd.steering <= 1.0
    post[true]: checked_cmd.longitudinal_accel <= 3.0 and checked_cmd.brake == 0
    post[actuator_cmd.steering <= 1.0 and actuator_cmd.steering == -1.0]: checked_cmd.steering = actuator_cmd.steering

## 数据流（共 26）
- raw_sensor_data: E1 -> F1
- gnss_imu: E2 -> F1
- hd_map_segment: D1 -> F1
- ego_state: F1 -> F2
- object_table: F1 -> F2
- ego_state: F1 -> F3
- ego_state: F1 -> F5
- predicted_trajectories: F2 -> F3
- predicted_trajectories: F2 -> F5
- manoeuvre: F3 -> F5
- warning: F3 -> E7
- trajectory: F5 -> F6
- actuator_cmd: F6 -> E9
- checked_cmd: F7 -> E8
- object_table: F1 -> D2
- ego_state: F1 -> D3
- map_data: E5 -> D1
- traffic_rules: E6 -> D4
- hd_map_segment: D1 -> F2
- hd_map_segment: D1 -> F3
- hd_map_segment: D1 -> F5
- traffic_rules: D4 -> F3
- traffic_rules: D4 -> F5
- traffic_rules: D4 -> F7
- ego_state: D3 -> F6
- ego_state: D3 -> F7

## 追溯条目（共 21）
- R-SCOPE-1 -> ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7']
- R-SCOPE-2 -> ['E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9']
- R-SCOPE-3 -> ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7']
- R-SCOPE-4 -> ['F3', 'F3.1', 'F3.2', 'F3.3']
- R-E-1 -> ['E7', 'E8', 'F3', 'F7']
- R-E-2 -> ['E9', 'E8', 'F6', 'F7']
- R-D-1 -> ['D1', 'D2', 'D3', 'D4', 'F1', 'F5']
- R-D-2 -> ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7']
- R-L0-1 -> ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'D1', 'D2', 'D3', 'D4', 'E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9']
- R-L1-1 -> ['F3.1', 'F3.2', 'F3.3']
- R-G-1 -> ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7']
- R-G-2 -> ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7']
- R-G-3 -> ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7']
- R-G-4 -> ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7']
- R-G-5 -> ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7']
- R-G-6 -> ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7']
- F1 -> ['F1']
- F2 -> ['F2']
- F3 -> ['F3']
- F4 -> ['F4']
- F5 -> ['F5']