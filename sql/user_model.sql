create table user_model as
with consecutive_revisions as (
    select
		r.revision_id,
		r.username,
        r.user_type,
		r.timestamp,
        v.entity_id,
        v.property_id,
        v.action,
        v.change_target,
        v.is_reverted,
        v.reversion,
        lag(r.timestamp) over (
            partition by r.username
            order by r.timestamp asc
        ) as previous_timestamp
    from revision r
    join value_change v on r.revision_id = v.revision_id
    where 
		r.user_type in ('bot', 'human') and change_target = ''
)
select 
	username,
	user_type,
	
	MIN(timestamp) as first_edit,
	MAX(timestamp) as last_edit,
	
	COUNT(DISTINCT entity_id) as num_entities,
	COUNT(DISTINCT revision_id) as num_revisions,
	COUNT(DISTINCT property_id) as num_properties,
	
	COUNT(*) FILTER (WHERE action = 'CREATE') as num_creates,
	COUNT(*) FILTER (WHERE action = 'DELETE') as num_deletes,
	COUNT(*) FILTER (WHERE action = 'UPDATE') as num_updates,
	COUNT(*) as num_value_changes,
	
	COUNT(*) FILTER (WHERE is_reverted = 1) as num_reverted_edits,
	COUNT(*) FILTER (WHERE is_reverted = 0 and reversion = 0) as num_non_reverted_edits,
	
	avg(extract(epoch from (timestamp - previous_timestamp))) / 86400.0  as avg_days_between_revisions,

	count(*) filter (where extract(hour from timestamp) between 6 and 11)   as num_edits_morning,
    count(*) filter (where extract(hour from timestamp) between 12 and 19)  as num_edits_afternoon,
    count(*) filter (where extract(hour from timestamp) >= 20
                        or extract(hour from timestamp) < 6)                as num_edits_night,

    count(*) filter (where extract(isodow from timestamp) between 1 and 5)  as num_edits_weekday,
    count(*) filter (where extract(isodow from timestamp) in (6, 7))        as num_edits_weekend,

    count(distinct entity_id)::float / nullif(extract(days from max(timestamp) - min(timestamp)), 0) as avg_entities_per_day,

    count(distinct property_id)::float / nullif(extract(days from max(timestamp) - min(timestamp)), 0) as avg_properties_per_day
	 
from consecutive_revisions 
group by username, user_type;

-- TOP 10 most edited PROPERTIES PER USER
create table user_property as 
select user_id, property_id, count(*) as count_changes, 0 as avg_changes_to_property
from revision r join value_change v on v.revision_id = r.revision_id
where v.change_target = '' and r.user_type != 'anonymous' and v.is_reverted = 0
group by user_id, property_id;

update user_property up
set avg_changes_to_property = up.count_changes::float / nullif(um.num_value_changes, 0)
from user_model um
where um.user_id = up.user_id; 

alter table user_model add column property_id_expertise_list text default '';
alter table user_model add column property_label_expertise_list text default '';

with ranked_properties as (
    select 
        up.user_id,
        up.property_id,
        pt.property_label,
        up.avg_changes_to_property,
        row_number() over (
            partition by up.user_id 
            order by up.avg_changes_to_property desc
        ) as rn
    from user_property up
    join property_type pt on pt.property_id = up.property_id
),
top10_per_user as (
    select 
        user_id,
        array_agg(property_id order by avg_changes_to_property desc) as property_id_expertise_list,
        array_agg(property_label order by avg_changes_to_property desc) as property_label_expertise_list
    from ranked_properties
    where rn <= 10
    group by user_id
)
update user_model um
set 
    property_id_expertise_list = t.property_id_expertise_list,
    property_label_expertise_list = t.property_label_expertise_list
from top10_per_user t
where t.user_id = um.user_id;

-- TOP 3 ENTITIES PER USER
alter table user_model add column top_3_entity_id text default '';

WITH num_revisions_per_entity_user AS (
    SELECT user_id, entity_id, count(*) AS num_revisions_entity
    FROM revision
    WHERE user_type != 'anonymous'
    GROUP BY user_id, entity_id
),
top_3_most_edited_entities AS (
    SELECT
        user_id,
        entity_id,
        num_revisions_entity,
        ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY num_revisions_entity DESC) AS row_num
    FROM num_revisions_per_entity_user
),
aggregated AS (
    SELECT user_id, array_agg(entity_id ORDER BY num_revisions_entity DESC) AS top_3
    FROM top_3_most_edited_entities
    WHERE row_num <= 3
    GROUP BY user_id
)
UPDATE user_model um
SET top_3_entity_id = a.top_3
FROM aggregated a
WHERE um.user_id = a.user_id;