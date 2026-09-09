-- 1) get 1 representative value per (entity, property)
with rep_values as (
    select distinct on (entity_id) -- get one value per entity (the one with highest num_updates)
        entity_id,
        value_id,
        count(*) as num_updates
    from value_change
    where 
        property_id = 1113
        and action = 'UPDATE'
		and change_target = ''
        and is_reverted = 0
        and reversion = 0
		-- filter for actual value changes:
		and (change_type = 'property_value_update' or label = 'property_value_update')
    group by entity_id, value_id
    order by entity_id, num_updates desc
),
-- 2) compute lag per row, so get previous_timestamp
consecutive_updates as (
    select 
        v.entity_id,
        v.timestamp,
        lag(v.timestamp) over (
            partition by v.entity_id order by v.timestamp
        ) as previous_timestamp
    from value_change v
    join rep_values rv on rv.entity_id = v.entity_id and rv.value_id = v.value_id
    where 
        v.property_id = 1113
        and v.action = 'UPDATE'
		and change_target = ''
		and (change_type = 'property_value_update' or label = 'property_value_update')
        and v.is_reverted = 0
        and v.reversion = 0
),
-- 3) aggregate the diffs to get avg
avg_times as (
    select
        entity_id,
        avg(
            extract(epoch from (timestamp - previous_timestamp)) / 86400.0
        ) as avg_days_between_updates,
		count(*) as num_updates
    from consecutive_updates
    where previous_timestamp is not null  -- skip first row per entity
    group by entity_id
),
-- 4) Entities can have multiple types which are separated per commas
exploded_types as (
    select 
        es.entity_id,
        trim(unnest(string_to_array(es.entity_types_31, ','))) as entity_type
    from entity_stats es
    where es.entity_id in (select entity_id from avg_times)
)
-- 5) Join everything to get avg_days_between_updates for entity types
select 
    et.entity_type,
    count(distinct et.entity_id) as num_entities,
	sum(num_updates) as total_updates_all_entities,
    avg(at.avg_days_between_updates) as avg_days_between_updates,
    percentile_cont(0.5) within group (order by at.avg_days_between_updates) as median_days_between_updates
from exploded_types et
join avg_times at on at.entity_id = et.entity_id
group by et.entity_type
having num_entities > 1
order by avg_days_between_updates asc