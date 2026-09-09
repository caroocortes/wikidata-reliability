-- This features answer how is a property updated (it doesn't differentiate between different values)
-- For properties like population, you would see a lot of creates, with no updates. To measure time between "updates"
-- I need to look at the level of (entity, property)

drop table if exists entity_prop_overall_activity;
create table entity_prop_overall_activity as
with changes as (
    select
        v.entity_id,
        v.property_id,
        v.value_id,
        v.timestamp,
        v.action,
        -- v.user_type,
        lag(v.timestamp) over (
            partition by v.entity_id, v.property_id
            order by v.timestamp
        ) as prev_timestamp,
        min(v.timestamp) over (
            partition by v.entity_id, v.property_id
        ) as first_insert
    from small_table v
    where is_overall_activity
)
select
    entity_id,
    property_id,
    count(*) as num_changes,
    count(distinct value_id) as num_distinct_values,                                         

    avg(extract(epoch from (timestamp - prev_timestamp))) as avg_time_between_changes_sec,
    min(extract(epoch from (timestamp - prev_timestamp))) as min_time_between_changes_sec,
    max(extract(epoch from (timestamp - prev_timestamp))) as max_time_between_changes_sec,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY extract(epoch from (timestamp - prev_timestamp))) as median_time_between_updates_sec,

    count(*) filter (where prev_timestamp is not null
                     and extract(epoch from (timestamp - prev_timestamp)) < 3600) as num_close_in_time_changes,
    avg(extract(epoch from (timestamp - prev_timestamp)))
        filter (where extract(epoch from (timestamp - prev_timestamp)) >= 3600) as avg_time_between_changes_not_close_in_time_sec,
    min(extract(epoch from (timestamp - prev_timestamp)))
        filter (where extract(epoch from (timestamp - prev_timestamp)) >= 3600) as min_time_between_changes_not_close_in_time_sec,
    max(extract(epoch from (timestamp - prev_timestamp)))
        filter (where extract(epoch from (timestamp - prev_timestamp)) >= 3600) as max_time_between_changes_not_close_in_time_sec,

    count(distinct value_id) filter (where action = 'CREATE') as num_value_creates,
    count(*) filter (where action = 'UPDATE') as num_real_updates,
    count(distinct value_id) filter (where action = 'UPDATE') as num_value_id_real_updated,

    avg(extract(epoch from (timestamp - first_insert)))
            filter (where prev_timestamp is not null) as avg_age_of_value_to_first_insert_sec

from changes
group by entity_id, property_id;