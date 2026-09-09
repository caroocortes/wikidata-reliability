create table entity_prop_distinct_val_change as
select 
	v.entity_id,
	v.property_id,
	-- this is for single valued (e.g., date of birth) vs multi valued properties (e.g., instance of, subclass of)
	count(distinct value_id) as num_distinct_values, -- don't filter for creates because if they exist they where created at least once
	count(*) FILTER(WHERE v.action = 'CREATE') as num_creates,
	count(*) FILTER(WHERE v.action = 'UPDATE') as num_updates,
	count(*) as total_creates_updates,
	-- This 2 are for time_span / num_changes (total_creates_updates)
	MIN(v.timestamp) as first_prop_value_insert,
	MAX(v.timestamp) as last_prop_value_insert_update,
    count(*) FILTER(WHERE r.user_type = 'bot') as num_bot_changes,
    count(*) FILTER(WHERE r.user_type = 'human') as num_human_changes
	-- Then I can aggregate for num_entities_that_suffer_updates_for_the_property
from value_change_to_keep v join revision_to_keep r on v.revision_id = r.revision_id
where v.action != 'DELETE' and v.change_target = ''
group by v.entity_id, v.property_id;