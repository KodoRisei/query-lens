\c querylens;

DROP SCHEMA IF EXISTS game1 CASCADE;
CREATE SCHEMA game1;
SET search_path=game1;

CREATE TABLE user_m (
    user_id VARCHAR(10),
    guid VARCHAR(50),
    country_code VARCHAR(10),
    register_status INT,
    create_time TIMESTAMP,
    update_time TIMESTAMP,
    delete_flg BOOLEAN
);

CREATE TABLE login_log (
    limitation_action_id VARCHAR(10),
    user_id VARCHAR(10),
    limitation_action_type INT,
    create_time TIMESTAMP,
    create_user_id VARCHAR(10),
    create_activity_id VARCHAR(10),
    update_time TIMESTAMP,
    update_user_id VARCHAR(10),
    update_activity_id VARCHAR(10),
    delete_flg BOOLEAN
);

CREATE TABLE user_world_result_log (
    user_world_result_log_id VARCHAR(10),
    user_id VARCHAR(10),
    user_world_start_log_id VARCHAR(10),
    world_dungeon_id INT,
    clear_flg BOOLEAN,
    exp INT,
    money INT,
    money_before INT,
    money_after INT,
    friend_point_before INT,
    friend_point_after INT,
    create_time TIMESTAMP,
    create_user_id VARCHAR(10),
    create_activity_id VARCHAR(10),
    update_time TIMESTAMP,
    update_user_id VARCHAR(10),
    update_activity_id VARCHAR(10),
    delete_flg BOOLEAN
);

CREATE TABLE user_world_start_log (
    user_world_start_log_id VARCHAR(10),
    user_id VARCHAR(10),
    type INT,
    world_dungeon_id INT,
    create_time TIMESTAMP,
    create_user_id VARCHAR(10),
    create_activity_id VARCHAR(10),
    update_time TIMESTAMP,
    update_user_id VARCHAR(10),
    update_activity_id VARCHAR(10),
    delete_flg BOOLEAN
);

CREATE TABLE user_tutorial_status_t (
    user_tutorial_status_id VARCHAR(10),
    user_id VARCHAR(10),
    status_id VARCHAR(10),
    end_flg BOOLEAN,
    sub_status INT,
    create_time TIMESTAMP,
    create_user_id VARCHAR(10),
    create_activity_id VARCHAR(10),
    update_time TIMESTAMP,
    update_user_id VARCHAR(10),
    update_activity_id VARCHAR(10),
    delete_flg BOOLEAN
);

CREATE TABLE user_purchase_history_t (
    user_purchase_history_id VARCHAR(10),
    user_id VARCHAR(10),
    os_type INT,
    os_version VARCHAR(10),
    request_type INT,
    purchase_status INT,
    shop_purchase_id VARCHAR(10),
    product_id VARCHAR(25),
    tier_ver INT,
    tier INT,
    transaction_id VARCHAR(50),
    asset_num INT,
    result_asset_num INT,
    create_time TIMESTAMP,
    create_user_id VARCHAR(10),
    create_activity_id VARCHAR(10),
    update_time TIMESTAMP,
    update_user_id VARCHAR(10),
    update_activity_id VARCHAR(10),
    delete_flg BOOLEAN
);

CREATE TABLE shop_purchase_m (
    shop_purchase_id VARCHAR(10),
    shop_id VARCHAR(10),
    product_type INT,
    product_title VARCHAR(25),
    product_id VARCHAR(50),
    tier_ver INT,
    tier INT,
    priority INT,
    display_type INT,
    limit_count INT,
    os_type INT,
    product_description VARCHAR(25),
    img INT,
    price INT,
    create_time TIMESTAMP,
    create_user_id VARCHAR(10),
    update_time TIMESTAMP,
    update_user_id VARCHAR(10),
    delete_flg BOOLEAN
);

CREATE TABLE world_dungeon_m (
    world_dungeon_id INT,
    world_stage_id INT,
    priority INT,
    dungeon_name VARCHAR(10),
    level INT,
    type INT,
    prerequisite_world_dungeon_id VARCHAR(10),
    need_stamina INT,
    battle_num INT,
    attribute INT,
    link_point INT,
    entry_num_limit INT,
    entry_phase_limit INT,
    clear_round_limit INT,
    dungeon_effect1 INT,
    dungeon_effect2 INT,
    dungeon_effect3 INT,
    dungeon_effect4 INT,
    dungeon_effect5 INT,
    background VARCHAR(25),
    sky INT,
    time_zone INT,
    weather INT,
    cloud INT,
    flare INT,
    environment_sound INT,
    bgm VARCHAR(10),
    bgm_intro_flg BOOLEAN,
    boss_bgm VARCHAR(10),
    boss_bgm_intro_flg BOOLEAN,
    ex_boss_bgm VARCHAR(10),
    ex_boss_bgm_intro_flg BOOLEAN,
    ex_boss_bgm_condition INT,
    can_continue BOOLEAN,
    round_flg BOOLEAN,
    create_time TIMESTAMP,
    create_user_id VARCHAR(10),
    update_time TIMESTAMP,
    update_user_id VARCHAR(10),
    delete_flg BOOLEAN
);

CREATE TABLE world_stage_m (
    world_stage_id INT,
    world_area_id VARCHAR(10),
    priority INT,
    name VARCHAR(25),
    type INT,
    force_open_num INT,
    prerequisite_world_stage_id VARCHAR(10),
    stage_image VARCHAR(50),
    open_time TIMESTAMP,
    close_time TIMESTAMP,
    admin_open_flg BOOLEAN,
    create_time TIMESTAMP,
    create_user_id VARCHAR(10),
    update_time TIMESTAMP,
    update_user_id VARCHAR(10),
    delete_flg BOOLEAN
);

\COPY game1.user_m FROM '/docker-entrypoint-initdb.d/csv/mio01_user_m.csv' DELIMITER ',' CSV HEADER;
\COPY game1.login_log FROM '/docker-entrypoint-initdb.d/csv/mio02_login_log.csv' DELIMITER ',' CSV HEADER;
\COPY game1.user_world_result_log FROM '/docker-entrypoint-initdb.d/csv/mio03_user_world_result_log.csv' DELIMITER ',' CSV HEADER;
\COPY game1.user_world_start_log FROM '/docker-entrypoint-initdb.d/csv/mio04_user_world_start_log.csv' DELIMITER ',' CSV HEADER;
\COPY game1.user_tutorial_status_t FROM '/docker-entrypoint-initdb.d/csv/mio05_user_tutorial_status_t.csv' DELIMITER ',' CSV HEADER;
\COPY game1.user_purchase_history_t FROM '/docker-entrypoint-initdb.d/csv/mio06_user_purchase_history_t.csv' DELIMITER ',' CSV HEADER;
\COPY game1.shop_purchase_m FROM '/docker-entrypoint-initdb.d/csv/mio07_shop_purchase_m.csv' DELIMITER ',' CSV HEADER;
\COPY game1.world_dungeon_m FROM '/docker-entrypoint-initdb.d/csv/mio08_world_dungeon_m.csv' DELIMITER ',' CSV HEADER;
\COPY game1.world_stage_m FROM '/docker-entrypoint-initdb.d/csv/mio09_world_stage_m.csv' DELIMITER ',' CSV HEADER;
