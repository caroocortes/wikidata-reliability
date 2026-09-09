-- This features answer how is a property updated (it doesn't differentiate between different values)
-- For properties like population, you would see a lot of creates, with no updates. To measure time between "updates"
-- I need to look at the level of (entity, property)

-- Checks what happens to values after they are inserted
create table entity_prop_avg_activity_of_values as
with changes as (
    select
        v.entity_id,
        v.property_id,
        v.value_id,
        v.timestamp,
        v.action,
        --v.user_type,
        lag(v.timestamp) over (
            partition by v.entity_id, v.property_id, v.value_id
            order by v.timestamp
        ) as prev_timestamp,
        min(v.timestamp) over (
            partition by v.entity_id, v.property_id, v.value_id
        ) as value_first_insert
    from small_table v
    where is_overall_activity
),
per_value as (
    select
        entity_id,
        property_id,      
        value_id,
        count(*) as num_changes,                     

        count(*) filter (where prev_timestamp is not null) as num_changes_after_birth,

        avg(extract(epoch from (timestamp - prev_timestamp))) as avg_time_between_updates_sec,
        max(extract(epoch from (timestamp - prev_timestamp))) as max_time_between_updates_sec,
        min(extract(epoch from (timestamp - prev_timestamp))) as min_time_between_updates_sec,
        percentile_cont(0.5) WITHIN GROUP (ORDER BY extract(epoch from (timestamp - prev_timestamp))) as median_time_between_updates_sec,

        avg(extract(epoch from (timestamp - value_first_insert)))
            filter (where prev_timestamp is not null) as avg_age_of_value_at_update_sec,

        count(*) filter (where prev_timestamp is not null
                 and extract(epoch from (timestamp - prev_timestamp)) < 3600) as num_close_in_time_changes,
        avg(extract(epoch from (timestamp - prev_timestamp)))
            filter (where prev_timestamp is not null and extract(epoch from (timestamp - prev_timestamp)) >= 3600) as avg_time_between_changes_not_close_in_time_sec,
        min(extract(epoch from (timestamp - prev_timestamp)))
            filter (where prev_timestamp is not null and extract(epoch from (timestamp - prev_timestamp)) >= 3600) as min_time_between_changes_not_close_in_time_sec,
        max(extract(epoch from (timestamp - prev_timestamp)))
            filter (where prev_timestamp is not null and extract(epoch from (timestamp - prev_timestamp)) >= 3600) as max_time_between_changes_not_close_in_time_sec,

    from changes
    group by entity_id, property_id, value_id
)
select
    entity_id,
    property_id,

    count(*) as num_distinct_values,
    sum(num_changes) as num_changes,

    sum(num_changes_after_birth) as num_changes_after_birth,
    avg(num_changes) as avg_num_changes_per_value,
    sum((num_changes_after_birth > 0)::int)::float / count(*) as pct_values_ever_changed,

    -- re routing
    avg(avg_time_between_updates_sec) as avg_time_between_updates_sec,
    min(min_time_between_updates_sec) as min_time_between_updates_sec,
    max(max_time_between_updates_sec) as max_time_between_updates_sec,
    avg(median_time_between_updates_sec) as avg_median_time_between_updates_sec,
    -- ---

    -- re routing
    sum(num_close_in_time_changes) as num_close_in_time_changes,
    avg(avg_time_between_changes_not_close_in_time_sec) as avg_time_between_changes_not_close_in_time_sec,
    min(min_time_between_changes_not_close_in_time_sec) as min_time_between_changes_not_close_in_time_sec,
    max(max_time_between_changes_not_close_in_time_sec) as max_time_between_changes_not_close_in_time_sec,
    -- ---

    avg(avg_age_of_value_at_update_sec) as avg_age_of_value_at_update_sec,
    sum(num_close_in_time_changes)::float / nullif(sum(num_changes_after_birth), 0) as pct_changes_close_in_time

from per_value
group by entity_id, property_id;