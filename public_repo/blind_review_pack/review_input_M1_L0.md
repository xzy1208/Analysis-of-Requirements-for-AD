# 待评审模型：M1-L0

## 元素（共 6）
- **Perception_Localization** (function): 及时处理相关数据以提供合适输出
    pre: 输入应在适当时刻有效
    post[true]: objects.lead_speed==0 and ego_pose.yaw_rate>-3.5 and ego_pose.yaw_rate<3.5
- **Prediction** (function): Predict each relevant object's future motion over at least 3 s and derive the minimum TTC; the only 
    pre: objects.lead_speed==0 and ego_pose.speed==0 and map_data.speed_limit==0
    post[true]: predicted_trajectories.count==0 and predicted_trajectories.min_ttc==0
- **Behavior_Planning** (function): Decide the target manoeuvre (cruise, keep lane, lane change, deceleration, emergency braking), targe
    pre: ego_state.speed==0 and driver_intent.cruise_speed==0 and route.path_length>0 and traffic_rules.speed_limit>0
    post[true]: maneuver.target_speed==0 and maneuver.decel_req==0
    post[predicted_trajectories.min_ttc<1.5]: maneuver.maneuver_type=3 and maneuver.decel_req==2.0 and warning.warn_active=1
- **Motion_Planning** (function): Convert the manoeuvre into a kinematically feasible trajectory with maximum speed, acceleration and 
    pre: maneuver.target_speed==0 and ego_state.speed==0 and map_data.speed_limit==0
    post[true]: trajectory.horizon>0 and trajectory.max_speed==0 and trajectory.max_accel<=3.0
    post[traffic_rules.speed_limit>0]: trajectory.max_speed<=traffic_rules.speed_limit
- **Control** (function): Convert the trajectory into actuator commands (longitudinal acceleration, brake, steering) inside th
    pre: trajectory.horizon>0 and ego_state.speed==0
    post[true]: actuator_cmd.accel_cmd<=3.0 and actuator_cmd.brake_cmd==0 and actuator_cmd.steer_cmd>-1.0 and actuator_cmd.steer_cmd<1.0
- **Route_Planning** (function): Compute the route to the destination: path length and ETA, plus lane geometry needed by F3 and F5.
    pre: ego_pose.speed==0 and map_data.speed_limit==0 and destination.lon==0
    post[true]: route.path_length>0 and route.eta==0

## 数据流（共 33）
- map_data: HD_Map_DB -> Perception_Localization
- raw_sensor_data: raw_sensor_data -> Perception_Localization
- gnss_imu: gnss_imu -> Perception_Localization
- map_data: HD_Map_DB -> Prediction
- objects: Object_Track_DB -> Prediction
- ego_pose: ego_pose -> Prediction
- map_data: HD_Map_DB -> Behavior_Planning
- ego_state: Ego_State_DB -> Behavior_Planning
- traffic_rules: Traffic_Rules_DB -> Behavior_Planning
- predicted_trajectories: predicted_trajectories -> Behavior_Planning
- route: route -> Behavior_Planning
- driver_intent: driver_intent -> Behavior_Planning
- map_data: HD_Map_DB -> Motion_Planning
- ego_state: Ego_State_DB -> Motion_Planning
- traffic_rules: Traffic_Rules_DB -> Motion_Planning
- predicted_trajectories: predicted_trajectories -> Motion_Planning
- maneuver: maneuver -> Motion_Planning
- ego_state: Ego_State_DB -> Control
- trajectory: trajectory -> Control
- map_data: HD_Map_DB -> Route_Planning
- ego_pose: ego_pose -> Route_Planning
- destination: destination -> Route_Planning
- objects: Perception_Localization -> Object_Track_DB
- ego_pose: Perception_Localization -> ego_pose
- ego_pose: Perception_Localization -> ego_pose
- predicted_trajectories: Prediction -> predicted_trajectories
- predicted_trajectories: Prediction -> predicted_trajectories
- maneuver: Behavior_Planning -> maneuver
- warning: Behavior_Planning -> warning
- trajectory: Motion_Planning -> trajectory
- actuator_cmd: Control -> actuator_cmd
- route: Route_Planning -> route
- route: Route_Planning -> route

## 追溯条目（共 6）
- F-Perception_Localization -> ['Perception_Localization']
- F-Prediction -> ['Prediction']
- F-Behavior_Planning -> ['Behavior_Planning']
- F-Safety_Shield -> ['Safety_Shield']
- F-Motion_Planning -> ['Motion_Planning']
- F-Control -> ['Control']