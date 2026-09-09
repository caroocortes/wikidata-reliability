create index idx_entity_prop_overall_activity_entity_property on entity_prop_overall_activity(entity_id, property_id);
analyze entity_prop_overall_activity;

create index idx_entity_prop_avg_activity_of_values_entity_property on entity_prop_avg_activity_of_values(entity_id, property_id);
analyze entity_prop_avg_activity_of_values;

create table entity_property_stats as
select 
	-- columns from entity_prop_distinct_val_change
	-- This table has information of all (entity, property) pairs that
	-- the other 2 may miss because they capture information about time between changes
	-- That's why the epdvc table is the anchor (left join) for the joins
	epdvc.property_id,
	p.property_label,
	epdvc.entity_id,
	
    epaav.num_distinct_values as epaav_num_distinct_values,
    epaav.num_changes as epaav_num_changes,
    epaav.num_changes_after_birth as epaav_num_changes_after_birth,
    epaav.avg_num_changes_per_value as epaav_avg_num_changes_per_value,
    epaav.pct_values_ever_changed as epaav_pct_values_ever_changed,
    epaav.avg_time_between_updates_sec as epaav_avg_time_between_updates_sec,
    epaav.avg_median_time_between_updates_sec as epaav_avg_median_time_between_updates_sec,
    epaav.min_time_between_updates_sec as epaav_min_time_between_updates_sec,
    epaav.max_time_between_updates_sec as epaav_max_time_between_updates_sec,
    epaav.num_close_in_time_changes as epaav_num_close_in_time_changes,
    epaav.avg_time_between_changes_not_close_in_time_sec as epaav_avg_time_between_changes_not_close_in_time_sec,
    epaav.min_time_between_changes_not_close_in_time_sec as epaav_min_time_between_changes_not_close_in_time_sec,
    epaav.max_time_between_changes_not_close_in_time_sec as epaav_max_time_between_changes_not_close_in_time_sec,
    epaav.avg_age_of_value_at_update_sec as epaav_avg_age_of_value_at_update_sec,
    epaav.pct_changes_close_in_time as epaav_pct_changes_close_in_time,

    epoa.num_changes as epoa_num_changes,
    epoa.num_distinct_values as epoa_num_distinct_values,
    epoa.avg_time_between_changes_sec as epoa_avg_time_between_changes_sec,
    epoa.min_time_between_changes_sec as epoa_min_time_between_changes_sec,
    epoa.max_time_between_changes_sec as epoa_max_time_between_changes_sec,
    epoa.median_time_between_updates_sec as epoa_median_time_between_updates_sec,
    epoa.num_close_in_time_changes as epoa_num_close_in_time_changes,
    epoa.avg_time_between_changes_not_close_in_time_sec as epoa_avg_time_between_changes_not_close_in_time_sec,
    epoa.min_time_between_changes_not_close_in_time_sec as epoa_min_time_between_changes_not_close_in_time_sec,
    epoa.max_time_between_changes_not_close_in_time_sec as epoa_max_time_between_changes_not_close_in_time_sec,
    epoa.num_value_creates as epoa_num_value_creates,
    epoa.num_real_updates as epoa_num_real_updates,
    epoa.num_value_id_real_updated as epoa_num_value_id_real_updated,
    epoa.avg_age_of_value_to_first_insert_sec as epoa_avg_age_of_value_to_first_insert_sec,
	
	p.property_type
from 
	properties p 
	join entity_prop_distinct_val_change epdvc on p.property_id = epdvc.property_id
	left join entity_prop_avg_activity_of_values epaav on epaav.property_id = epdvc.property_id and epdvc.entity_id = epaav.entity_id
	left join entity_prop_overall_activity epoa on epoa.property_id = epdvc.property_id and epoa.entity_id = epdvc.entity_id;